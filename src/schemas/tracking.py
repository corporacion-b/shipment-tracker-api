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
    description: str = Field(
        ...,
        description="Descripción legible del estado actual del envío.",
        json_schema_extra={"example": "The shipment is in transit"},
    )


class ShipmentLocation(BaseModel):
    tracking_id: str = Field(
        ...,
        description="Número de guía DHL consultado.",
        json_schema_extra={"example": "7777777770"},
    )
    location: str = Field(
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