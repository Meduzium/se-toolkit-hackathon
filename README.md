# 🎵 Telegram Music Bot

A modern Telegram bot for searching, downloading music from YouTube, and viewing trending charts with user attribution.

**Features:**
- 🔍 **YouTube Search** - Find any song on YouTube via yt-dlp
- 📥 **MP3 Download** - Download and send audio directly to Telegram
- 📊 **Trending Charts** - View daily, weekly, and monthly top tracks
- 👥 **User Attribution** - See who's searching what (e.g., "@username - Song Name")
- 🔐 **Secure** - All data stored in PostgreSQL, no external dependencies
- 🚀 **Fast** - Full async/await architecture with aiogram
- 🐳 **Docker Ready** - One-command deployment with Docker Compose

---

## Architecture

```
┌─────────────────────┐
│  Telegram Bot       │ (aiogram, async)
│  - Search Handler   │
│  - /top Command     │
│  - /start, /help    │
└──────────┬──────────┘
           │ REST API (httpx)
           ↓
┌─────────────────────┐
│  FastAPI Backend    │ (async, uvicorn)
│  /api/search        │
│  /api/download      │
│  /api/log-search    │
│  /api/charts        │
└──────────┬──────────┘
           │ SQL Queries
           ↓
┌─────────────────────┐
│  PostgreSQL         │ (users, tracks, searches)
│  - indexed queries  │
│  - aggregations     │
└─────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- FFmpeg
- Telegram Bot Token ([get from @BotFather](https://t.me/botfather))

### Local Setup (5 minutes)

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Bot (new terminal)
cd bot
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### Docker Setup (2 minutes)

```bash
export TELEGRAM_BOT_TOKEN=your_token_here
export GENIUS_API_KEY=your_key_here  # optional

docker-compose up --build
```

See **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** for detailed instructions.

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and instructions |
| `/help` | Show all commands |
| `/top [period]` | View top tracks (day/week/month) |

## How to Use

1. **Search**: Send a song name (e.g., "Bohemian Rhapsody")
2. **Select**: Click on a result to download
3. **Receive**: Get MP3 file in Telegram
4. **Explore**: Use `/top` to see what's trending

---

## API Reference

### GET /api/search?q=query
Search YouTube for tracks
```json
{
  "results": [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "album_art_url": "https://...",
      "youtube_url": "https://..."
    }
  ]
}
```

### POST /api/download
Download audio file
```json
{
  "title": "Song Title",
  "youtube_url": "https://..."
}
```

### POST /api/log-search
Log a user's search
```json
{
  "user_id": 123,
  "track_id": 456
}
```

### GET /api/charts?period=day|week|month
Get trending tracks
```json
{
  "period": "day",
  "entries": [
    {
      "username": "john_doe",
      "title": "Song Title",
      "artist": "Artist",
      "count": 5
    }
  ]
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  username VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tracks Table
```sql
CREATE TABLE tracks (
  id SERIAL PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  artist VARCHAR(500) NOT NULL,
  album_art_url VARCHAR(2000),
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tracks_title_artist ON tracks(title, artist);
```

### Searches Table
```sql
CREATE TABLE searches (
  id SERIAL PRIMARY KEY,
  user_id INTEGER FOREIGN KEY REFERENCES users(id),
  track_id INTEGER FOREIGN KEY REFERENCES tracks(id),
  searched_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_searches_user_track_time ON searches(user_id, track_id, searched_at);
```

---

## File Structure

```
music_bot_project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app with routes
│   │   ├── config.py            # Settings & env vars
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # ORM models (User, Track, Search)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── music.py         # Search & download endpoints
│   │   │   └── analytics.py     # Charts endpoint
│   │   ├── services/
│   │   │   ├── ytdlp_service.py # YouTube integration
│   │   │   └── genius_service.py# Album art fetching
│   │   └── tests/
│   ├── requirements.txt
│   ├── .env                     # Configuration
│   └── Dockerfile
│
├── bot/
│   ├── main.py                  # Bot entry point
│   ├── config.py                # Bot settings
│   ├── handlers/
│   │   ├── commands.py          # /start, /help, /top handlers
│   │   └── search.py            # Search query handling
│   ├── requirements.txt
│   ├── .env                     # Telegram token & backend URL
│   └── Dockerfile
│
├── docker-compose.yml           # Multi-service orchestration
├── SETUP_GUIDE.md              # Detailed setup instructions
├── README.md                   # This file
└── .gitignore
```

---

## Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/music_bot_db
GENIUS_API_KEY=your_genius_key_here
LOG_LEVEL=INFO
```

### Bot (.env)
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_URL=http://localhost:8000
```

---

## Dependencies

### Backend
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for database operations
- **psycopg2** - PostgreSQL adapter
- **yt-dlp** - YouTube download library
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Bot
- **aiogram** - Modern async Telegram bot framework
- **httpx** - Async HTTP client
- **python-dotenv** - Environment variable management

---

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### API Documentation
Open http://localhost:8000/docs for interactive Swagger UI

### Database Management
```bash
# Connect to database
psql postgresql://user:password@localhost:5432/music_bot_db

# View tables
\dt

# Check top searches
SELECT u.username, t.title, t.artist, COUNT(*) as count
FROM searches s
JOIN users u ON s.user_id = u.id
JOIN tracks t ON s.track_id = t.id
GROUP BY u.id, t.id
ORDER BY count DESC
LIMIT 10;
```

---

## Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL is running
psql postgresql://localhost/music_bot_db

# Check port 8000 is free
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux
```

### Bot not responding
```bash
# Check bot token in bot/.env
# Check backend is running and accessible
# View bot logs for errors
```

### yt-dlp errors
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Install ffmpeg
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

---

## Performance Notes

- ✅ Full async/await for responsive UI
- ✅ Database indices on user_id, track_id, searched_at for fast queries
- ✅ yt-dlp caches results for faster repeated searches
- ✅ Genius API optional (only for album art)
- ✅ Connection pooling with SQLAlchemy

---

## Security

- ✅ Environment variables for sensitive data
- ✅ No hardcoded API keys
- ✅ CORS enabled for local development
- ✅ Input validation with Pydantic
- ✅ SQL injection protection via SQLAlchemy ORM

---

## Roadmap

- [ ] Playlist support
- [ ] User preferences (favorite genres)
- [ ] Advanced search filters
- [ ] Music recommendations
- [ ] Offline cache
- [ ] Bot analytics dashboard

---

## License

MIT License - See LICENSE file for details

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## Support

For issues and questions:
- Check [SETUP_GUIDE.md](./SETUP_GUIDE.md) for setup help
- Review logs in console output
- Verify all services are running

**Built with ❤️ using FastAPI, aiogram, and PostgreSQL**
