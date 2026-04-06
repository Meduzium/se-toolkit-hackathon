"""
FastAPI Configuration
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/music_bot_db"
    api_title: str = "Music Bot API"
    api_version: str = "1.0.0"
    genius_api_key: str = ""
    audio_download_dir: str = "./downloads"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
