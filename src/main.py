import os
import httpx
from fastapi import FastAPI, HTTPException, status, Path
from dotenv import load_dotenv

load_dotenv()

src = FastAPI(
    title="Shipment Tracker API",
    description="API para el rastreo de paquetes DHL con manejo de errores optimizado."
)

DHL_API_KEY = os.getenv("DHL_API_KEY")
DHL_BASE_URL = "https://api-eu.dhl.com/track/shipments"

async def buscar_en_dhl(tracking_id: str):
    if not DHL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración: DHL_API_KEY no encontrada."
        )

    params = {"trackingNumber": tracking_id}
    headers = {"DHL-API-Key": DHL_API_KEY}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(DHL_BASE_URL, params=params, headers=headers)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="La API de DHL tardó demasiado en responder."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado de conexión: {str(e)}"
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El número de rastreo '{tracking_id}' no existe en DHL."
        )
    
    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error externo (DHL): {response.text}"
        )

    return response.json()

# Endpoints

@src.get("/", tags=["General"])
async def root():
    """Estado de la API."""
    return {
        "service": "Shipment Tracker API",
        "auth_ready": bool(DHL_API_KEY)
    }

@src.get(
    "/full-tracking/{tracking_id}", 
    tags=["Tracking"],
    summary="Obtiene el JSON completo de DHL.",
    responses={
        200: {"description": "Operación exitosa"},
        404: {"description": "El número de rastreo no existe en los registros"},
        500: {"description": "Error de configuración o conexión inesperada"},
        504: {"description": "DHL no respondió a tiempo"}
    }
)
async def get_full_tracking(tracking_id: str):
    """Retorna la respuesta completa de DHL sin filtros."""
    return await buscar_en_dhl(tracking_id)

@src.get(
    "/status/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener estado del paquete",
    description="Filtra la respuesta de DHL para entregar solo el estado y descripción.",
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "tracking_id": "12345678",
                        "status": "TRANSIT",
                        "description": "The shipment is in transit"
                    }
                }
            },
        },
        404: {"description": "El número de rastreo no existe en los registros"},
        422: {"description": "La estructura del JSON de DHL cambió o es inválida"},
        500: {"description": "Error de configuración o conexión inesperada"},
        504: {"description": "DHL no respondió a tiempo"}
    },
)
async def get_status(
    tracking_id: str = Path(..., examples="7777777770", description="Número de guía DHL")
):
    """Obtiene únicamente el estado y descripción del paquete."""
    data = await buscar_en_dhl(tracking_id)
    
    try:
        shipments = data.get("shipments", [])
        if not shipments:
            raise IndexError
            
        shipment = shipments[0]
        status_data = shipment.get("status", {})
        
        return {
            "tracking_id": tracking_id, 
            "status": status_data.get("status", "N/A"),
            "description": status_data.get("description", "Sin descripción disponible")
        }
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La respuesta de DHL no contiene la estructura de envío esperada."
        )