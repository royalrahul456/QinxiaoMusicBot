import html
from typing import Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.config.settings import settings
from app.player.queue_manager import GroupQueue, QueueItem
from app.utils.formatting import format_duration


def build_player_text(queue: GroupQueue, is_paused: bool = False, current_time: int = 0) -> str:
    """Build compact, elegant HTML player text matching Image 2 layout."""
    item: Optional[QueueItem] = queue.current_item

    if not item:
        return (
            "| <u>Stream ended</u>\n\n"
            f"<b>{settings.BOT_NAME}</b> queue is empty.\n"
            "Use <code>/play &lt;song&gt;</code> to start listening!"
        )

    song = item.song
    header = "| <u>Stream paused</u>" if is_paused else "| <u>Started streaming</u>"

    m, s = divmod(song.duration, 60)
    h, m = divmod(m, 60)
    if h > 0:
        dur_str = f"{h}:{m:02d}:{s:02d} hr"
    elif song.duration > 0:
        dur_str = f"{m}:{s:02d} min"
    else:
        dur_str = "Live min"

    title_escaped = html.escape(song.title)
    requester_escaped = html.escape(item.requested_by_name or "User")

    text = (
        f"{header}\n\n"
        f"<b>Title:</b> <a href=\"{song.url}\">{title_escaped}</a>\n\n"
        f"<b>Duration:</b> {dur_str}\n"
        f"<b>Requested by:</b> {requester_escaped}"
    )
    return text


def build_player_keyboard(queue: GroupQueue, is_paused: bool = False) -> InlineKeyboardMarkup:
    """Build minimalist inline playback control buttons matching Image 2."""
    play_pause_btn = InlineKeyboardButton(
        "▷" if is_paused else "II",
        callback_data="cb_player_resume" if is_paused else "cb_player_pause"
    )

    bot_username = settings.BOT_USERNAME.replace("@", "")
    add_group_url = f"https://t.me/{bot_username}?startgroup=true"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▸▸I", callback_data="cb_player_skip"),
            InlineKeyboardButton("◽", callback_data="cb_player_stop"),
            play_pause_btn,
        ],
        [
            InlineKeyboardButton("➕", url=add_group_url),
            InlineKeyboardButton("Close", callback_data="cb_player_close"),
        ]
    ])
    return keyboard
