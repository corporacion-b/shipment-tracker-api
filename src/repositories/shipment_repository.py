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
    def upsert_status(self, shipment_status: NormalizedShipmentStatus, raw_payload: dict):
        payload = json.dumps(raw_payload)
        with database.connect() as connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO shipments (tracking_id, carrier, current_status, current_description, raw_payload, last_synced_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tracking_id) DO UPDATE SET
                    carrier = excluded.carrier,
                    current_status = excluded.current_status,
                    current_description = excluded.current_description,
                    raw_payload = excluded.raw_payload,
                    updated_at = CURRENT_TIMESTAMP,
                    last_synced_at = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (
                shipment_status.tracking_id, shipment_status.carrier,
                shipment_status.status, shipment_status.description, payload
            ))

    def upsert_location(self, shipment_location: NormalizedShipmentLocation, raw_payload: dict):
        payload = json.dumps(raw_payload)
        with database.connect() as connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO shipments (tracking_id, location, city, timestamp, raw_payload, last_synced_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tracking_id) DO UPDATE SET
                    location = excluded.location,
                    city = excluded.city,
                    timestamp = excluded.timestamp,
                    raw_payload = excluded.raw_payload,
                    updated_at = CURRENT_TIMESTAMP,
                    last_synced_at = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (
                shipment_location.tracking_id, shipment_location.location,
                shipment_location.city, shipment_location.timestamp, payload
            ))
