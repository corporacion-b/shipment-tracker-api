import json
from dataclasses import dataclass

from src.db.connection import database


@dataclass(frozen=True)
class NormalizedShipmentStatus:
    tracking_id: str
    status: str
    weight: float | None
    id_user: int
    initial_location: int
    end_location: int

@dataclass(frozen=True)
class NormalizedShipmentLocation:
    tracking_id: str
    country_code: str
    city: str
    timestamp: str


@dataclass(frozen=True)
class NormalizedShipmentDwellTime:
    tracking_id: str
    status: str
    country_code: str
    city: str
    current_status_timestamp: str
    dwell_time_hours: float
    dwell_time_days: float

@dataclass(frozen=True)
class NormalizedHistoryEvent:
    event_timestamp: str
    status: str
    description: str | None
    raw_payload: str 
    id_shipment: int
    id_location: int

class ShipmentRepository:
    @staticmethod
    def _upsert_shipment_sql() -> str:
        return """
            INSERT INTO shipments (
                dhl_id, status, weight, initial_location, 
                end_location, id_user
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                weight = VALUES(weight),
                updated_at = CURRENT_TIMESTAMP
        """

    def upsert_status(self, shipment: NormalizedShipmentStatus):
        with database.connect() as connection:
            cursor = connection.cursor()
            query = self._upsert_shipment_sql()
            cursor.execute(query, (
                shipment.tracking_id,
                shipment.status,
                shipment.weight,
                shipment.initial_location,
                shipment.end_location,
                shipment.id_user
            ))

    @staticmethod
    def _upsert_current_location_sql() -> str:
        return """
            UPDATE shipments 
            SET current_location = %s,  
                updated_at = CURRENT_TIMESTAMP
            WHERE dhl_id = %s
        """

    def update_current_location(self, tracking_id: str, location_id: int):
        with database.connect() as connection:
            cursor = connection.cursor()
            query = self._upsert_current_location_sql()
            cursor.execute(query, (location_id, tracking_id))

    def get_shipment_id_by_tracking(self, tracking_id: str) -> int | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_shipment FROM shipments WHERE dhl_id = %s", (tracking_id,))
            result = cursor.fetchone()

            if result:
                return result.get('id_shipment')
            return None

    @staticmethod
    def _upsert_history_sql() -> str:
        return """
            INSERT INTO shipment_history 
            (event_timestamp, status, description, raw_payload, id_shipment, id_location)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                raw_payload = VALUES(raw_payload),
                updated_at = CURRENT_TIMESTAMP
        """

    def upsert_history_event(self, event: NormalizedHistoryEvent):
        query = self._upsert_history_sql()
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (
                event.event_timestamp, event.status, event.description,
                event.raw_payload, event.id_shipment, event.id_location
            ))
