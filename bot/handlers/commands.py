"""
Command handlers for /start, /help, /top, /lyrics, /cover
"""

from aiogram import Router, types
from aiogram.filters import Command
import httpx
import logging
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

logger = logging.getLogger(__name__)
router = Router()


def _split_text(text: str, chunk_size: int = 3900):
    chunks = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > chunk_size:
            if current:
                chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks


def _parse_track_query(raw_query: str) -> tuple[str, str]:
    """Parse '/lyrics' input into (title, artist)."""
    query = raw_query.strip().strip('"').strip("'")
    if not query:
        return "", "Unknown"

    # Support common forms: "Artist - Title" and "Artist – Title".
    parts = re.split(r"\s[-\u2013]\s", query, maxsplit=1)
    if len(parts) == 2:
        artist, title = parts[0].strip(), parts[1].strip()
        if title:
            return title, artist or "Unknown"

    # Fallback: pass whole query as title; backend matching handles variants.
    return query, "Unknown"

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
        f"/lyrics <artist name - track name> - Find lyrics via Genius\n"
        f"/cover <artist name - track name> - Get track cover via Genius\n"
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
        "/help - Show this message\n\n"
        "/lyrics <artist name - track name> - Get song lyrics via Genius\n"
        "/cover <artist name - track name> - Get song/album cover via Genius\n\n"
        "Examples:\n"
        "/lyrics ATL - Унисон\n\n"
        "/cover LAZZY2WICE - Tagilla\n"
        
    )
    await message.answer(help_text)


@router.message(Command("lyrics"))
async def cmd_lyrics(message: types.Message):
    """Handle /lyrics command to fetch lyrics without downloading."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage:\n"
            "/lyrics Lil Wayne - A Milli"
        )
        return

    title, artist = _parse_track_query(args[1])
    if not title:
        await message.answer("Please provide a track name.")
        return

    status_msg = await message.answer("🔎 Searching lyrics...")
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.get(
                f"{settings.backend_url}/api/lyrics",
                params={"title": title, "artist": artist},
            )

        if response.status_code != 200:
            await status_msg.edit_text("❌ Could not fetch lyrics now. Try again later.")
            return

        data = response.json()
        lyrics = data.get("lyrics")
        found = data.get("found")
        resolved_title = data.get("title", title)
        resolved_artist = data.get("artist", artist)

        if not found or not lyrics:
            await status_msg.edit_text(f"❌ Lyrics not found for: {resolved_title} - {resolved_artist}")
            return

        chunks = _split_text(lyrics)
        if not chunks:
            await status_msg.edit_text("❌ Lyrics are empty.")
            return

        chunks[0] = f"📝 Lyrics: {resolved_title} - {resolved_artist}\n\n{chunks[0]}"
        await status_msg.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.answer(chunk)

    except httpx.ConnectError:
        await status_msg.edit_text("❌ Backend not available. Please try again later.")
    except Exception as e:
        logger.error(f"Lyrics command error: {e}")
        await status_msg.edit_text("❌ Error fetching lyrics. Please try again.")


@router.message(Command("cover"))
async def cmd_cover(message: types.Message):
    """Handle /cover command to fetch track/album cover without downloading."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage:\n"
            "/cover A Milli\n"
            "/cover Lil Wayne - A Milli"
        )
        return

    title, artist = _parse_track_query(args[1])
    if not title:
        await message.answer("Please provide a track name.")
        return

    status_msg = await message.answer("🖼 Searching cover...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{settings.backend_url}/api/cover",
                params={"title": title, "artist": artist},
            )

        if response.status_code != 200:
            await status_msg.edit_text("❌ Could not fetch cover now. Try again later.")
            return

        data = response.json()
        cover_url = data.get("cover_url")
        found = data.get("found")
        resolved_title = data.get("title", title)
        resolved_artist = data.get("artist", artist)

        if not found or not cover_url:
            await status_msg.edit_text(f"❌ Cover not found for: {resolved_title} - {resolved_artist}")
            return

        await message.answer_photo(
            photo=cover_url,
            caption=f"🖼 Cover: {resolved_title} - {resolved_artist}",
        )
        await status_msg.delete()

    except httpx.ConnectError:
        await status_msg.edit_text("❌ Backend not available. Please try again later.")
    except Exception as e:
        logger.error(f"Cover command error: {e}")
        await status_msg.edit_text("❌ Error fetching cover. Please try again.")

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
            title = entry.get("title", "Unknown")
            artist = entry.get("artist", "Unknown")
            count = entry.get("count", 0)
            text += f"{i}. {title} by {artist} ({count})\n"
        
        await message.answer(text)
    
    except httpx.ConnectError:
        await message.answer("❌ Backend not available. Please try again later.")
    except Exception as e:
        logger.error(f"Charts error: {e}")
        await message.answer("❌ Error fetching charts. Please try again.")
