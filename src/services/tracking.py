from datetime import datetime, timezone

from anyio import to_thread
from fastapi import HTTPException, status

from src.repositories.shipment_repository import (
    NormalizedShipmentDwellTime,
    NormalizedShipmentStatus,
    NormalizedShipmentLocation,
    ShipmentRepository,
)
from src.repositories.location_repository import LocationRepository
from src.services.dhl import DHLService


class TrackingService:
    def __init__(self, repository: ShipmentRepository | None = None):
        self.repository = repository or ShipmentRepository()

    async def get_status(self, tracking_id: str, user_id: int) -> NormalizedShipmentStatus:
        data = await DHLService.buscar_en_dhl(tracking_id)
        normalized_status = self._normalize_status(tracking_id, data, user_id)
        await to_thread.run_sync(
            self.repository.upsert_status,
            normalized_status,
        )
        return normalized_status

    @staticmethod
    def _extract_status_data(data: dict) -> dict:
        try:
            shipment = data["shipments"][0]
        except (KeyError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        status_data = shipment.get("status")
        if not isinstance(status_data, dict) or not status_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        return status_data

    @classmethod
    def _normalize_status(cls, tracking_id: str, data: dict, user_id: int,) -> NormalizedShipmentStatus:
        shipment_data = data["shipments"][0]
        loc_repo = LocationRepository()

        origin_address = shipment_data.get("origin", {}).get("address", {})
        origin_city = origin_address.get("addressLocality", "Unknown")
        origin_cc = origin_address.get("countryCode", "XX")

        dest_address = shipment_data.get("destination", {}).get("address", {})
        dest_city = dest_address.get("addressLocality", "Unknown")
        dest_cc = dest_address.get("countryCode", "XX")

        id_initial = loc_repo.get_or_create_location(origin_cc, origin_city)
        id_end = loc_repo.get_or_create_location(dest_cc, dest_city)

        details = shipment_data.get("details", {})
        actual_weight = details.get("weight", {}).get("value") or 0.0

        return NormalizedShipmentStatus(
            tracking_id=tracking_id,
            status=shipment_data.get("status", {}).get("status", "UNKNOWN"),
            weight=float(actual_weight),
            id_user=user_id,
            initial_location=id_initial,
            end_location=id_end          
        )
    
    async def get_current_location(self, tracking_id: str, user_id: int) -> NormalizedShipmentLocation:
        data = await DHLService.buscar_en_dhl(tracking_id)
        loc_repo = LocationRepository()
        
        normalized_location = self._normalize_location(tracking_id, data)
       
        location_id = loc_repo.get_or_create_location(
            country_code=normalized_location.country_code,
            city=normalized_location.city
        )
        
        # 3. Actualizar la FK 'current_location' en la tabla 'shipments'
        await to_thread.run_sync(
            self.repository.update_current_location,
            tracking_id,
            location_id
        )
        
        return normalized_location

    async def get_dwell_time(self, tracking_id: str, user_id: int) -> NormalizedShipmentDwellTime:
        del user_id

        data = await DHLService.buscar_en_dhl(tracking_id)
        shipment_data = self._extract_shipment_data(data)
        status_data = self._extract_status_data(data)
        current_location = self._extract_location_from_status(status_data)

        current_status = str(status_data.get("status", "UNKNOWN")).upper()
        if current_status == "DELIVERED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El dwell time no aplica a envios entregados.",
            )

        current_timestamp_raw = status_data.get("timestamp")
        if not current_timestamp_raw:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        current_timestamp = self._parse_dhl_timestamp(current_timestamp_raw)
        dwell_start = self._resolve_dwell_start(
            shipment_data,
            current_location["country_code"],
            current_location["city"],
            current_timestamp,
        )

        now_utc = datetime.now(timezone.utc)
        elapsed_hours = max((now_utc - dwell_start).total_seconds() / 3600, 0.0)

        return NormalizedShipmentDwellTime(
            tracking_id=tracking_id,
            status=current_status,
            country_code=current_location["country_code"],
            city=current_location["city"],
            current_status_timestamp=current_timestamp_raw,
            dwell_time_hours=round(elapsed_hours, 2),
            dwell_time_days=round(elapsed_hours / 24, 2),
        )

    @staticmethod
    def _extract_shipment_data(data: dict) -> dict:
        try:
            shipment = data["shipments"][0]
        except (KeyError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        if not isinstance(shipment, dict) or not shipment:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        return shipment

    @classmethod
    def _normalize_location(
        cls,
        tracking_id: str,
        data: dict,
    ) -> NormalizedShipmentLocation:
        try:
            shipment_data = data["shipments"][0]
            status_data = shipment_data.get("status", {})
            location_dict = status_data.get("location", {})
            address_dict = location_dict.get("address", {})
            city_value = address_dict.get("addressLocality")
            country_value = address_dict.get("countryCode")

            if city_value and " - " in city_value:
                city_value = city_value.split(" - ")[0].strip()

            return NormalizedShipmentLocation(
                tracking_id=tracking_id,
                country_code=country_value or "XX",
                city=city_value or "Unknown City",
                timestamp=status_data.get("timestamp", "Fecha desconocida"),
            )
        except (KeyError, IndexError):
            # Fallback en caso de que la estructura sea distinta
            return NormalizedShipmentLocation(
                tracking_id=tracking_id,
                country_code="XX",
                city="Unknown",
                timestamp="N/A"
            )

    @staticmethod
    def _extract_location_from_status(status_data: dict) -> dict[str, str]:
        location_dict = status_data.get("location")
        address_dict = location_dict.get("address") if isinstance(location_dict, dict) else None

        if not isinstance(address_dict, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        city_value = address_dict.get("addressLocality")
        country_value = address_dict.get("countryCode")

        if city_value and " - " in city_value:
            city_value = city_value.split(" - ")[0].strip()

        if not city_value or not country_value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        return {
            "country_code": str(country_value),
            "city": str(city_value),
        }

    @staticmethod
    def _parse_dhl_timestamp(timestamp_value: str) -> datetime:
        normalized_value = str(timestamp_value).strip()
        if normalized_value.endswith("Z"):
            normalized_value = normalized_value[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(normalized_value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    @classmethod
    def _extract_timeline_events(cls, shipment_data: dict) -> list[dict]:
        for candidate_key in ("events", "checkpoints", "history"):
            candidate = shipment_data.get(candidate_key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return []

    @classmethod
    def _extract_location_from_event(cls, event: dict) -> tuple[str, str] | None:
        location_dict = event.get("location")
        address_dict = location_dict.get("address") if isinstance(location_dict, dict) else None
        if not isinstance(address_dict, dict):
            return None

        city_value = address_dict.get("addressLocality")
        country_value = address_dict.get("countryCode")

        if city_value and " - " in str(city_value):
            city_value = str(city_value).split(" - ")[0].strip()

        if not city_value or not country_value:
            return None

        return str(country_value), str(city_value)

    @classmethod
    def _resolve_dwell_start(
        cls,
        shipment_data: dict,
        current_country_code: str,
        current_city: str,
        current_timestamp: datetime,
    ) -> datetime:
        current_location = (current_country_code, current_city)
        usable_events: list[tuple[datetime, tuple[str, str]]] = []

        for event in cls._extract_timeline_events(shipment_data):
            timestamp_value = event.get("timestamp")
            event_location = cls._extract_location_from_event(event)
            if not timestamp_value or event_location is None:
                continue

            parsed_timestamp = cls._parse_dhl_timestamp(str(timestamp_value))
            usable_events.append((parsed_timestamp, event_location))

        usable_events.append((current_timestamp, current_location))
        usable_events.sort(key=lambda item: item[0])

        dwell_start = current_timestamp
        for event_timestamp, event_location in reversed(usable_events):
            if event_location != current_location:
                break
            dwell_start = event_timestamp

        return dwell_start
