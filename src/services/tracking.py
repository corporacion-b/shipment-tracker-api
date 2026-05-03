from anyio import to_thread
from fastapi import HTTPException, status

from src.repositories.shipment_repository import (
    NormalizedShipmentStatus,
    NormalizedShipmentLocation,
    ShipmentRepository,
)
from src.services.dhl import DHLService


class TrackingService:
    def __init__(self, repository: ShipmentRepository | None = None):
        self.repository = repository or ShipmentRepository()

    async def get_status(self, tracking_id: str) -> NormalizedShipmentStatus:
        data = await DHLService.buscar_en_dhl(tracking_id)
        normalized_status = self._normalize_status(tracking_id, data)
        await to_thread.run_sync(
            self.repository.upsert_status,
            normalized_status,
            data,
        )
        return normalized_status

    @staticmethod
    def _normalize_status(
        tracking_id: str,
        data: dict,
    ) -> NormalizedShipmentStatus:
        try:
            shipment = data["shipments"][0]
            status_data = shipment.get("status", {})
        except (KeyError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        return NormalizedShipmentStatus(
            tracking_id=tracking_id,
            carrier="DHL",
            status=status_data.get("status", "N/A"),
            description=status_data.get("description", "Sin descripción"),
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
    
    @staticmethod
    def _normalize_location(
        tracking_id: str,
        data: dict,
    ) -> NormalizedShipmentLocation:
        try:
            shipment = data["shipments"][0]
            status_data = shipment.get("status", {})
            location_dict = status_data.get("location", {})
            address_dict = location_dict.get("address", {})
            country = address_dict.get("countryCode", "")
            
            raw_locality = address_dict.get("addressLocality", "")
            if " - " in raw_locality:
                country_name = raw_locality.split(" - ")[1].strip()
            else:
                country_name = country
            
            location_only_country = country_name if country_name else "País desconocido"
            city_clean = raw_locality.split(" - ")[0].strip() if " - " in raw_locality else raw_locality
            city_final = city_clean if city_clean else "Ciudad desconocida"
            timestamp = status_data.get("timestamp", "Fecha desconocida")
            
        except (KeyError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Estructura de DHL inválida.",
            )

        return NormalizedShipmentLocation(
            tracking_id=tracking_id,
            location=location_only_country,
            city=city_final,
            timestamp=timestamp,
        )