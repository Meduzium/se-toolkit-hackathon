"""
Search handler for music queries
"""

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
import logging

logger = logging.getLogger(__name__)

router = Router()

# Store search results temporarily
_search_results = {}

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
    
    # Show loading message
    status_msg = await message.answer("🔍 Searching...")
    
    try:
        backend_url = "http://localhost:8000"  # Will be set from config
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{backend_url}/api/search", params={"q": query})
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
