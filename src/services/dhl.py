import httpx
from fastapi import HTTPException, status
from src.core.config import settings

class DHLService:
    @staticmethod
    async def buscar_en_dhl(tracking_id: str):
        if not settings.DHL_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de configuración: DHL_API_KEY no encontrada."
            )

        params = {"trackingNumber": tracking_id}
        headers = {"DHL-API-Key": settings.DHL_API_KEY}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(settings.DHL_BASE_URL, params=params, headers=headers)
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="La API de DHL tardó demasiado.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Guía '{tracking_id}' no existe.")
        
        if response.is_error:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()