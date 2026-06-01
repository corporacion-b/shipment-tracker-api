from fastapi import HTTPException

from src.repositories.shipment_repository import ShipmentRepository
from src.services.risk_analyzer import RiskAnalyzerClient
from src.services.tracking import TrackingService


class ShipmentRefreshService:
    def __init__(
        self,
        tracking_service: TrackingService | None = None,
        shipment_repository: ShipmentRepository | None = None,
        risk_analyzer_client: RiskAnalyzerClient | None = None,
    ):
        self.tracking_service = tracking_service or TrackingService()
        self.shipment_repository = shipment_repository or ShipmentRepository()
        self.risk_analyzer_client = risk_analyzer_client or RiskAnalyzerClient()

    async def refresh_and_evaluate(self, tracking_id: str, user_id: int, token: str) -> dict | None:
        previous_shipment = self.shipment_repository.get_detail_for_user(tracking_id, user_id)

        await self.tracking_service.get_status(tracking_id, user_id)
        await self.tracking_service.get_current_location(tracking_id, user_id)
        await self.tracking_service.get_history(tracking_id, user_id)

        shipment = self.shipment_repository.get_detail_for_user(tracking_id, user_id)
        if shipment is None:
            return None

        dwell_time_days = None
        try:
            dwell_time = await self.tracking_service.get_dwell_time(tracking_id, user_id)
            dwell_time_days = dwell_time.dwell_time_days
        except HTTPException:
            dwell_time_days = None

        await self.risk_analyzer_client.evaluate_shipment_update(
            token=token,
            payload={
                "dhl_id": shipment["tracking_id"],
                "id_shipment": shipment["id_shipment"],
                "previous_status": previous_shipment["status"] if previous_shipment else None,
                "current_status": shipment["status"],
                "current_location": (
                    shipment["current_location"]["id_location"]
                    if shipment.get("current_location")
                    else None
                ),
                "dwell_time_days": dwell_time_days,
                "max_days_stopped": 3,
            },
        )

        return shipment
