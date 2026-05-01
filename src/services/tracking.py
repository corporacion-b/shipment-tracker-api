from anyio import to_thread
from fastapi import HTTPException, status

from src.repositories.shipment_repository import (
    NormalizedShipmentStatus,
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
