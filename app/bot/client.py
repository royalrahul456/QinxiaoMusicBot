import logging
from typing import Optional
from pyrogram import Client
from app.config.settings import settings

logger = logging.getLogger("QinxiaoMusic.Bot")


def create_bot_client() -> Client:
    """Create Pyrogram Client for Qinxiao Music (@QinxiaoMusicBot)."""
    bot = Client(
        name="QinxiaoMusicBot",
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        bot_token=settings.BOT_TOKEN,
        in_memory=False,
    )
    logger.info(f"Pyrogram client created for {settings.BOT_NAME} ({settings.BOT_USERNAME}).")
    return bot


def create_assistant_client() -> Optional[Client]:
    """Create Pyrogram Assistant User Client for Voice Chat streaming."""
    if not settings.ASSISTANT_SESSION:
        logger.info("ASSISTANT_SESSION not configured. Assistant client skipped.")
        return None

    try:
        user_bot = Client(
            name="QinxiaoAssistant",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            session_string=settings.ASSISTANT_SESSION,
            in_memory=True,
        )
        logger.info("Pyrogram Assistant User Client created successfully.")
        return user_bot
    except Exception as e:
        logger.error(f"Failed to create Assistant User Client: {e}")
        return None
