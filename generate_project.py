#!/usr/bin/env python3
"""
Music Bot Project Generator
Creates the complete project structure and all necessary files
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

# Create all directories
directories = [
    "backend/app/routers",
    "backend/app/services",
    "backend/tests",
    "bot/handlers",
    "downloads",
]

for directory in directories:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Create __init__.py files
init_dirs = [
    "backend",
    "backend/app",
    "backend/app/routers",
    "backend/app/services",
    "backend/tests",
    "bot",
    "bot/handlers",
]

for directory in init_dirs:
    Path(f"{directory}/__init__.py").touch()

print("✓ All directories and __init__ files created")

# Now create all the project files
files_content = {
    # Backend requirements
    "backend/requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
yt-dlp==2023.12.30
requests==2.31.0
httpx==0.25.1
pytest==7.4.3
pytest-asyncio==0.21.1
""",
    
    # Backend .env example
    "backend/.env": """DATABASE_URL=postgresql://user:password@localhost:5432/music_bot_db
GENIUS_API_KEY=your_genius_api_key_here
""",

    # Bot requirements
    "bot/requirements.txt": """aiogram==3.2.0
python-dotenv==1.0.0
httpx==0.25.1
Pillow==10.1.0
""",

    # Bot .env example
    "bot/.env": """TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_URL=http://localhost:8000
""",

    # Backend config.py
    "backend/app/config.py": '''"""
FastAPI Configuration
Loads environment variables and provides database connection settings
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/music_bot_db"
    
    # API
    api_title: str = "Music Bot API"
    api_version: str = "1.0.0"
    
    # Genius API
    genius_api_key: str = ""
    
    # Audio
    audio_download_dir: str = "./downloads"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = \'utf-8\'
        case_sensitive = False

settings = Settings()
''',

    # Database.py
    "backend/app/database.py": '''"""
SQLAlchemy database setup
Creates engine, session factory, and base model for ORM
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',

    # Models.py
    "backend/app/models.py": '''"""
SQLAlchemy ORM Models
Defines User, Track, and Search models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    searches = relationship("Search", back_populates="user")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), nullable=False)
    album_art_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    searches = relationship("Search", back_populates="track")
    
    __table_args__ = (
        Index("idx_tracks_title_artist", "title", "artist"),
    )


class Search(Base):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="searches")
    track = relationship("Track", back_populates="searches")
    
    __table_args__ = (
        Index("idx_searches_user_track_time", "user_id", "track_id", "searched_at"),
    )
''',

    # Schemas.py
    "backend/app/schemas.py": '''"""
Pydantic schemas for request/response validation
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Track schemas
class TrackBase(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None

class TrackCreate(TrackBase):
    pass

class Track(TrackBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Search schemas
class SearchBase(BaseModel):
    user_id: int
    track_id: int

class SearchCreate(SearchBase):
    pass

class Search(SearchBase):
    id: int
    searched_at: datetime
    
    class Config:
        from_attributes = True

# API Response schemas
class SearchResult(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None
    youtube_url: Optional[str] = None

class ChartEntry(BaseModel):
    username: Optional[str]
    title: str
    artist: str
    count: int

class ChartsResponse(BaseModel):
    period: str
    entries: List[ChartEntry]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    count: int
''',
}

# Create all files
for file_path, content in files_content.items():
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Created {file_path}")

print("\n✓ All files generated successfully!")
print("\nNext steps:")
print("1. Run: python backend/app/config.py")
print("2. Create PostgreSQL database")
print("3. Fill in .env files with your API keys")
print("4. Install dependencies and run the backend/bot")
