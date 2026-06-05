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
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="La API de DHL tardó demasiado.")
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                detail = f"Guía '{tracking_id}' no encontrada." if status_code == 404 else e.response.text
                raise HTTPException(status_code=status_code, detail=detail)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

        shipments = data.get("shipments")
        if not data or not shipments or len(shipments) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Guía '{tracking_id}' no encontrada en los registros de DHL."
            )

        return data

    @staticmethod
    async def obtener_coordenadas(city: str) -> tuple[float, float]:
        """
        Obtiene la lista de ubicaciones del mock en Railway mapeando la estructura
        bajo la llave 'locations' para extraer latitud y longitud.
        """
        url_locations_list = "https://shipment-tracker-mock-api-production.up.railway.app/locations"
        ciudad_buscada = city.lower().strip()
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url_locations_list)
                if response.status_code == 200:
                    data = response.json()
                    
                    locations = data.get("locations", []) if isinstance(data, dict) else data
                    
                    for loc in locations:
                        ciudad_mock = loc.get("city", "").lower().strip()
                        
                        if ciudad_buscada in ciudad_mock or ciudad_mock in ciudad_buscada:
                            lat = loc.get("latitude")
                            lon = loc.get("longitude")
                            if lat is not None and lon is not None:
                                return float(lat), float(lon)
                                
            except Exception:
                pass
                
        return 0.0, 0.0