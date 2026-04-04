"""
Telegram bot main entry point
"""

import asyncio
import logging
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def set_default_commands(bot: Bot):
    """Set default bot commands"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="top", description="View top charts"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Start the bot"""
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    bot = Bot(token=settings.telegram_bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Set default commands
    await set_default_commands(bot)
    
    # Import and register routers
    from handlers import commands, search
    
    dp.include_router(commands.router)
    dp.include_router(search.router)
    
    logger.info(f"Bot started. Backend URL: {settings.backend_url}")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
