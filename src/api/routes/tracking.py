from fastapi import APIRouter, Path

from src.schemas.tracking import DHLRawResponse, ShipmentLocation, ShipmentStatus
from src.services.dhl import DHLService
from src.services.tracking import TrackingService


router = APIRouter()


TRACKING_ID_PATH = Path(
    ...,
    description="Número de guía DHL",
    openapi_examples={
        "guia_dhl": {
            "summary": "Guía DHL de ejemplo",
            "value": "7777777770",
        }
    },
)


COMMON_ERROR_RESPONSES = {
    404: {
        "description": "El número de rastreo no existe en los registros",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Guía '7777777770' no existe."
                }
            }
        },
    },
    500: {
        "description": "Error de configuración o conexión inesperada",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error de configuración: DHL_API_KEY no encontrada."
                }
            }
        },
    },
    504: {
        "description": "DHL no respondió a tiempo",
        "content": {
            "application/json": {
                "example": {
                    "detail": "La API de DHL tardó demasiado."
                }
            }
        },
    },
}


@router.get(
    "/full-tracking/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener tracking completo desde DHL",
    description=(
        "Consulta DHL con el número de guía recibido y devuelve el JSON completo "
        "sin filtrar. Este endpoint sirve para revisar la respuesta original de DHL."
    ),
    response_model=DHLRawResponse,
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "shipments": [
                            {
                                "id": "7777777770",
                                "status": {
                                    "status": "TRANSIT",
                                    "description": "The shipment is in transit",
                                    "timestamp": "2024-04-16T09:30:00Z",
                                    "location": {
                                        "address": {
                                            "addressLocality": "Madrid - Spain",
                                            "countryCode": "ES",
                                        }
                                    },
                                },
                            }
                        ]
                    }
                }
            },
        },
        422: {
            "description": "El parámetro tracking_id es inválido",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "tracking_id"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_full_tracking(tracking_id: str = TRACKING_ID_PATH):
    """Retorna la respuesta completa de DHL sin filtros."""
    return await DHLService.buscar_en_dhl(tracking_id)


@router.get(
    "/status/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener estado del paquete",
    description=(
        "Consulta DHL y filtra la respuesta para entregar solo el número de guía, "
        "el estado actual y la descripción del estado."
    ),
    response_model=ShipmentStatus,
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "tracking_id": "7777777770",
                        "status": "TRANSIT",
                        "description": "The shipment is in transit",
                    }
                }
            },
        },
        422: {
            "description": "La estructura del JSON de DHL cambió o es inválida",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Estructura de DHL inválida."
                    }
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_status(tracking_id: str = TRACKING_ID_PATH):
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
    description=(
        "Consulta DHL y filtra la respuesta para entregar solo el número de guía, "
        "la ubicación, la ciudad y la fecha del último estado reportado."
    ),
    response_model=ShipmentLocation,
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "tracking_id": "7777777770",
                        "location": "Spain",
                        "city": "Madrid",
                        "timestamp": "2024-04-16T09:30:00Z",
                    }
                }
            },
        },
        422: {
            "description": "La estructura del JSON de DHL cambió o es inválida",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Estructura de DHL inválida."
                    }
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_location(tracking_id: str = TRACKING_ID_PATH):
    """Obtiene la ubicación actual del paquete."""
    normalized_location = await TrackingService().get_location(tracking_id)

    return ShipmentLocation(
        tracking_id=normalized_location.tracking_id,
        location=normalized_location.location,
        city=normalized_location.city,
        timestamp=normalized_location.timestamp,
    )