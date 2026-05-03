from pydantic import BaseModel

class ShipmentStatus(BaseModel):
    tracking_id: str
    status: str
    description: str

class ShipmentLocation(BaseModel):
    tracking_id: str
    location: str
    city: str
    timestamp: str

class DHLRawResponse(BaseModel):
    shipments: list