import json
from dataclasses import dataclass
from typing import Any

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
    SORT_COLUMNS = {
        "tracking_id": "s.dhl_id",
        "status": "s.status",
        "created_at": "s.created_at",
        "updated_at": "s.updated_at",
        "user": "u.email",
        "weight": "s.weight",
    }

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

    @staticmethod
    def _shipment_select_sql() -> str:
        return """
            SELECT
                s.id_shipment,
                s.dhl_id AS tracking_id,
                s.status,
                s.weight,
                CAST(s.created_at AS CHAR) AS created_at,
                CAST(s.updated_at AS CHAR) AS updated_at,
                u.id_user,
                u.email AS user_email,
                il.id_location AS initial_id_location,
                il.country_code AS initial_country_code,
                il.city AS initial_city,
                il.latitude AS initial_latitude,
                il.longitude AS initial_longitude,
                CAST(il.created_at AS CHAR) AS initial_created_at,
                CAST(il.updated_at AS CHAR) AS initial_updated_at,
                el.id_location AS end_id_location,
                el.country_code AS end_country_code,
                el.city AS end_city,
                el.latitude AS end_latitude,
                el.longitude AS end_longitude,
                CAST(el.created_at AS CHAR) AS end_created_at,
                CAST(el.updated_at AS CHAR) AS end_updated_at,
                cl.id_location AS current_id_location,
                cl.country_code AS current_country_code,
                cl.city AS current_city,
                cl.latitude AS current_latitude,
                cl.longitude AS current_longitude,
                CAST(cl.created_at AS CHAR) AS current_created_at,
                CAST(cl.updated_at AS CHAR) AS current_updated_at
            FROM shipments s
            JOIN users u ON u.id_user = s.id_user
            LEFT JOIN locations il ON il.id_location = s.initial_location
            LEFT JOIN locations el ON el.id_location = s.end_location
            LEFT JOIN locations cl ON cl.id_location = s.current_location
        """

    @staticmethod
    def _location_from_row(row: dict[str, Any], prefix: str) -> dict | None:
        id_location = row.get(f"{prefix}_id_location")
        if id_location is None:
            return None

        return {
            "id_location": id_location,
            "country_code": row.get(f"{prefix}_country_code"),
            "city": row.get(f"{prefix}_city"),
            "latitude": float(row[f"{prefix}_latitude"]) if row.get(f"{prefix}_latitude") is not None else None,
            "longitude": float(row[f"{prefix}_longitude"]) if row.get(f"{prefix}_longitude") is not None else None,
            "created_at": row.get(f"{prefix}_created_at"),
            "updated_at": row.get(f"{prefix}_updated_at"),
        }

    @classmethod
    def _shipment_from_row(cls, row: dict[str, Any]) -> dict:
        return {
            "id_shipment": row["id_shipment"],
            "tracking_id": row["tracking_id"],
            "status": row["status"],
            "weight": float(row["weight"]) if row.get("weight") is not None else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "user": {
                "id_user": row["id_user"],
                "email": row["user_email"],
            },
            "initial_location": cls._location_from_row(row, "initial"),
            "end_location": cls._location_from_row(row, "end"),
            "current_location": cls._location_from_row(row, "current"),
        }

    @staticmethod
    def _list_filters(
        user_id: int,
        status: str | None,
        q: str | None,
        created_from: str | None,
        created_to: str | None,
        updated_from: str | None,
        updated_to: str | None,
    ) -> tuple[list[str], list[Any]]:
        filters = ["s.id_user = %s"]
        params: list[Any] = [user_id]

        if status:
            filters.append("s.status = %s")
            params.append(status)

        if q:
            filters.append("(s.dhl_id LIKE %s OR CAST(s.id_shipment AS CHAR) LIKE %s)")
            like_value = f"%{q}%"
            params.extend([like_value, like_value])

        if created_from:
            filters.append("s.created_at >= %s")
            params.append(created_from)

        if created_to:
            filters.append("s.created_at <= %s")
            params.append(created_to)

        if updated_from:
            filters.append("s.updated_at >= %s")
            params.append(updated_from)

        if updated_to:
            filters.append("s.updated_at <= %s")
            params.append(updated_to)

        return filters, params

    def list_for_user(
        self,
        user_id: int,
        status: str | None = None,
        q: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        updated_from: str | None = None,
        updated_to: str | None = None,
        sort: str = "-updated_at",
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        filters, params = self._list_filters(
            user_id,
            status,
            q,
            created_from,
            created_to,
            updated_from,
            updated_to,
        )
        where_sql = " WHERE " + " AND ".join(filters)

        descending = sort.startswith("-")
        sort_key = sort[1:] if descending else sort
        sort_column = self.SORT_COLUMNS.get(sort_key, "s.updated_at")
        direction = "DESC" if descending else "ASC"
        offset = (page - 1) * page_size

        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM shipments s JOIN users u ON u.id_user = s.id_user{where_sql}",
                params,
            )
            total = int(cursor.fetchone()["total"])

            cursor.execute(
                f"""
                    {self._shipment_select_sql()}
                    {where_sql}
                    ORDER BY {sort_column} {direction}
                    LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            rows = cursor.fetchall()

        return {
            "items": [self._shipment_from_row(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_detail_for_user(self, tracking_id: str, user_id: int) -> dict | None:
        with database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                    {self._shipment_select_sql()}
                    WHERE s.dhl_id = %s AND s.id_user = %s
                """,
                (tracking_id, user_id),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._shipment_from_row(row)
