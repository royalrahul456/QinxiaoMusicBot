from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.player.queue_manager import queue_manager, LoopMode
from app.player.playback import playback_manager
from app.permissions.checker import is_admin
from app.database.session import get_session
from app.utils.formatting import format_duration, escape_markdown


async def _require_group_admin(client, message: Message) -> bool:
    if message.chat.id > 0:
        return True
    user = message.from_user
    async with get_session() as session:
        return await is_admin(client, message.chat.id, user.id if user else 0, session)


@rate_limit("command", 1.0)
async def queue_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)
    items = queue.get_queue_list()

    text = f"📋 **Qingxiao Music Queue (@QinxiaoMusicBot)**\n━━━━━━━━━━━━━━━━━━━━━━━\n"

    if queue.current_item:
        song = queue.current_item.song
        text += f"▶️ **Now Playing:** [{escape_markdown(song.title)}]({song.url}) (`{format_duration(song.duration)}`)\n"
        text += f"👤 **Requested by:** `{escape_markdown(queue.current_item.requested_by_name)}`\n━━━━━━━━━━━━━━━━━━━━━━━\n"

    if not items:
        text += "❌ Queue is currently empty."
    else:
        text += "📌 **Up Next:**\n"
        for idx, item in enumerate(items[:15], start=1):
            s = item.song
            text += f"`{idx}.` [{escape_markdown(s.title)}]({s.url}) | `{format_duration(s.duration)}` | `{escape_markdown(item.requested_by_name)}`\n"

        if len(items) > 15:
            text += f"\n*...and {len(items) - 15} more tracks in queue.*"

    await message.reply_text(text, disable_web_page_preview=True)


@rate_limit("command", 1.0)
async def nowplaying_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if not queue.current_item:
        return await message.reply_text("❌ Qingxiao Music is not currently playing anything.")

    await playback_manager.update_player_ui(chat_id)


@rate_limit("command", 1.0)
async def shuffle_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can shuffle the queue.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)
    shuffled = await queue.shuffle()

    if shuffled:
        await message.reply_text("🔀 **Qingxiao Queue has been shuffled!**")
    else:
        await message.reply_text("❌ Not enough items in queue to shuffle.")


@rate_limit("command", 1.0)
async def clear_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can clear the queue.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)
    count = await queue.clear()
    await message.reply_text(f"🗑 **Cleared {count} tracks from the Qingxiao queue.**")


@rate_limit("command", 1.0)
async def loop_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change loop mode.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if queue.loop_mode == LoopMode.TRACK:
        queue.loop_mode = LoopMode.OFF
        mode_str = "Off"
    else:
        queue.loop_mode = LoopMode.TRACK
        mode_str = "🔂 Track Loop Enabled"

    await playback_manager.update_player_ui(chat_id)
    await message.reply_text(f"🔁 **Loop Mode:** `{mode_str}`")


@rate_limit("command", 1.0)
async def loopqueue_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change loop mode.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if queue.loop_mode == LoopMode.QUEUE:
        queue.loop_mode = LoopMode.OFF
        mode_str = "Off"
    else:
        queue.loop_mode = LoopMode.QUEUE
        mode_str = "🔁 Queue Loop Enabled"

    await playback_manager.update_player_ui(chat_id)
    await message.reply_text(f"🔁 **Loop Mode:** `{mode_str}`")


@rate_limit("command", 1.0)
async def autoplay_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can toggle autoplay.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)
    queue.autoplay = not queue.autoplay
    status = "Enabled" if queue.autoplay else "Disabled"
    await message.reply_text(f"📻 **Qingxiao Autoplay:** `{status}`")

