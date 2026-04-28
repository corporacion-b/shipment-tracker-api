from fastapi import FastAPI
from src.api.routes import tracking
from src.core.config import settings

src = FastAPI(title=settings.PROJECT_NAME)

# Rutas
src.include_router(tracking.router)

@src.get("/", tags=["General"])
async def root():
    """Estado de la API."""
    return {"service": settings.PROJECT_NAME, "status": "online"}