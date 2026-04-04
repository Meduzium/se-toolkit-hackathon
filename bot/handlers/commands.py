"""
Command handlers for /start, /help, /top
"""

from aiogram import Router, types
from aiogram.filters import Command
import httpx
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user_first_name = message.from_user.first_name or "User"
    await message.answer(
        f"🎵 Welcome {user_first_name}!\n\n"
        f"I can help you search and download music from YouTube.\n\n"
        f"Just send me a song name to search!\n\n"
        f"Commands:\n"
        f"/start - Welcome message\n"
        f"/top - View top charts\n"
        f"/help - Show help"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_text = (
        "🎵 Music Bot Help\n\n"
        "Send me a song name to search for it.\n"
        "I'll show you matching results with an inline keyboard.\n"
        "Click on a track to download it as an MP3.\n\n"
        "Commands:\n"
        "/start - Show welcome message\n"
        "/top [period] - View top charts (day/week/month)\n"
        "/help - Show this message"
    )
    await message.answer(help_text)

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    """Handle /top command to show charts"""
    period = "day"
    args = message.text.split()
    if len(args) > 1 and args[1] in ["day", "week", "month"]:
        period = args[1]
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.backend_url}/api/charts",
                params={"period": period}
            )
            data = response.json()
        
        if not data.get("entries"):
            await message.answer("No charts data yet. Start searching to see trending tracks!")
            return
        
        text = f"📊 Top Tracks ({period.upper()})\n\n"
        for i, entry in enumerate(data["entries"][:10], 1):
            username = entry.get("username", "Anonymous")
            title = entry.get("title", "Unknown")
            artist = entry.get("artist", "Unknown")
            count = entry.get("count", 0)
            text += f"{i}. @{username} - {title} by {artist} ({count})\n"
        
        await message.answer(text)
    
    except httpx.ConnectError:
        await message.answer("❌ Backend not available. Please try again later.")
    except Exception as e:
        logger.error(f"Charts error: {e}")
        await message.answer("❌ Error fetching charts. Please try again.")
