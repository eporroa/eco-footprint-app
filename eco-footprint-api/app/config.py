from pydantic import BaseModel
import os

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    cors_allow_origins: str = os.getenv("CORS_ALLOW_ORIGINS", "*")
    rate: float = float(os.getenv("OFFSET_RATE", "0.02"))

settings = Settings()