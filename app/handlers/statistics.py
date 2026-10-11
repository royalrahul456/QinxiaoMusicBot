from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.statistics.tracker import stats_tracker
from app.database.session import get_session
from app.repositories.song_repo import SongRepository
from app.repositories.stats_repo import StatsRepository
from app.repositories.user_repo import UserRepository
from app.utils.formatting import format_duration
from app.utils.time import format_uptime


@rate_limit("command", 1.0)
async def top_command(client, message: Message):
    async with get_session() as session:
        top_songs, top_artists = await stats_tracker.get_bot_leaderboards(session)

    text = f"📊 **Qinxiao Music Top Charts**\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "🎵 **Most Played Songs:**\n"
    for idx, s in enumerate(top_songs[:5], start=1):
        text += f"`{idx}.` [{s.title}]({s.url}) - `{s.artist}` (`{s.play_count}` plays)\n"

    text += "\n🎙 **Top Artists:**\n"
    for idx, (artist, count) in enumerate(top_artists[:5], start=1):
        text += f"`{idx}.` `{artist}` (`{count}` plays)\n"

    await message.reply_text(text, disable_web_page_preview=True)


@rate_limit("command", 1.0)
async def topsongs_command(client, message: Message):
    async with get_session() as session:
        song_repo = SongRepository(session)
        top_songs = await song_repo.get_top_songs(limit=10)

    if not top_songs:
        return await message.reply_text("📊 No track playback statistics recorded yet.")

    text = "🎵 **Qinxiao Music Most Played Tracks**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, s in enumerate(top_songs, start=1):
        text += f"`{idx}.` [{s.title}]({s.url}) - `{s.artist}` (`{s.play_count}` plays)\n"

    await message.reply_text(text, disable_web_page_preview=True)


@rate_limit("command", 1.0)
async def topartists_command(client, message: Message):
    async with get_session() as session:
        song_repo = SongRepository(session)
        top_artists = await song_repo.get_top_artists(limit=10)

    if not top_artists:
        return await message.reply_text("📊 No artist statistics recorded yet.")

    text = "🎙 **Qinxiao Music Most Played Artists**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (artist, count) in enumerate(top_artists, start=1):
        text += f"`{idx}.` `{artist}` (`{count}` total plays)\n"

    await message.reply_text(text)


@rate_limit("command", 1.0)
async def groupstats_command(client, message: Message):
    chat_id = message.chat.id
    async with get_session() as session:
        stats_repo = StatsRepository(session)
        grp_stats = await stats_repo.get_group_stats(chat_id)

    if not grp_stats:
        return await message.reply_text("📊 No listening statistics recorded for this group yet.")

    text = (
        f"📊 **Group Listening Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎵 **Total Plays:** `{grp_stats.total_plays}`\n"
        f"⏭ **Total Skips:** `{grp_stats.total_skips}`\n"
        f"⏱ **Total Listening Time:** `{format_uptime(grp_stats.total_time_seconds)}`"
    )
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def listeningtime_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        usr = await user_repo.get_or_create(user.id)

    uptime_str = format_uptime(int(usr.total_listening_time))
    await message.reply_text(f"⏱ **Your Total Qinxiao Listening Time:** `{uptime_str}` ({usr.total_play_count} tracks played)")
