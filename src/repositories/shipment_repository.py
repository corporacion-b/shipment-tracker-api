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
    current_location: int | None

@dataclass(frozen=True)
class NormalizedShipmentLocation:
    tracking_id: str
    location: str
    timestamp: str
    city: str

class ShipmentRepository:
    @staticmethod
    def _upsert_shipment_sql() -> str:
        return """
            INSERT INTO shipments (
                dhl_id, status, weight, initial_location, 
                end_location, current_location, id_user
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                weight = VALUES(weight),
                current_location = VALUES(current_location),
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
                shipment.current_location,
                shipment.id_user
            ))

    @staticmethod
    def _upsert_location_sql() -> str:
        return """
            INSERT INTO shipments (tracking_id, location, city, timestamp, raw_payload, last_synced_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                location = VALUES(location),
                city = VALUES(city),
                timestamp = VALUES(timestamp),
                raw_payload = VALUES(raw_payload),
                last_synced_at = CURRENT_TIMESTAMP
        """

    def upsert_location(self, shipment_location: NormalizedShipmentLocation, raw_payload: dict):
        payload = json.dumps(raw_payload)
        with database.connect() as connection:
            cursor = connection.cursor()
            query = self._upsert_location_sql()
            cursor.execute(query, (
                shipment_location.tracking_id, shipment_location.location,
                shipment_location.city, shipment_location.timestamp, payload
            ))
