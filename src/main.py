from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, tracking
from src.core.config import settings
from src.db.connection import init_db
from src.services.tracking_poller import poll_tracked_shipments


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    poller_task = asyncio.create_task(poll_tracked_shipments())
    try:
        yield
    finally:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass


src = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

src.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
src.include_router(auth.router)
src.include_router(tracking.router)

@src.get("/", tags=["General"])
async def health():
    """Revisar estado de la API."""
    return {"service": settings.PROJECT_NAME, "status": "online"}
