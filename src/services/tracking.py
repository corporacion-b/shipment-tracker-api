from anyio import to_thread
from fastapi import HTTPException, status

from src.repositories.shipment_repository import (
    NormalizedShipmentStatus,
    NormalizedShipmentLocation,
    NormalizedShipmentHistory,
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
    def _normalize_status(
        cls,
        tracking_id: str,
        data: dict,
    ) -> NormalizedShipmentStatus:
        status_data = cls._extract_status_data(data)

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
    
    async def get_history(self, tracking_id: str) -> NormalizedShipmentHistory:
        data = await DHLService.buscar_en_dhl(tracking_id)
        normalized_history = self._normalize_history(tracking_id, data)
        
        # Guardamos en hilo separado para no bloquear la respuesta
        await to_thread.run_sync(
            self.repository.upsert_history,
            normalized_history,
            data,
        )
        return normalized_history
    
    @classmethod
    def _normalize_history(cls, tracking_id: str, data: dict) -> NormalizedShipmentHistory:
        try:
            shipments = data.get("shipments", [])
            if not shipments:
                raise ValueError("No se encontraron envíos para esta guía.")
            
            events = shipments[0].get("events", [])
            if not isinstance(events, list):
                events = []

            return NormalizedShipmentHistory(
                tracking_id=tracking_id,
                events=events, # DHL ya los entrega ordenados cronológicamente
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Error al procesar historial de DHL: {str(e)}",
            )