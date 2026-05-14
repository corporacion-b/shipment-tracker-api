from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.api.dependencies import get_current_user
from src.repositories.shipment_repository import ShipmentRepository
from src.schemas.tracking import (
    DHLRawResponse,
    ShipmentDwellTime,
    ShipmentListResponse,
    ShipmentLocation,
    ShipmentRead,
    ShipmentStatus,
    ShipmentHistoryResponse,
)
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
    "/shipments",
    tags=["Shipments"],
    summary="Listar pedidos del usuario autenticado",
    response_model=ShipmentListResponse,
)
async def list_shipments(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, description="Busca por número de guía o id interno."),
    created_from: str | None = None,
    created_to: str | None = None,
    updated_from: str | None = None,
    updated_to: str | None = None,
    sort: str = Query(default="-updated_at"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return ShipmentRepository().list_for_user(
        user_id=current_user["id_user"],
        status=status_filter,
        q=q,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/shipments/{tracking_id}",
    tags=["Shipments"],
    summary="Obtener detalle de un pedido",
    response_model=ShipmentRead,
)
async def get_shipment_detail(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    shipment = ShipmentRepository().get_detail_for_user(
        tracking_id,
        current_user["id_user"],
    )

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guía '{tracking_id}' no existe para el usuario autenticado.",
        )

    return shipment


@router.post(
    "/shipments/{tracking_id}/refresh",
    tags=["Shipments"],
    summary="Consultar DHL y actualizar un pedido",
    response_model=ShipmentRead,
)
async def refresh_shipment(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    tracking_service = TrackingService()
    await tracking_service.get_status(tracking_id, current_user["id_user"])
    await tracking_service.get_current_location(tracking_id, current_user["id_user"])
    await tracking_service.get_history(tracking_id, current_user["id_user"])

    shipment = ShipmentRepository().get_detail_for_user(
        tracking_id,
        current_user["id_user"],
    )

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guía '{tracking_id}' no existe para el usuario autenticado.",
        )

    return shipment


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
async def get_status(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    """Obtiene únicamente el estado y descripción del paquete."""
    normalized_status = await TrackingService().get_status(
        tracking_id,
        current_user["id_user"],
    )

    return ShipmentStatus(
        tracking_id=normalized_status.tracking_id,
        status=normalized_status.status,
        weight=normalized_status.weight,
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
                        "country_code": "ES",
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
async def get_location(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    """Obtiene la ubicación actual del paquete."""
    normalized_location = await TrackingService().get_current_location(
        tracking_id,
        current_user["id_user"],
    )

    return ShipmentLocation(
        tracking_id=normalized_location.tracking_id,
        country_code=normalized_location.country_code,
        city=normalized_location.city,
        timestamp=normalized_location.timestamp,
    )


@router.get(
    "/dwell-time/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener tiempo inmóvil del paquete",
    description=(
        "Consulta DHL y calcula cuánto tiempo ha permanecido el paquete inmóvil "
        "en su ubicación actual. Este endpoint no aplica a envíos entregados."
    ),
    response_model=ShipmentDwellTime,
    responses={
        200: {
            "description": "Operación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "tracking_id": "7777777770",
                        "status": "TRANSIT",
                        "country_code": "ES",
                        "city": "Madrid",
                        "current_status_timestamp": "2024-04-16T09:30:00Z",
                        "dwell_time_hours": 48.5,
                        "dwell_time_days": 2.02,
                    }
                }
            },
        },
        422: {
            "description": (
                "La estructura del JSON de DHL cambió, es inválida o el envío "
                "ya fue entregado"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": "El dwell time no aplica a envios entregados."
                    }
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_dwell_time(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    """Obtiene el tiempo inmóvil estimado del paquete en su ubicación actual."""
    dwell_time = await TrackingService().get_dwell_time(
        tracking_id,
        current_user["id_user"],
    )

    return ShipmentDwellTime(
        tracking_id=dwell_time.tracking_id,
        status=dwell_time.status,
        country_code=dwell_time.country_code,
        city=dwell_time.city,
        current_status_timestamp=dwell_time.current_status_timestamp,
        dwell_time_hours=dwell_time.dwell_time_hours,
        dwell_time_days=dwell_time.dwell_time_days,
    )

@router.get(
    "/history/{tracking_id}",
    tags=["Tracking"],
    summary="Obtener historial de eventos",
    response_model=ShipmentHistoryResponse,
    responses={**COMMON_ERROR_RESPONSES},
)
async def get_history(
    tracking_id: str = TRACKING_ID_PATH,
    current_user: dict = Depends(get_current_user),
):
    """Retorna la línea de tiempo de movimientos del paquete."""
    history_events = await TrackingService().get_history(
        tracking_id,
        current_user["id_user"],
    )

    return ShipmentHistoryResponse(
        tracking_id=tracking_id,
        history=history_events
    )
