from pydantic import BaseModel

class ShipmentStatus(BaseModel):
    tracking_id: str
    status: str
    description: str

class DHLRawResponse(BaseModel):
    shipments: list