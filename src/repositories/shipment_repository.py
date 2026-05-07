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

@dataclass(frozen=True)
class NormalizedShipmentHistory:
    tracking_id: str
    events: list

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

    @staticmethod
    def _upsert_history_sql() -> str:
        return """
            INSERT INTO shipments (
                tracking_id, current_status, current_description, 
                location, city, timestamp, raw_payload, last_synced_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                current_status = VALUES(current_status),
                current_description = VALUES(current_description),
                location = VALUES(location),
                city = VALUES(city),
                timestamp = VALUES(timestamp),
                raw_payload = VALUES(raw_payload),
                last_synced_at = CURRENT_TIMESTAMP
        """

    def upsert_history(self, shipment_history: NormalizedShipmentHistory, raw_payload: dict):
        payload = json.dumps(raw_payload)
        
        last_event = shipment_history.events[0] if shipment_history.events else {}
        
        status_dict = last_event.get("status") if isinstance(last_event.get("status"), dict) else {}
        
        status_str = status_dict.get("status") or last_event.get("status") or "N/A"
        description_str = status_dict.get("description") or last_event.get("description") or "Sin descripción"

        loc_data = last_event.get("location", {}).get("address", {})
        raw_locality = loc_data.get("addressLocality") or ""
        
        city = raw_locality.split(" - ")[0] if " - " in raw_locality else raw_locality
        country = raw_locality.split(" - ")[1] if " - " in raw_locality else loc_data.get("countryCode", "")

        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(self._upsert_history_sql(), (
                shipment_history.tracking_id,
                str(status_str),    
                str(description_str), 
                str(country),
                str(city),
                str(last_event.get("timestamp") or ""),
                payload
            ))