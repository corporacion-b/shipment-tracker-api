from fastapi import APIRouter, Path, HTTPException, status
from src.services.dhl import DHLService
from src.schemas.tracking import ShipmentStatus

router = APIRouter()

@router.get(
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
    return await DHLService.buscar_en_dhl(tracking_id)

@router.get(
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
    data = await DHLService.buscar_en_dhl(tracking_id)
    try:
        shipment = data["shipments"][0]
        status_data = shipment.get("status", {})
        return {
            "tracking_id": tracking_id,
            "status": status_data.get("status", "N/A"),
            "description": status_data.get("description", "Sin descripción")
        }
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Estructura de DHL inválida."
        )