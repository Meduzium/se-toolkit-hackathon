"""
Search handler for music queries
"""

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

router = Router()

# Store search results temporarily
_search_results = {}

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@router.message(F.text)
async def handle_search(message: types.Message):
    """Handle text search queries"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("Please provide at least 2 characters to search.")
        return
    
    # Skip if command
    if query.startswith('/'):
        return
    
    # Show loading message with retry logic
    max_retries = 3
    status_msg = None
    
    for attempt in range(max_retries):
        try:
            status_msg = await message.answer("🔍 Searching...")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to send message after {max_retries} attempts: {e}")
                return
            await asyncio.sleep(1)
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(f"{BACKEND_URL}/api/search", params={"q": query})
            data = response.json()
        
        results = data.get("results", [])
        
        if not results:
            await status_msg.edit_text("No results found. Try another search.")
            return
        
        # Store results for callback handling
        _search_results[message.from_user.id] = results
        
        # Build inline keyboard with results
        buttons = []
        for i, result in enumerate(results[:8]):
            title = result["title"][:40]
            btn_text = f"{i+1}. {title}"
            callback_data = f"download_{i}"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=callback_data)])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        text = "🎵 Found these tracks:\n\n"
        for i, result in enumerate(results[:8], 1):
            artist = result.get("artist", "Unknown")
            text += f"{i}. {result['title']} - {artist}\n"
        
        await status_msg.edit_text(text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        await status_msg.edit_text("Error searching. Please try again.")

@router.callback_query(F.data.startswith("download_"))
async def handle_download(callback: types.CallbackQuery):
    """Handle download button clicks"""
    try:
        await callback.answer()
        
        # Get result index from callback data
        index = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        # Get stored search results
        if user_id not in _search_results:
            await callback.message.edit_text("Search expired. Please search again.")
            return
        
        results = _search_results[user_id]
        if index >= len(results):
            await callback.message.edit_text("Invalid selection.")
            return
        
        track = results[index]
        title = track["title"]
        youtube_url = track["youtube_url"]
        artist = track.get("artist", "Unknown")
        
        # Update message to show downloading status
        await callback.message.edit_text(f"⬇️ Downloading: {title}...")
        
        # Request download from backend with user tracking
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/download",
                params={
                    "title": title, 
                    "youtube_url": youtube_url,
                    "telegram_id": callback.from_user.id,
                    "username": callback.from_user.username or callback.from_user.first_name,
                    "artist": artist
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                file_path = data.get("file_path")
                
                # Send the audio file
                await callback.message.answer_audio(
                    audio=types.FSInputFile(file_path),
                    title=title,
                    performer=track.get("artist", "Unknown")
                )
                await callback.message.edit_text(f"✅ Downloaded: {title}")
            else:
                detail = "Download failed"
                try:
                    detail = response.json().get("detail", detail)
                except Exception:
                    pass
                await callback.message.edit_text(f"❌ {detail}")
    
    except asyncio.TimeoutError:
        await callback.message.edit_text("⏱️ Download timeout. Try a shorter video.")
    except Exception as e:
        logger.error(f"Download error: {e}")
        await callback.message.edit_text("❌ Download error. Please try again.")
