import asyncio
import logging
import sys

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from app.config.settings import settings
from app.database.session import init_db
from app.cache.redis_cache import cache
from app.bot.instance import bot, assistant
from app.bot.poller import bot_poller
from app.player.vc_client import vc_client
from app.player.playback import playback_manager

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("QinxiaoMusic.Main")


async def main():
    logger.info("==========================================")
    logger.info(f" Starting {settings.BOT_NAME} ({settings.BOT_USERNAME}) ")
    logger.info("==========================================")

    # 1. Initialize Database Tables & Cache
    logger.info("Initializing database tables...")
    await init_db()

    logger.info("Initializing cache manager...")
    await cache.init_cache()

    # 2. Initialize PyTgCalls Client & Playback Manager
    logger.info("Initializing VoiceChatClient & PlaybackManager...")
    vc_client.init_app(bot, assistant)
    playback_manager.init_bot(bot)

    if not settings.BOT_TOKEN or settings.BOT_TOKEN.startswith("123456:"):
        logger.error("Valid BOT_TOKEN is missing! Please configure BOT_TOKEN in your .env or environment variables.")
        return

    # 3. Start HTTP Bot API Poller (guarantees instant command & callback responses using BOT_TOKEN)
    logger.info("Starting HTTP Bot API Poller...")
    poller_task = asyncio.create_task(bot_poller.start())

    # 4. Start Pyrogram MTProto Client & Assistant (only if API_ID and API_HASH are configured)
    mtproto_started = False
    if settings.API_ID and settings.API_HASH:
        logger.info("Starting Telegram Pyrogram MTProto client...")
        try:
            from pyrogram.handlers import InlineQueryHandler
            from app.handlers.inline import inline_search_handler
            bot.add_handler(InlineQueryHandler(inline_search_handler))
            await bot.start()
            mtproto_started = True
            if assistant:
                logger.info("Starting Assistant User Client...")
                await assistant.start()
                await vc_client.start()
        except Exception as e:
            logger.warning(f"Pyrogram MTProto start notice ({e}). HTTP Bot Poller is active and handling commands.")
    else:
        logger.warning("API_ID / API_HASH not set. Running in HTTP Bot API Poller mode.")

    logger.info("==========================================")
    logger.info(f" {settings.BOT_NAME} ({settings.BOT_USERNAME}) is now ONLINE! ")
    logger.info("==========================================")

    # Keep bot running continuously
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"Shutting down {settings.BOT_NAME} Bot...")
    finally:
        await bot_poller.stop()
        poller_task.cancel()
        if assistant and getattr(assistant, "is_connected", False):
            await assistant.stop()
        if mtproto_started and getattr(bot, "is_connected", False):
            await bot.stop()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
