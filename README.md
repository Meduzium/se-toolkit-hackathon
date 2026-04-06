# Telegram Music Bot

Telegram bot for searching and downloading music from YouTube with trending charts

## Demo

![Bot Search Example](https://via.placeholder.com/800x400.png?text=Search+and+Download+Music)

*Send a song name to the bot → Select from YouTube results → Receive MP3 file*

![Top Charts](https://via.placeholder.com/800x400.png?text=Top+Charts+View)

*View daily, weekly, and monthly trending tracks with user attribution*

## Product Context

**End Users:** Music enthusiasts and Telegram users who want quick access to music downloads

**Problem:** Finding and downloading music from YouTube is cumbersome - requires switching between apps, using web downloaders, or installing separate software

**Solution:** An all-in-one Telegram bot that allows users to search YouTube, download music as MP3, and discover trending tracks directly in Telegram messenger

## Features

### Implemented
✅ YouTube music search via yt-dlp  
✅ MP3 download and delivery to Telegram  
✅ Trending charts (daily, weekly, monthly)  
✅ User attribution for searches  
✅ PostgreSQL database for tracking  
✅ Full async/await architecture  
✅ Docker deployment  

### Not Yet Implemented
⬜ Playlist support  
⬜ User preferences and favorites  
⬜ Advanced search filters  
⬜ Music recommendations  
⬜ Offline cache  

## Usage

1. Start the bot: `/start`
2. Send any song name (e.g., "Bohemian Rhapsody")
3. Select from search results
4. Receive MP3 file in chat
5. Use `/top` to view trending tracks
6. Use `/help` to see all commands

## Deployment

### Requirements

**VM Operating System:** Ubuntu 24.04

**Required Software:**
- Docker (24.0+)
- Docker Compose (2.0+)

### Installation Steps

**1. Install Docker and Docker Compose**

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**2. Clone or Upload Project**

```bash
# If using git
git clone <your-repository-url>
cd se-toolkit-hackathon-master

# Or upload project files to the VM
```

**3. Configure Environment Variables**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
nano .env
```

Set the following variables in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GENIUS_API_KEY=your_genius_api_key_here  # Optional
```

**How to get Telegram Bot Token:**
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token provided

**4. Start the Application**

```bash
# Build and start all services
docker compose up -d --build

# Verify all containers are running
docker compose ps

# Check logs
docker compose logs -f
```

**5. Verify Deployment**

```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
docker compose exec postgres pg_isready -U user -d music_bot_db

# Check bot logs
docker compose logs bot
```

**6. Stop the Application**

```bash
# Stop all services
docker compose down

# Stop and remove all data
docker compose down -v
```

### Troubleshooting

**Bot not responding:**
- Verify TELEGRAM_BOT_TOKEN is correct in `.env`
- Check bot logs: `docker compose logs bot`
- Ensure backend is running: `docker compose ps`

**Backend errors:**
- Check backend logs: `docker compose logs backend`
- Verify database is healthy: `docker compose ps postgres`

**Database connection issues:**
- Wait for PostgreSQL healthcheck to pass (may take 30-60 seconds)
- Check: `docker compose logs postgres`

**Port conflicts:**
- PostgreSQL runs on port 5433 (mapped from internal 5432)
- Backend API runs on port 8000
- If these ports are in use, modify `docker-compose.yml` ports section
