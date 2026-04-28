from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Shipment Tracker API"
    DHL_API_KEY: str
    DHL_API_SECRET: str
    DHL_BASE_URL: str = "https://api-eu.dhl.com/track/shipments"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()