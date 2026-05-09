from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.api.routes import auth, tracking
from src.core.config import settings
from src.db.connection import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


src = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Rutas
src.include_router(auth.router)
src.include_router(tracking.router)

@src.get("/", tags=["General"])
async def root():
    """Estado de la API."""
    return {"service": settings.PROJECT_NAME, "status": "online"}
