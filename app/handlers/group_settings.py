from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.player.vc_client import vc_client
from app.player.queue_manager import queue_manager
from app.player.playback import playback_manager
from app.permissions.checker import is_admin
from app.database.session import get_session
from app.repositories.chat_repo import ChatRepository


@rate_limit("command", 1.0)
async def join_command(client, message: Message):
    chat_id = message.chat.id
    if vc_client.is_connected(chat_id):
        return await message.reply_text("ℹ️ Qinxiao Music is already connected to this voice chat.")

    queue = await queue_manager.get_queue(chat_id)
    # Join with dummy silence or ready state
    success = await vc_client.join_and_play(
        chat_id=chat_id,
        stream_url="http://stream.zeno.fm/f3wvbbqmdg8uv",  # Silence/fallback stream or init stream
        volume=queue.volume,
        bitrate=queue.bitrate
    )
    if success:
        await message.reply_text("🔌 **Qinxiao Music successfully joined the voice chat!**")
    else:
        await message.reply_text("❌ Failed to join voice chat. Make sure voice chat is active and Qinxiao Music has admin permissions!")


@rate_limit("command", 1.0)
async def leave_command(client, message: Message):
    chat_id = message.chat.id
    if not vc_client.is_connected(chat_id):
        return await message.reply_text("ℹ️ Qinxiao Music is not in the voice chat.")

    user = message.from_user
    if chat_id < 0:
        async with get_session() as session:
            if not await is_admin(client, chat_id, user.id if user else 0, session):
                return await message.reply_text("❌ Only group administrators can make the bot leave the voice chat.")

    await playback_manager.stop(chat_id)
    await message.reply_text("👋 **Qinxiao Music left the voice chat.**")


@rate_limit("command", 1.0)
async def vc_command(client, message: Message):
    chat_id = message.chat.id
    connected = vc_client.is_connected(chat_id)
    queue = await queue_manager.get_queue(chat_id)

    status = "🟢 Connected & Active" if connected else "🔴 Disconnected"
    playing = queue.current_item.song.title if (queue.current_item and connected) else "Nothing"

    text = (
        f"🎙 **Qinxiao Voice Chat Status**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Status: `{status}`\n"
        f"Now Playing: `{playing}`\n"
        f"Volume: `{queue.volume}%` | Bitrate: `{queue.bitrate}`"
    )
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def player_command(client, message: Message):
    chat_id = message.chat.id
    await playback_manager.update_player_ui(chat_id)


@rate_limit("command", 1.0)
async def toggle_247_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_admin(client, chat_id, user.id, session):
            return await message.reply_text("❌ Only group administrators can toggle 24/7 mode.")

        chat_repo = ChatRepository(session)
        chat_db = await chat_repo.get_or_create(chat_id)
        new_val = not chat_db.is_247
        await chat_repo.update_settings(chat_id, is_247=new_val)

    status = "Enabled 🔄 (Bot will stay in VC 24/7)" if new_val else "Disabled 🛑"
    await message.reply_text(f"🔁 **24/7 Mode:** `{status}`")


@rate_limit("command", 1.0)
async def autoleave_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_admin(client, chat_id, user.id, session):
            return await message.reply_text("❌ Only group administrators can configure auto-leave.")

        chat_repo = ChatRepository(session)
        chat_db = await chat_repo.get_or_create(chat_id)
        new_val = not chat_db.autoleave
        await chat_repo.update_settings(chat_id, autoleave=new_val)

    status = "Enabled (Auto-leaves when empty)" if new_val else "Disabled"
    await message.reply_text(f"🚪 **Auto Leave:** `{status}`")
