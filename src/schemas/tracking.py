from typing import Any

from pydantic import BaseModel, Field


class ShipmentStatus(BaseModel):
    tracking_id: str = Field(
        ...,
        description="Número de guía DHL consultado.",
        json_schema_extra={"example": "7777777770"},
    )
    status: str = Field(
        ...,
        description="Estado actual del envío.",
        json_schema_extra={"example": "TRANSIT"},
    )
    weight: float = Field(
        ...,
        description="Peso del envío.",
        json_schema_extra={"example": 10.5},
    )
    


class ShipmentLocation(BaseModel):
    tracking_id: str = Field(
        ...,
        description="Número de guía DHL consultado.",
        json_schema_extra={"example": "7777777770"},
    )
    country_code: str = Field(
        ...,
        description="País o ubicación principal del último estado reportado por DHL.",
        json_schema_extra={"example": "Spain"},
    )
    city: str = Field(
        ...,
        description="Ciudad del último estado reportado por DHL.",
        json_schema_extra={"example": "Madrid"},
    )
    timestamp: str = Field(
        ...,
        description="Fecha y hora del último estado reportado por DHL.",
        json_schema_extra={"example": "2024-04-16T09:30:00Z"},
    )


class ShipmentDwellTime(BaseModel):
    tracking_id: str = Field(
        ...,
        description="Número de guía DHL consultado.",
        json_schema_extra={"example": "7777777770"},
    )
    status: str = Field(
        ...,
        description="Estado actual del envío.",
        json_schema_extra={"example": "TRANSIT"},
    )
    country_code: str = Field(
        ...,
        description="Código de país de la ubicación actual del envío.",
        json_schema_extra={"example": "ES"},
    )
    city: str = Field(
        ...,
        description="Ciudad actual del envío.",
        json_schema_extra={"example": "Madrid"},
    )
    current_status_timestamp: str = Field(
        ...,
        description="Fecha y hora del estado actual reportado por DHL.",
        json_schema_extra={"example": "2024-04-16T09:30:00Z"},
    )
    dwell_time_hours: float = Field(
        ...,
        description="Tiempo inmóvil estimado en horas.",
        json_schema_extra={"example": 48.5},
    )
    dwell_time_days: float = Field(
        ...,
        description="Tiempo inmóvil estimado en días.",
        json_schema_extra={"example": 2.02},
    )


class DHLRawResponse(BaseModel):
    shipments: list[dict[str, Any]] = Field(
        ...,
        description="Lista de envíos devuelta por DHL para el número de guía consultado.",
        json_schema_extra={
            "example": [
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
        },
    )
