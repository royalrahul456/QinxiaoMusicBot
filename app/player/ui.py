from typing import Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.player.queue_manager import GroupQueue, QueueItem, LoopMode
from app.utils.formatting import format_duration, build_progress_bar, escape_markdown


def build_player_text(queue: GroupQueue, is_paused: bool = False, current_time: int = 0) -> str:
    """Build formatted player markup text for Qinxiao Music."""
    item: Optional[QueueItem] = queue.current_item

    if not item:
        return (
            "🎵 **Qinxiao Music Player** (@QinxiaoMusicBot)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌ Nothing is currently playing in this chat.\n"
            "Use `/play <song name or link>` to start playback!"
        )

    song = item.song
    progress = build_progress_bar(current_time, song.duration) if song.duration > 0 else "🔴 LIVE"
    status_icon = "⏸ Paused" if is_paused else "▶️ Playing"

    loop_icon = {
        LoopMode.OFF: "Off",
        LoopMode.TRACK: "🔂 Track",
        LoopMode.QUEUE: "🔁 Queue"
    }.get(queue.loop_mode, "Off")

    queue_count = len(queue.items)

    text = (
        f"🎵 **Qinxiao Music Player** (@QinxiaoMusicBot)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **Title:** [{escape_markdown(song.title)}]({song.url})\n"
        f"🎙 **Artist:** `{escape_markdown(song.artist)}`\n"
        f"👤 **Requested by:** `{escape_markdown(item.requested_by_name)}`\n"
        f"🎧 **Source:** `{song.source.title()}` | **Quality:** `{queue.bitrate}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔊 **Volume:** `{queue.volume}%` | 🎛 **EQ:** `{queue.equalizer.title()}`\n"
        f"🔁 **Loop:** `{loop_icon}` | 📋 **In Queue:** `{queue_count}` tracks\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} | {progress}\n"
    )

    return text


def build_player_keyboard(queue: GroupQueue, is_paused: bool = False) -> InlineKeyboardMarkup:
    """Build interactive inline keyboard buttons for player."""
    play_pause_btn = InlineKeyboardButton(
        "▶️ Resume" if is_paused else "⏸ Pause",
        callback_data="cb_player_resume" if is_paused else "cb_player_pause"
    )

    loop_label = {
        LoopMode.OFF: "🔁 Loop: Off",
        LoopMode.TRACK: "🔂 Loop: Track",
        LoopMode.QUEUE: "🔁 Loop: Queue"
    }.get(queue.loop_mode, "🔁 Loop")

    keyboard = InlineKeyboardMarkup([
        [
            play_pause_btn,
            InlineKeyboardButton("⏭ Skip", callback_data="cb_player_skip"),
            InlineKeyboardButton("🔄 Replay", callback_data="cb_player_replay"),
            InlineKeyboardButton("⏹ Stop", callback_data="cb_player_stop"),
        ],
        [
            InlineKeyboardButton("🔀 Shuffle", callback_data="cb_player_shuffle"),
            InlineKeyboardButton(loop_label, callback_data="cb_player_loop"),
            InlineKeyboardButton("🔉 Vol-", callback_data="cb_player_voldown"),
            InlineKeyboardButton("🔊 Vol+", callback_data="cb_player_volup"),
        ],
        [
            InlineKeyboardButton("🔇 Mute" if queue.volume > 0 else "🔊 Unmute", callback_data="cb_player_mute"),
            InlineKeyboardButton("📋 Queue", callback_data="cb_player_queue"),
            InlineKeyboardButton("❤️ Favorite", callback_data="cb_player_fav"),
            InlineKeyboardButton("🎵 Lyrics", callback_data="cb_player_lyrics"),
        ],
        [
            InlineKeyboardButton("🎛 Equalizer", callback_data="cb_player_eq"),
            InlineKeyboardButton("⚡ Bass", callback_data="cb_player_bass"),
            InlineKeyboardButton("🌐 Quality", callback_data="cb_player_quality"),
            InlineKeyboardButton("❌ Close", callback_data="cb_player_close"),
        ]
    ])

    return keyboard
