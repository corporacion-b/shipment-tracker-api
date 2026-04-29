import json
from dataclasses import dataclass

from src.db.connection import database


@dataclass(frozen=True)
class NormalizedShipmentStatus:
    tracking_id: str
    carrier: str
    status: str
    description: str


class ShipmentRepository:
    def upsert_status(self, shipment_status: NormalizedShipmentStatus, raw_payload: dict):
        payload = json.dumps(raw_payload)

        with database.connect() as connection:
            cursor = connection.cursor()

            if database.is_sqlite:
                cursor.execute(
                    """
                    INSERT INTO shipments (
                        tracking_id,
                        carrier,
                        current_status,
                        current_description,
                        raw_payload,
                        last_synced_at
                    )
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(tracking_id) DO UPDATE SET
                        carrier = excluded.carrier,
                        current_status = excluded.current_status,
                        current_description = excluded.current_description,
                        raw_payload = excluded.raw_payload,
                        updated_at = CURRENT_TIMESTAMP,
                        last_synced_at = CURRENT_TIMESTAMP
                    """,
                    (
                        shipment_status.tracking_id,
                        shipment_status.carrier,
                        shipment_status.status,
                        shipment_status.description,
                        payload,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO shipments (
                        tracking_id,
                        carrier,
                        current_status,
                        current_description,
                        raw_payload,
                        last_synced_at
                    )
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        carrier = VALUES(carrier),
                        current_status = VALUES(current_status),
                        current_description = VALUES(current_description),
                        raw_payload = VALUES(raw_payload),
                        updated_at = CURRENT_TIMESTAMP,
                        last_synced_at = CURRENT_TIMESTAMP
                    """,
                    (
                        shipment_status.tracking_id,
                        shipment_status.carrier,
                        shipment_status.status,
                        shipment_status.description,
                        payload,
                    ),
                )
