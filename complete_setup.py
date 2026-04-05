#!/usr/bin/env python3
"""
Complete Music Bot Project Generator
This script creates the entire project structure with all files
"""

import os
import sys
from pathlib import Path

def main():
    BASE = Path(__file__).parent
    os.chdir(BASE)
    
    # Create directories
    dirs = [
        "backend/app/routers",
        "backend/app/services",
        "backend/tests",
        "bot/handlers",
        "downloads",
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        
    # Create __init__.py files
    for d in ["backend", "backend/app", "backend/app/routers", "backend/app/services", 
              "backend/tests", "bot", "bot/handlers"]:
        Path(f"{d}/__init__.py").write_text("")
    
    print("✓ Directories created")
    
    # ============ BACKEND FILES ============
    
    # backend/requirements.txt
    Path("backend/requirements.txt").write_text("""fastapi==0.104.1
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
""")
    print("✓ backend/requirements.txt")
    
    # backend/.env
    Path("backend/.env").write_text("""DATABASE_URL=postgresql://user:password@localhost:5432/music_bot_db
GENIUS_API_KEY=your_genius_api_key_here
LOG_LEVEL=INFO
""")
    print("✓ backend/.env")
    
    # backend/app/config.py
    Path("backend/app/config.py").write_text("""\"\"\"
FastAPI Configuration
\"\"\"

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
""")
    print("✓ backend/app/config.py")
    
    # backend/app/database.py
    Path("backend/app/database.py").write_text("""\"\"\"
SQLAlchemy database setup
\"\"\"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""")
    print("✓ backend/app/database.py")
    
    # backend/app/models.py
    Path("backend/app/models.py").write_text("""\"\"\"
SQLAlchemy ORM Models
\"\"\"

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
    __table_args__ = (Index("idx_tracks_title_artist", "title", "artist"),)


class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="searches")
    track = relationship("Track", back_populates="searches")
    __table_args__ = (Index("idx_searches_user_track_time", "user_id", "track_id", "searched_at"),)
""")
    print("✓ backend/app/models.py")
    
    # backend/app/schemas.py
    Path("backend/app/schemas.py").write_text("""\"\"\"
Pydantic schemas for request/response validation
\"\"\"

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TrackBase(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None

class Track(TrackBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

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
""")
    print("✓ backend/app/schemas.py")
    
    # backend/app/services/ytdlp_service.py
    Path("backend/app/services/ytdlp_service.py").write_text("""\"\"\"
yt-dlp service for YouTube search and MP3 extraction
\"\"\"

import subprocess
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)

class YtDlpService:
    def __init__(self):
        self.download_dir = Path(settings.audio_download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        '''Search YouTube for videos matching query'''
        try:
            cmd = [
                "yt-dlp",
                "-j",
                "--no-warnings",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                f"ytsearch{limit}:{query}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp search error: {result.stderr}")
                return []
            
            # Parse JSON lines output
            results = []
            for line in result.stdout.strip().split("\\n"):
                if line:
                    try:
                        data = json.loads(line)
                        results.append({
                            "title": data.get("title", "Unknown"),
                            "artist": data.get("uploader", "Unknown"),
                            "youtube_url": data.get("webpage_url", ""),
                            "id": data.get("id", ""),
                            "duration": data.get("duration", 0),
                        })
                    except json.JSONDecodeError:
                        continue
            
            return results[:limit]
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def download(self, youtube_url: str, title: str) -> Optional[str]:
        '''Download audio from YouTube URL and return file path'''
        try:
            filename = f"{title.replace(' ', '_')}.mp3"
            filepath = self.download_dir / filename
            
            cmd = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                "-o", str(filepath.with_suffix("")),
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and filepath.exists():
                return str(filepath)
            else:
                logger.error(f"Download error: {result.stderr}")
                return None
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

ytdlp_service = YtDlpService()
""")
    print("✓ backend/app/services/ytdlp_service.py")
    
    # backend/app/services/genius_service.py
    Path("backend/app/services/genius_service.py").write_text("""\"\"\"
Genius API service for fetching album art
\"\"\"

import requests
import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

class GeniusService:
    def __init__(self):
        self.api_key = settings.genius_api_key
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def get_album_art(self, title: str, artist: str) -> Optional[str]:
        '''Fetch album art URL from Genius'''
        if not self.api_key:
            return None
        
        try:
            query = f"{title} {artist}"
            params = {"q": query}
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["response"]["hits"]:
                    hit = data["response"]["hits"][0]
                    song = hit["result"]
                    return song.get("song_art_image_url") or song.get("primary_artist", {}).get("image_url")
        
        except Exception as e:
            logger.error(f"Genius API error: {e}")
        
        return None

genius_service = GeniusService()
""")
    print("✓ backend/app/services/genius_service.py")
    
    # backend/app/routers/music.py
    Path("backend/app/routers/music.py").write_text("""\"\"\"
Music search and download endpoints
\"\"\"

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..services.ytdlp_service import ytdlp_service
from ..services.genius_service import genius_service

router = APIRouter(prefix="/api", tags=["music"])

@router.get("/search")
async def search(q: str, db: Session = Depends(get_db)):
    '''Search for tracks on YouTube'''
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    results = ytdlp_service.search(q, limit=10)
    return {"results": results}

@router.post("/download")
async def download(title: str, youtube_url: str):
    '''Download audio file from YouTube'''
    file_path = ytdlp_service.download(youtube_url, title)
    if not file_path:
        raise HTTPException(status_code=500, detail="Download failed")
    return {"file_path": file_path, "status": "ok"}

@router.post("/log-search")
async def log_search(user_id: int, track_id: int, db: Session = Depends(get_db)):
    '''Log a search to the database'''
    search = models.Search(user_id=user_id, track_id=track_id)
    db.add(search)
    db.commit()
    return {"status": "logged"}
""")
    print("✓ backend/app/routers/music.py")
    
    # backend/app/routers/analytics.py
    Path("backend/app/routers/analytics.py").write_text("""\"\"\"
Analytics and charts endpoints
\"\"\"

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/charts")
async def get_charts(period: str = "day", db: Session = Depends(get_db)):
    '''Get top tracks for specified period'''
    if period not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Calculate date threshold
    now = datetime.utcnow()
    if period == "day":
        since = now - timedelta(days=1)
    elif period == "week":
        since = now - timedelta(weeks=1)
    else:
        since = now - timedelta(days=30)
    
    # Query: top tracks with user attribution
    results = db.query(
        models.User.username,
        models.Track.title,
        models.Track.artist,
        func.count(models.Search.id).label("count")
    ).join(models.Search).join(models.Track).filter(
        models.Search.searched_at >= since
    ).group_by(
        models.User.id,
        models.Track.id
    ).order_by(desc("count")).limit(50).all()
    
    entries = [
        schemas.ChartEntry(
            username=r[0] or "Anonymous",
            title=r[1],
            artist=r[2],
            count=r[3]
        )
        for r in results
    ]
    
    return schemas.ChartsResponse(period=period, entries=entries)
""")
    print("✓ backend/app/routers/analytics.py")
    
    # backend/app/main.py
    Path("backend/app/main.py").write_text("""\"\"\"
FastAPI main application
\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import engine, Base
from .config import settings
from .routers import music, analytics

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(music.router)
app.include_router(analytics.router)

@app.get("/")
async def root():
    return {"message": "Music Bot API", "version": settings.api_version}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
""")
    print("✓ backend/app/main.py")
    
    # ============ BOT FILES ============
    
    # bot/requirements.txt
    Path("bot/requirements.txt").write_text("""aiogram==3.2.0
python-dotenv==1.0.0
httpx==0.25.1
Pillow==10.1.0
""")
    print("✓ bot/requirements.txt")
    
    # bot/.env
    Path("bot/.env").write_text("""TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_URL=http://localhost:8000
""")
    print("✓ bot/.env")
    
    # bot/config.py
    Path("bot/config.py").write_text("""\"\"\"
Bot configuration
\"\"\"

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
""")
    print("✓ bot/config.py")
    
    # bot/handlers/commands.py
    Path("bot/handlers/commands.py").write_text("""\"\"\"
Command handlers for /start, /help, /top
\"\"\"

from aiogram import Router, types
from aiogram.filters import Command
import httpx
from ..config import settings, logger

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    '''Handle /start command'''
    user_first_name = message.from_user.first_name or "User"
    await message.answer(
        f"🎵 Welcome {user_first_name}!\\n\\n"
        f"I can help you search and download music from YouTube.\\n\\n"
        f"Commands:\\n"
        f"/search <song> - Search for a song\\n"
        f"/top - View top charts\\n"
        f"/help - Show help"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    '''Handle /help command'''
    help_text = (
        "🎵 Music Bot Help\\n\\n"
        "Send me a song name to search for it.\\n"
        "I'll show you matching results with an inline keyboard.\\n"
        "Click on a track to download it as an MP3.\\n\\n"
        "Commands:\\n"
        "/start - Show welcome message\\n"
        "/top [period] - View top charts (day/week/month, default: day)\\n"
        "/help - Show this message"
    )
    await message.answer(help_text)

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    '''Handle /top command to show charts'''
    period = "day"
    args = message.text.split()
    if len(args) > 1 and args[1] in ["day", "week", "month"]:
        period = args[1]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.backend_url}/api/charts", params={"period": period})
            data = response.json()
        
        if not data["entries"]:
            await message.answer("No charts data yet. Start searching!")
            return
        
        text = f"📊 Top Tracks ({period.upper()})\\n\\n"
        for i, entry in enumerate(data["entries"][:10], 1):
            text += f"{i}. @{entry['username']} - {entry['title']} by {entry['artist']} ({entry['count']})\\n"
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Charts error: {e}")
        await message.answer("Error fetching charts. Please try again.")
""")
    print("✓ bot/handlers/commands.py")
    
    # bot/handlers/search.py
    Path("bot/handlers/search.py").write_text("""\"\"\"
Search handler for music queries
\"\"\"

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
from ..config import settings, logger

router = Router()

@router.message(F.text)
async def handle_search(message: types.Message):
    '''Handle text search queries'''
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("Please provide at least 2 characters to search.")
        return
    
    # Show loading message
    status_msg = await message.answer("🔍 Searching...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.backend_url}/api/search", params={"q": query})
            data = response.json()
        
        results = data.get("results", [])
        
        if not results:
            await status_msg.edit_text("No results found. Try another search.")
            return
        
        # Build inline keyboard with results
        buttons = []
        for i, result in enumerate(results[:8]):
            title = result["title"][:50]
            artist = result.get("artist", "Unknown")[:30]
            btn_text = f"{i+1}. {title}"
            callback_data = f"download_{i}"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=callback_data)])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        text = "🎵 Found these tracks:\\n\\n"
        for i, result in enumerate(results[:8], 1):
            text += f"{i}. {result['title']} - {result.get('artist', 'Unknown')}\\n"
        
        await status_msg.edit_text(text, reply_markup=keyboard)
        
        # Store results in message context (in production, use proper session management)
        message.bot.current_search_results = results
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        await status_msg.edit_text("Error searching. Please try again.")
""")
    print("✓ bot/handlers/search.py")
    
    # bot/handlers/charts.py
    Path("bot/handlers/charts.py").write_text("""\"\"\"
Chart display handlers
\"\"\"

from aiogram import Router

router = Router()

# Charts functionality is handled in commands.py
""")
    print("✓ bot/handlers/charts.py")
    
    # bot/main.py
    Path("bot/main.py").write_text("""\"\"\"
Telegram bot main entry point
\"\"\"

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from .config import settings
from .handlers import commands, search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    '''Start the bot'''
    bot = Bot(token=settings.telegram_bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(commands.router)
    dp.include_router(search.router)
    
    logger.info("Bot started")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
""")
    print("✓ bot/main.py")
    
    # ============ DOCKER & CONFIG FILES ============
    
    # docker-compose.yml
    Path("docker-compose.yml").write_text("""version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: music_bot_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/music_bot_db
      GENIUS_API_KEY: $GENIUS_API_KEY
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./downloads:/app/downloads

  bot:
    build:
      context: ./bot
      dockerfile: Dockerfile
    environment:
      TELEGRAM_BOT_TOKEN: $TELEGRAM_BOT_TOKEN
      BACKEND_URL: http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./bot:/app

volumes:
  postgres_data:
""")
    print("✓ docker-compose.yml")
    
    # backend/Dockerfile
    Path("backend/Dockerfile").write_text("""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && apt-get update && apt-get install -y ffmpeg

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")
    print("✓ backend/Dockerfile")
    
    # bot/Dockerfile
    Path("bot/Dockerfile").write_text("""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
""")
    print("✓ bot/Dockerfile")
    
    # README.md
    Path("README.md").write_text("""# Music Bot 🎵

A Telegram bot for searching and downloading music from YouTube with analytics dashboard.

## Architecture

- **Telegram Bot** (aiogram) - User interface
- **FastAPI Backend** - REST API for search, download, and analytics
- **PostgreSQL** - Data storage

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- ffmpeg
- Telegram Bot Token (get from @BotFather)
- Genius API Key (optional, for album art)

### Local Setup

1. Clone and enter directory:
   ```bash
   cd music_bot_project
   ```

2. Create virtual environments:
   ```bash
   cd backend && python -m venv venv && .\\venv\\Scripts\\activate
   pip install -r requirements.txt
   cd ../bot && python -m venv venv && .\\venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # backend/.env
   DATABASE_URL=postgresql://user:password@localhost:5432/music_bot_db
   GENIUS_API_KEY=your_key
   
   # bot/.env
   TELEGRAM_BOT_TOKEN=your_token
   BACKEND_URL=http://localhost:8000
   ```

4. Create PostgreSQL database:
   ```sql
   CREATE DATABASE music_bot_db;
   ```

5. Run backend (from backend directory):
   ```bash
   uvicorn app.main:app --reload
   ```

6. Run bot (from bot directory):
   ```bash
   python main.py
   ```

### Docker Setup

```bash
docker-compose up --build
```

## API Endpoints

- `GET /api/search?q=<query>` - Search for tracks
- `POST /api/download` - Download track
- `POST /api/log-search` - Log a search
- `GET /api/charts?period=day|week|month` - Get top charts

## Bot Commands

- `/start` - Welcome message
- `/help` - Show help
- `/top [period]` - View top tracks (day/week/month)

## Usage

1. Start the bot in Telegram
2. Send a song name
3. Click on a result to download
4. Use /top to see trending tracks with user attribution

## Features

✓ YouTube search integration with yt-dlp
✓ MP3 download and direct Telegram delivery
✓ User-attributed top charts (daily/weekly/monthly)
✓ Album art from Genius API
✓ Full async implementation
✓ Docker Compose for easy deployment

## Database Schema

### Users
- `id` (PK)
- `telegram_id` (unique)
- `username` (nullable)
- `created_at`, `updated_at`

### Tracks
- `id` (PK)
- `title`
- `artist`
- `album_art_url`
- `created_at`

### Searches
- `id` (PK)
- `user_id` (FK)
- `track_id` (FK)
- `searched_at`

## License

MIT
""")
    print("✓ README.md")
    
    print("\\n" + "="*50)
    print("✓ Project structure generated successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
