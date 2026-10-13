from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.player.queue_manager import queue_manager
from app.lyrics.provider import lyrics_provider


@rate_limit("search", 2.0)
async def lyrics_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    title = None
    artist = None

    if len(message.command) > 1:
        query = " ".join(message.command[1:])
        if "-" in query:
            parts = query.split("-", 1)
            artist, title = parts[0].strip(), parts[1].strip()
        else:
            title = query.strip()
    elif queue.current_item:
        song = queue.current_item.song
        title = song.title
        artist = song.artist

    if not title:
        return await message.reply_text("❌ Please specify a song title or play a song first!\nExample: `/lyrics Alan Walker - Faded`")

    status_msg = await message.reply_text(f"🔍 **Qingxiao Music** is fetching lyrics for `{artist + ' - ' if artist else ''}{title}`...")
    res = await lyrics_provider.fetch_lyrics(title, artist)

    if not res or not res.plain_lyrics:
        return await status_msg.edit_text(f"❌ Lyrics not found for `{title}`.")

    lyrics_text = res.plain_lyrics
    if len(lyrics_text) > 4000:
        lyrics_text = lyrics_text[:3990] + "\n\n*(Truncated due to length)*"

    text = (
        f"🎵 **Lyrics: {res.title}** by `{res.artist}`\n"
        f"🎙 **Source:** `{res.source}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{lyrics_text}"
    )
    await status_msg.edit_text(text)


@rate_limit("search", 2.0)
async def syncedlyrics_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if not queue.current_item:
        return await message.reply_text("❌ Play a song first to view synced lyrics!")

    song = queue.current_item.song
    res = await lyrics_provider.fetch_lyrics(song.title, song.artist)

    if not res or not res.synced_lines:
        return await message.reply_text(f"⚠️ Synchronized LRC lyrics not available for `{song.title}`. Showing plain lyrics:\n\n/lyrics")

    formatted_lines = [f"`[{l.timestamp_ms // 1000}s]` {l.text}" for l in res.synced_lines[:25]]
    text = (
        f"⏱ **Synced Lyrics: {res.title}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n".join(formatted_lines)
    )
    await message.reply_text(text)
