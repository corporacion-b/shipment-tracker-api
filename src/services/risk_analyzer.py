import httpx

from src.core.config import settings


class RiskAnalyzerClient:
    async def evaluate_shipment_update(
        self,
        token: str,
        payload: dict,
    ) -> None:
        if not settings.RISK_ANALYZER_BASE_URL:
            return

        url = f"{settings.RISK_ANALYZER_BASE_URL.rstrip('/')}/tracking/evaluate"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError:
            # El rastreo no debe fallar si el analizador no esta disponible.
            return

    async def delete_alerts_for_shipment(self, token: str, tracking_id: str) -> None:
        if not settings.RISK_ANALYZER_BASE_URL:
            return

        url = f"{settings.RISK_ANALYZER_BASE_URL.rstrip('/')}/tracking/alerts/by-shipment/{tracking_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.delete(url, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError:
            return
