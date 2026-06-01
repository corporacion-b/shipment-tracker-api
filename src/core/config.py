from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Shipment Tracker API"
    DHL_API_KEY: Optional[str] = None
    DHL_API_SECRET: Optional[str] = None
    DHL_BASE_URL: str = "https://shipment-tracker-mock-api-production.up.railway.app/track/shipments"
    DATABASE_URL: str = "mysql://root:secret@127.0.0.1:3307/shipments"
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: Optional[str] = None
    BREVO_SENDER_NAME: str = "Shipment Tracker"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    RISK_ANALYZER_BASE_URL: Optional[str] = None
    TRACKING_POLL_INTERVAL_SECONDS: int = 60
    TRACKING_POLL_START_DELAY_SECONDS: int = 10
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440
    EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS: int = 60
    FRONTEND_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
