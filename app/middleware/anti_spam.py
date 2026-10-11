import time
import asyncio
import logging
from typing import Dict, Tuple, Callable, Any
from functools import wraps
from pyrogram.errors import FloodWait

from app.config.settings import settings

logger = logging.getLogger("QinxiaoMusic.AntiSpam")

# Maintenance mode state
MAINTENANCE_MODE: bool = False

# Rate limiting storage: key -> timestamp
_rate_limits: Dict[str, float] = {}
_lock = asyncio.Lock()


def set_maintenance_mode(status: bool) -> None:
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = status


def is_maintenance_mode() -> bool:
    return MAINTENANCE_MODE


async def check_rate_limit(user_id: int, action_type: str = "command", limit_seconds: float = 1.5) -> Tuple[bool, float]:
    """Check if a user is rate limited for a specific action."""
    key = f"{user_id}:{action_type}"
    now = time.time()
    async with _lock:
        if len(_rate_limits) > 2000:
            cutoff = now - 60.0
            stale = [k for k, ts in _rate_limits.items() if ts < cutoff]
            for k in stale:
                _rate_limits.pop(k, None)

        last_time = _rate_limits.get(key, 0.0)
        elapsed = now - last_time
        if elapsed < limit_seconds:
            return True, limit_seconds - elapsed
        _rate_limits[key] = now
        return False, 0.0


def rate_limit(action_type: str = "command", limit_seconds: float = 1.5):
    """Decorator for Pyrogram handlers to enforce rate limits and handle FloodWait."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(client, message_or_query, *args, **kwargs):
            user = getattr(message_or_query, "from_user", None)
            user_id = user.id if user else 0
            logger.info(f"Incoming update: handler={func.__name__}, user={user_id}")

            # Maintenance mode check
            if MAINTENANCE_MODE and not (settings.OWNER_ID > 0 and user_id == settings.OWNER_ID):
                text = "⚠️ **Qinxiao Music** is currently under maintenance. Please try again later."
                if hasattr(message_or_query, "answer"):
                    await message_or_query.answer(text, show_alert=True)
                elif hasattr(message_or_query, "reply_text"):
                    await message_or_query.reply_text(text)
                return

            if user_id > 0:
                is_limited, wait_time = await check_rate_limit(user_id, action_type, limit_seconds)
                if is_limited:
                    text = f"⏱ Slow down! Please wait {wait_time:.1f}s before trying again."
                    if hasattr(message_or_query, "answer"):
                        await message_or_query.answer(text, show_alert=True)
                    elif hasattr(message_or_query, "reply_text"):
                        await message_or_query.reply_text(text)
                    return

            try:
                return await func(client, message_or_query, *args, **kwargs)
            except FloodWait as e:
                logger.warning(f"Telegram FloodWait encountered: waiting {e.value} seconds.")
                await asyncio.sleep(e.value + 1)
                return await func(client, message_or_query, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in handler {func.__name__}: {e}", exc_info=True)
                err_msg = "❌ An unexpected error occurred while processing your request. Please try again."
                if hasattr(message_or_query, "reply_text"):
                    await message_or_query.reply_text(err_msg)
                elif hasattr(message_or_query, "answer"):
                    await message_or_query.answer(err_msg, show_alert=True)

        return wrapper
    return decorator

