import asyncio
from datetime import timedelta

from src.core.config import settings
from src.core.security import create_access_token
from src.repositories.shipment_repository import ShipmentRepository
from src.services.shipment_refresh import ShipmentRefreshService


async def poll_tracked_shipments() -> None:
    if settings.TRACKING_POLL_INTERVAL_SECONDS <= 0:
        return

    if settings.TRACKING_POLL_START_DELAY_SECONDS > 0:
        await asyncio.sleep(settings.TRACKING_POLL_START_DELAY_SECONDS)

    repository = ShipmentRepository()
    refresh_service = ShipmentRefreshService()

    while True:
        targets = repository.list_polling_targets()

        for target in targets:
            tracking_id = target["tracking_id"]
            user_id = int(target["id_user"])
            token = create_access_token(
                subject=str(user_id),
                expires_delta=timedelta(minutes=10),
            )

            try:
                await refresh_service.refresh_and_evaluate(tracking_id, user_id, token)
            except Exception as exc:
                print(f"Tracking poll failed for {tracking_id}: {exc}")

        await asyncio.sleep(settings.TRACKING_POLL_INTERVAL_SECONDS)
