from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.player.queue_manager import queue_manager
from app.database.session import get_session
from app.repositories.favorite_repo import FavoriteRepository
from app.utils.formatting import format_duration


@rate_limit("command", 1.0)
async def fav_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    queue = await queue_manager.get_queue(chat_id)
    if not queue.current_item:
        return await message.reply_text("❌ Nothing is currently playing to add to favorites!")

    song = queue.current_item.song
    async with get_session() as session:
        repo = FavoriteRepository(session)
        _, created = await repo.add_favorite(
            user_id=user.id,
            song_id=song.song_id,
            title=song.title,
            artist=song.artist,
            duration=song.duration,
            url=song.url,
            thumbnail=song.thumbnail,
            source=song.source
        )

    if created:
        await message.reply_text(f"❤️ **Added to your Qinxiao Favorites:** [{song.title}]({song.url})")
    else:
        await message.reply_text(f"ℹ️ [{song.title}]({song.url}) is already in your favorites.")


@rate_limit("command", 1.0)
async def unfav_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    queue = await queue_manager.get_queue(chat_id)
    if not queue.current_item:
        return await message.reply_text("❌ Nothing is currently playing to remove from favorites!")

    song = queue.current_item.song
    async with get_session() as session:
        repo = FavoriteRepository(session)
        removed = await repo.remove_favorite(user.id, song.song_id)

    if removed:
        await message.reply_text(f"💔 **Removed from your Qinxiao Favorites:** `{song.title}`")
    else:
        await message.reply_text(f"❌ `{song.title}` was not found in your favorites.")


@rate_limit("command", 1.0)
async def favorites_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        repo = FavoriteRepository(session)
        favs = await repo.get_favorites(user.id, limit=20)

    if not favs:
        return await message.reply_text("💔 You have no saved favorites yet. Use `/fav` while playing a song!")

    text = f"❤️ **Your Qinxiao Favorite Tracks ({len(favs)})**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, f in enumerate(favs, start=1):
        text += f"`{idx}.` [{f.title}]({f.url}) - `{f.artist}` (`{format_duration(f.duration)}`)\n"

    await message.reply_text(text, disable_web_page_preview=True)
