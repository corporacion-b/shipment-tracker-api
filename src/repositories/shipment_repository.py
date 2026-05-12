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
