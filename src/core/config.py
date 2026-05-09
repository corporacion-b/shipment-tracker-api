from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Shipment Tracker API"
    DHL_API_KEY: Optional[str] = None
    DHL_API_SECRET: Optional[str] = None
    DHL_BASE_URL: str = "https://api-eu.dhl.com/track/shipments"
    DATABASE_URL: str = "mysql://root:secret@127.0.0.1:3307/shipments"
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
