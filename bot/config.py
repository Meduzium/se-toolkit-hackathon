"""
Bot configuration
"""

from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    telegram_bot_token: str = ""
    backend_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
