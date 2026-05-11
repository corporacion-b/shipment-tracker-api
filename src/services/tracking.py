from anyio import to_thread
from fastapi import HTTPException, status

from src.repositories.shipment_repository import (
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
    
    async def get_location(self, tracking_id: str) -> NormalizedShipmentLocation:
        data = await DHLService.buscar_en_dhl(tracking_id)
        normalized_location = self._normalize_location(tracking_id, data)
        await to_thread.run_sync(
            self.repository.upsert_location,
            normalized_location,
            data,
        )
        return normalized_location
    
    @classmethod
    def _normalize_location(
        cls,
        tracking_id: str,
        data: dict,
    ) -> NormalizedShipmentLocation:
        status_data = cls._extract_status_data(data)
        location_dict = status_data.get("location") or {}
        address_dict = location_dict.get("address") or {}
        raw_locality = address_dict.get("addressLocality", "")

        if " - " in raw_locality:
            city, country = raw_locality.split(" - ", 1)
            city_value = city.strip()
            location_value = country.strip()
        else:
            city_value = raw_locality.strip()
            location_value = address_dict.get("countryCode", "").strip()

        return NormalizedShipmentLocation(
            tracking_id=tracking_id,
            location=location_value or "País desconocido",
            city=city_value or "Ciudad desconocida",
            timestamp=status_data.get("timestamp", "Fecha desconocida"),
        )
