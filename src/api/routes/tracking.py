from fastapi import APIRouter, Path
from src.services.dhl import DHLService
from src.schemas.tracking import ShipmentStatus, ShipmentLocation
from src.services.tracking import TrackingService

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
    normalized_status = await TrackingService().get_status(tracking_id)
    return ShipmentStatus(
        tracking_id=normalized_status.tracking_id,
        status=normalized_status.status,
        description=normalized_status.description,
    )

@router.get(
    "/location/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener ubicación del paquete",
    description="Filtra la respuesta de DHL para entregar la ubicación actual del paquete.",
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "tracking_id": "12345678",
                        "location": "Spain",
                        "city": "Madrid",
                        "timestamp": "2024-04-16T09:30:00Z"
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
async def get_location(
    tracking_id: str = Path(..., examples="7777777770", description="Número de guía DHL")
    ):
    """Obtiene la ubicación actual del paquete."""
    normalized_location = await TrackingService().get_location(tracking_id)
    return ShipmentLocation (
        tracking_id=normalized_location.tracking_id,
        location=normalized_location.location,
        city=normalized_location.city,
        timestamp=normalized_location.timestamp,
    )
