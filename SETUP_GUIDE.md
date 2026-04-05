# 🎵 Telegram Music Bot Setup Guide

## Quick Start

This is a complete Telegram music bot with YouTube integration, search, and trending charts.

### System Requirements

- **Python 3.10+**
- **PostgreSQL 12+**
- **FFmpeg** (for audio conversion)
- **Telegram Bot Token** (from @BotFather on Telegram)
- **Genius API Key** (optional, for album art)

### Installation Steps

#### 1. Install Python Dependencies

**Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Bot:**
```bash
cd ../bot
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Install System Dependencies

**Windows (using Chocolatey):**
```bash
choco install ffmpeg postgresql
```

**macOS (using Homebrew):**
```bash
brew install ffmpeg postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg postgresql-client
```

#### 3. Set Up PostgreSQL Database

**Windows (PowerShell):**
```powershell
# Start PostgreSQL service
Start-Service postgresql-x64-16

# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE music_bot_db;
\q
```

**macOS/Linux:**
```bash
# Start PostgreSQL
brew services start postgresql
# or
sudo service postgresql start

# Connect
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE music_bot_db;
\q
```

#### 4. Configure Environment Variables

**Backend (.env):**
```bash
cd backend
cp .env.example .env
# Edit .env with your settings
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/music_bot_db
GENIUS_API_KEY=your_genius_api_key_here
LOG_LEVEL=INFO
```

**Bot (.env):**
```bash
cd ../bot
# Edit .env with your settings
```

Edit `bot/.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_URL=http://localhost:8000
```

#### 5. Run the Backend

```bash
cd backend

# Activate venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 6. Run the Bot (in another terminal)

```bash
cd bot

# Activate venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

python main.py
```

You should see:
```
INFO - Bot started. Backend URL: http://localhost:8000
```

---

## Docker Setup (Alternative)

If you have Docker and Docker Compose installed:

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN=your_bot_token
export GENIUS_API_KEY=your_key

# Start all services
docker-compose up --build

# View logs
docker-compose logs -f
```

Services will be available at:
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

---

## Usage

### Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/start`
3. Send `/newbot`
4. Follow the prompts
5. Copy your bot token

### Get Genius API Key (Optional)

1. Visit https://genius.com/api-clients
2. Create an app
3. Generate access token
4. Copy your API key

### Using the Bot

1. Find your bot on Telegram (use the username you created)
2. Send `/start` to initialize
3. Send a song name (e.g., "Imagine by John Lennon")
4. Click on results to download as MP3
5. Use `/top` to see trending tracks
6. Use `/help` for more commands

---

## API Endpoints

### Search
```
GET /api/search?q=song_name
```
Returns list of YouTube search results

### Download
```
POST /api/download
{
    "title": "Song Title",
    "youtube_url": "https://..."
}
```

### Log Search
```
POST /api/log-search
{
    "user_id": 123,
    "track_id": 456
}
```

### Charts
```
GET /api/charts?period=day|week|month
```
Returns top tracks for the specified period

---

## Troubleshooting

### Backend Connection Refused
- Ensure PostgreSQL is running
- Check DATABASE_URL in backend/.env
- Verify port 8000 is not in use

### Bot Not Responding
- Check TELEGRAM_BOT_TOKEN
- Ensure backend is running
- Check bot logs for errors

### yt-dlp Errors
- Install ffmpeg: `pip install yt-dlp ffmpeg-python`
- Check YouTube URL accessibility
- yt-dlp updates frequently; update with: `pip install --upgrade yt-dlp`

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql postgresql://user:password@localhost:5432/music_bot_db

# Create tables manually if needed
psql -d music_bot_db -f schema.sql
```

---

## Project Structure

```
music_bot_project/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration & settings
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── music.py     # Search & download endpoints
│   │   │   ├── analytics.py # Charts endpoints
│   │   ├── services/
│   │   │   ├── ytdlp_service.py     # YouTube download wrapper
│   │   │   ├── genius_service.py    # Genius API client
│   ├── requirements.txt
│   ├── .env
│   ├── Dockerfile
│   ├── tests/
├── bot/
│   ├── main.py              # Bot entry point
│   ├── config.py            # Bot configuration
│   ├── handlers/
│   │   ├── commands.py      # /start, /help, /top
│   │   ├── search.py        # Search query handling
│   ├── requirements.txt
│   ├── .env
│   ├── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## Database Schema

### users
```sql
id              INTEGER PRIMARY KEY
telegram_id     BIGINT UNIQUE NOT NULL
username        VARCHAR(255) NULLABLE
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

### tracks
```sql
id              INTEGER PRIMARY KEY
title           VARCHAR(500) NOT NULL
artist          VARCHAR(500) NOT NULL
album_art_url   VARCHAR(2000) NULLABLE
created_at      TIMESTAMP DEFAULT NOW()
```

### searches
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER FOREIGN KEY REFERENCES users(id)
track_id        INTEGER FOREIGN KEY REFERENCES tracks(id)
searched_at     TIMESTAMP DEFAULT NOW() INDEXED
```

---

## Development

### Run Tests
```bash
cd backend
pytest tests/
```

### View API Documentation
Navigate to `http://localhost:8000/docs` (Swagger UI)

### Check Database
```bash
psql -d music_bot_db

SELECT * FROM users;
SELECT * FROM tracks;
SELECT * FROM searches;
```

---

## Performance Tips

- Use the `GENIUS_API_KEY` for faster album art loading
- yt-dlp caches results; clear if needed with `yt-dlp --rm-cache-dir`
- PostgreSQL indices are optimized for chart queries
- Bot uses async/await for responsive UI

---

## License

MIT License - Feel free to use and modify!

---

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review logs in backend and bot terminals
3. Ensure all services are running (`postgres`, `backend`, `bot`)

Good luck! 🎵
