from fastapi import FastAPI, HTTPException

src = FastAPI(title="Shipment Tracker API")

db = {
    "DHL-123": {
        "status": "In Transit",
        "location": "Mexico City",
        "days_stationary": 0
    },
    "DHL-456": {
        "status": "Held in Customs",
        "location": "Madrid",
        "days_stationary": 3
    },
    "DHL-789": {
        "status": "Delivered",
        "location": "New York",
        "days_stationary": 0
    }
}

@src.get("/")
async def root():
    return {"message": "API de Rastreo con DB simulada."}

@src.get("/status/{tracking_id}")
async def get_status(tracking_id: str):
    if tracking_id in db:
        shipment_info = db[tracking_id]
        return {
            "tracking_id": tracking_id,
            "status": shipment_info["status"],
            "location": shipment_info["location"],
            "days_stationary": shipment_info["days_stationary"]
        }
    
    raise HTTPException(status_code=404, detail="Envío no encontrado en el sistema")