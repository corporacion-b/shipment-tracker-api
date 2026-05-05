import json
from dataclasses import dataclass

from src.db.connection import database


@dataclass(frozen=True)
class NormalizedShipmentStatus:
    tracking_id: str
    carrier: str
    status: str
    description: str

@dataclass(frozen=True)
class NormalizedShipmentLocation:
    tracking_id: str
    location: str
    timestamp: str
    city: str

class ShipmentRepository:
    @staticmethod
    def _upsert_status_sql() -> str:
        return """
            INSERT INTO shipments (tracking_id, carrier, current_status, current_description, raw_payload, last_synced_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                carrier = VALUES(carrier),
                current_status = VALUES(current_status),
                current_description = VALUES(current_description),
                raw_payload = VALUES(raw_payload),
                last_synced_at = CURRENT_TIMESTAMP
        """

    def upsert_status(self, shipment_status: NormalizedShipmentStatus, raw_payload: dict):
        payload = json.dumps(raw_payload)
        with database.connect() as connection:
            cursor = connection.cursor()
            query = self._upsert_status_sql()
            cursor.execute(query, (
                shipment_status.tracking_id, shipment_status.carrier,
                shipment_status.status, shipment_status.description, payload
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
