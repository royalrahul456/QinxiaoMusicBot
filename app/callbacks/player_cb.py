import logging
from pyrogram.types import CallbackQuery

from app.middleware.anti_spam import rate_limit
from app.player.queue_manager import queue_manager, LoopMode
from app.player.playback import playback_manager
from app.player.vc_client import vc_client
from app.player.vote_skip import vote_skip_tracker
from app.permissions.checker import is_admin
from app.database.session import get_session
from app.repositories.chat_repo import ChatRepository
from app.repositories.favorite_repo import FavoriteRepository
from app.lyrics.provider import lyrics_provider
from app.audio.quality import EQUALIZER_PRESETS, QUALITY_PROFILES
from app.utils.formatting import format_duration, escape_markdown

logger = logging.getLogger("QinxiaoMusic.Callbacks.Player")

ADMIN_PROTECTED_CALLBACKS = {
    "cb_player_pause",
    "cb_player_resume",
    "cb_player_replay",
    "cb_player_stop",
    "cb_player_shuffle",
    "cb_player_loop",
    "cb_player_volup",
    "cb_player_voldown",
    "cb_player_mute",
    "cb_player_eq",
    "cb_player_bass",
    "cb_player_quality",
    "cb_player_close",
}


@rate_limit("callback", 0.5)
async def player_callback_handler(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    user = query.from_user
    user_id = user.id if user else 0
    data = query.data

    queue = await queue_manager.get_queue(chat_id)

    # Authorization check for state-modifying player callbacks in group chats
    if chat_id < 0 and data in ADMIN_PROTECTED_CALLBACKS:
        is_requester = (
            data in ("cb_player_pause", "cb_player_resume", "cb_player_replay")
            and queue.current_item is not None
            and queue.current_item.requested_by_id == user_id
            and user_id > 0
        )
        if not is_requester:
            async with get_session() as session:
                if not await is_admin(client, chat_id, user_id, session):
                    return await query.answer("❌ Only group administrators can use this control.", show_alert=True)

    if data == "cb_player_pause":
        if vc_client.is_connected(chat_id):
            await vc_client.pause(chat_id)
            await playback_manager.update_player_ui(chat_id, is_paused=True)
            await query.answer("⏸ Paused Qinxiao playback.")
        else:
            await query.answer("❌ Qinxiao is not active in voice chat.", show_alert=True)

    elif data == "cb_player_resume":
        if vc_client.is_connected(chat_id):
            await vc_client.resume(chat_id)
            await playback_manager.update_player_ui(chat_id, is_paused=False)
            await query.answer("▶️ Resumed Qinxiao playback.")
        else:
            await query.answer("❌ Qinxiao is not active in voice chat.", show_alert=True)

    elif data == "cb_player_skip":
        if not vc_client.is_connected(chat_id):
            return await query.answer("❌ Qinxiao is not active in voice chat.", show_alert=True)

        async with get_session() as session:
            chat_repo = ChatRepository(session)
            chat_db = await chat_repo.get_or_create(chat_id)
            user_is_admin = await is_admin(client, chat_id, user_id, session)

        if user_is_admin or chat_id > 0:
            await query.answer("⏭ Skipping track (Admin)...")
            await playback_manager.play_next(chat_id)
            return

        passed, current_votes, needed_votes = await vote_skip_tracker.add_vote(
            chat_id=chat_id,
            user_id=user_id,
            total_listeners=5,
            required_percentage=chat_db.vote_skip_percent,
        )
        if passed:
            await query.answer(f"⏭ Skip vote passed ({current_votes}/{needed_votes})!")
            await playback_manager.play_next(chat_id)
        else:
            await query.answer(f"🗳 Skip vote registered ({current_votes}/{needed_votes} needed).", show_alert=True)

    elif data == "cb_player_replay":
        if queue.current_item and vc_client.is_connected(chat_id):
            song = queue.current_item.song
            await vc_client.join_and_play(
                chat_id=chat_id,
                stream_url=song.stream_url or song.url,
                volume=queue.volume,
                equalizer=queue.equalizer,
                bass_boost=queue.bass_boost,
                normalize=queue.normalize,
                bitrate=queue.bitrate,
                seek_sec=0
            )
            await query.answer("🔄 Replaying track.")
        else:
            await query.answer("❌ Nothing playing to replay.", show_alert=True)

    elif data == "cb_player_stop":
        await playback_manager.stop(chat_id)
        await query.answer("⏹ Playback stopped & queue cleared.")
        try:
            await query.message.delete()
        except Exception:
            pass

    elif data == "cb_player_shuffle":
        if await queue.shuffle():
            await playback_manager.update_player_ui(chat_id)
            await query.answer("🔀 Queue shuffled!")
        else:
            await query.answer("❌ Not enough tracks to shuffle.", show_alert=True)

    elif data == "cb_player_loop":
        if queue.loop_mode == LoopMode.OFF:
            queue.loop_mode = LoopMode.TRACK
            lbl = "🔂 Track Loop Enabled"
        elif queue.loop_mode == LoopMode.TRACK:
            queue.loop_mode = LoopMode.QUEUE
            lbl = "🔁 Queue Loop Enabled"
        else:
            queue.loop_mode = LoopMode.OFF
            lbl = "Loop Disabled"

        await playback_manager.update_player_ui(chat_id)
        await query.answer(f"🔁 {lbl}")

    elif data in ["cb_player_volup", "cb_player_voldown"]:
        delta = 10 if data == "cb_player_volup" else -10
        queue.volume = max(0, min(200, queue.volume + delta))

        if queue.current_item and vc_client.is_connected(chat_id):
            song = queue.current_item.song
            await vc_client.join_and_play(
                chat_id=chat_id,
                stream_url=song.stream_url or song.url,
                volume=queue.volume,
                equalizer=queue.equalizer,
                bass_boost=queue.bass_boost,
                normalize=queue.normalize,
                bitrate=queue.bitrate
            )

        await playback_manager.update_player_ui(chat_id)
        await query.answer(f"🔊 Volume set to {queue.volume}%")

    elif data == "cb_player_mute":
        if queue.volume > 0:
            queue.volume = 0
            ans = "🔇 Muted"
        else:
            queue.volume = 100
            ans = "🔊 Unmuted (100%)"

        if queue.current_item and vc_client.is_connected(chat_id):
            song = queue.current_item.song
            await vc_client.join_and_play(
                chat_id=chat_id,
                stream_url=song.stream_url or song.url,
                volume=queue.volume,
                equalizer=queue.equalizer,
                bass_boost=queue.bass_boost,
                normalize=queue.normalize,
                bitrate=queue.bitrate
            )

        await playback_manager.update_player_ui(chat_id)
        await query.answer(ans)

    elif data == "cb_player_queue":
        items = queue.get_queue_list()
        if not items:
            return await query.answer("📋 Up Next queue is currently empty.", show_alert=True)
        preview = "\n".join(
            f"{idx}. {item.song.title[:35]} ({format_duration(item.song.duration)})"
            for idx, item in enumerate(items[:5], start=1)
        )
        if len(items) > 5:
            preview += f"\n...and {len(items) - 5} more."
        await query.answer(f"📋 Up Next:\n{preview}", show_alert=True)

    elif data == "cb_player_eq":
        presets = list(EQUALIZER_PRESETS.keys())
        curr_idx = presets.index(queue.equalizer) if queue.equalizer in presets else 0
        queue.equalizer = presets[(curr_idx + 1) % len(presets)]
        await playback_manager.update_player_ui(chat_id)
        await query.answer(f"🎛 Equalizer set to: {queue.equalizer.title()}")

    elif data == "cb_player_bass":
        levels = [0, 3, 6, 10]
        nxt_lvl = next((l for l in levels if l > queue.bass_boost), 0)
        queue.bass_boost = nxt_lvl
        await playback_manager.update_player_ui(chat_id)
        lbl = f"Level {nxt_lvl}" if nxt_lvl > 0 else "Off"
        await query.answer(f"⚡ Bass Boost: {lbl}")

    elif data == "cb_player_quality":
        profiles = list(QUALITY_PROFILES.keys())
        curr_idx = profiles.index(queue.quality) if queue.quality in profiles else 0
        nxt_q = profiles[(curr_idx + 1) % len(profiles)]
        queue.quality = nxt_q
        queue.bitrate = QUALITY_PROFILES[nxt_q]
        await playback_manager.update_player_ui(chat_id)
        await query.answer(f"🌐 Quality: {nxt_q.title()} ({queue.bitrate})")

    elif data == "cb_player_fav":
        if not queue.current_item:
            return await query.answer("❌ Nothing playing.", show_alert=True)

        song = queue.current_item.song
        async with get_session() as session:
            repo = FavoriteRepository(session)
            _, created = await repo.add_favorite(
                user_id=user_id,
                song_id=song.song_id,
                title=song.title,
                artist=song.artist,
                duration=song.duration,
                url=song.url,
                thumbnail=song.thumbnail,
                source=song.source
            )

        msg = "❤️ Added to Favorites!" if created else "ℹ️ Already in Favorites!"
        await query.answer(msg, show_alert=True)

    elif data == "cb_player_lyrics":
        if not queue.current_item:
            return await query.answer("❌ Nothing playing.", show_alert=True)

        song = queue.current_item.song
        await query.answer("🔍 Fetching lyrics...")
        res = await lyrics_provider.fetch_lyrics(song.title, song.artist)
        if res and res.plain_lyrics:
            lyrics_snippet = res.plain_lyrics[:500] + "..." if len(res.plain_lyrics) > 500 else res.plain_lyrics
            await query.message.reply_text(f"🎵 **Lyrics for {escape_markdown(song.title)}:**\n\n{lyrics_snippet}")
        else:
            await query.message.reply_text(f"❌ Lyrics not found for `{escape_markdown(song.title)}`.")

    elif data == "cb_player_close":
        try:
            await query.message.delete()
        except Exception:
            pass

