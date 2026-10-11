import logging
from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.providers.manager import provider_manager
from app.player.queue_manager import queue_manager, QueueItem
from app.player.playback import playback_manager
from app.player.vc_client import vc_client
from app.player.vote_skip import vote_skip_tracker
from app.permissions.checker import is_admin
from app.database.session import get_session
from app.repositories.chat_repo import ChatRepository
from app.repositories.stats_repo import StatsRepository
from app.utils.formatting import format_duration, escape_markdown

logger = logging.getLogger("QinxiaoMusic.Handlers.Play")


async def _check_playback_permission(client, chat_id: int, user) -> bool:
    if chat_id > 0:
        return True
    user_id = user.id if user else 0
    queue = await queue_manager.get_queue(chat_id)
    if queue.current_item and queue.current_item.requested_by_id == user_id and user_id > 0:
        return True
    async with get_session() as session:
        return await is_admin(client, chat_id, user_id, session)


@rate_limit("search", 2.0)
async def play_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    cmd = message.command[0].lower().split("@")[0].lstrip("/") if message.command else "play"

    queue = await queue_manager.get_queue(chat_id)

    # Handle /trending and /recommend which do not require an explicit query argument
    if cmd == "trending" and len(message.command) < 2:
        status_msg = await message.reply_text("🔥 **Qinxiao Music** is fetching trending tracks...")
        results = await provider_manager.get_trending(limit=1)
        query_label = "Trending Music"
    elif cmd == "recommend" and len(message.command) < 2:
        if queue.current_item:
            status_msg = await message.reply_text("📻 **Qinxiao Music** is finding recommendations...")
            results = await provider_manager.get_recommendations(queue.current_item.song, limit=1)
            query_label = f"Recommendations for {queue.current_item.song.title}"
        else:
            status_msg = await message.reply_text("🔥 **Qinxiao Music** is fetching top recommendations...")
            results = await provider_manager.get_trending(limit=1)
            query_label = "Recommended Music"
    else:
        if len(message.command) < 2:
            return await message.reply_text("❌ Please specify a song name or URL!\nExample: `/play Faded Alan Walker`")

        query = " ".join(message.command[1:])
        query_label = escape_markdown(query)
        status_msg = await message.reply_text(f"🔍 **Qinxiao Music** is searching for `{query_label}`...")

        if cmd == "playlist":
            results = await provider_manager.get_playlist(query, limit=queue.max_size)
        else:
            provider_map = {
                "yt": "youtube",
                "spotify": "spotify",
                "soundcloud": "soundcloud",
            }
            p_name = provider_map.get(cmd, "auto")
            results = await provider_manager.search(query, provider_name=p_name, limit=1)

    if not results:
        return await status_msg.edit_text(f"❌ No music results found for `{query_label}`.")

    # If multiple tracks returned (e.g. /playlist), enqueue all
    if len(results) > 1:
        should_start = not vc_client.is_connected(chat_id) or queue.current_item is None
        added_count = 0
        for s in results:
            q_item = QueueItem(
                song=s,
                requested_by_id=user.id if user else 0,
                requested_by_name=user.first_name if user else "User"
            )
            ok, _ = await queue.add(q_item, allow_duplicate=True)
            if ok:
                added_count += 1

        if should_start and added_count > 0:
            await status_msg.edit_text(f"📃 **Loaded playlist:** Starting playback and queued `{added_count}` tracks!")
            await playback_manager.play_next(chat_id)
        else:
            await status_msg.edit_text(f"➕ **Added `{added_count}` playlist tracks to the Qinxiao Queue!**")
        return

    song = results[0]
    safe_title = escape_markdown(song.title)
    safe_artist = escape_markdown(song.artist)

    item = QueueItem(
        song=song,
        requested_by_id=user.id if user else 0,
        requested_by_name=user.first_name if user else "User"
    )

    if vc_client.is_connected(chat_id) and queue.current_item is not None:
        added, reason = await queue.add(item)
        if added:
            await status_msg.edit_text(
                f"➕ **Added to Qinxiao Queue:** [{safe_title}]({song.url})\n"
                f"🎙 **Artist:** `{safe_artist}` | ⏱ **Duration:** `{format_duration(song.duration)}`"
            )
        else:
            await status_msg.edit_text(f"⚠️ Could not add to queue: {reason}")
    else:
        # Start playback directly: add item to queue so play_next -> queue.get_next() pops and plays it
        await queue.add(item, allow_duplicate=True)
        await status_msg.edit_text(f"⏳ **Starting playback for:** [{safe_title}]({song.url})...")
        await playback_manager.play_next(chat_id)


@rate_limit("command", 1.0)
async def pause_command(client, message: Message):
    chat_id = message.chat.id
    if not vc_client.is_connected(chat_id):
        return await message.reply_text("❌ Qinxiao Music is not currently playing in this chat.")

    if not await _check_playback_permission(client, chat_id, message.from_user):
        return await message.reply_text("❌ Only group admins or the song requester can pause playback.")

    success = await vc_client.pause(chat_id)
    if success:
        await playback_manager.update_player_ui(chat_id, is_paused=True)
        await message.reply_text("⏸ **Qinxiao Music playback paused.**")
    else:
        await message.reply_text("❌ Failed to pause playback.")


@rate_limit("command", 1.0)
async def resume_command(client, message: Message):
    chat_id = message.chat.id
    if not vc_client.is_connected(chat_id):
        return await message.reply_text("❌ Qinxiao Music is not currently playing in this chat.")

    if not await _check_playback_permission(client, chat_id, message.from_user):
        return await message.reply_text("❌ Only group admins or the song requester can resume playback.")

    success = await vc_client.resume(chat_id)
    if success:
        await playback_manager.update_player_ui(chat_id, is_paused=False)
        await message.reply_text("▶️ **Qinxiao Music playback resumed.**")
    else:
        await message.reply_text("❌ Failed to resume playback.")


@rate_limit("command", 1.0)
async def skip_command(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user

    if not vc_client.is_connected(chat_id):
        return await message.reply_text("❌ Qinxiao Music is not playing in this chat.")

    # Admin bypass check
    async with get_session() as session:
        chat_repo = ChatRepository(session)
        chat_db = await chat_repo.get_or_create(chat_id)
        user_is_admin = await is_admin(client, chat_id, user.id if user else 0, session)

    if user_is_admin or chat_id > 0:
        await message.reply_text("⏭ **Skipped track (Admin Bypass).**")
        await playback_manager.play_next(chat_id)
        return

    # Skip voting calculation
    passed, current_votes, needed_votes = await vote_skip_tracker.add_vote(
        chat_id=chat_id,
        user_id=user.id if user else 0,
        total_listeners=5,
        required_percentage=chat_db.vote_skip_percent
    )

    if passed:
        await message.reply_text(f"⏭ **Skip Vote Passed ({current_votes}/{needed_votes})! Skipping track...**")
        await playback_manager.play_next(chat_id)
    else:
        await message.reply_text(f"🗳 **Vote registered ({current_votes}/{needed_votes} required to skip).**")


@rate_limit("command", 1.0)
async def stop_command(client, message: Message):
    chat_id = message.chat.id
    if not vc_client.is_connected(chat_id):
        return await message.reply_text("❌ Qinxiao Music is not playing in this chat.")

    user = message.from_user
    if chat_id < 0:
        async with get_session() as session:
            if not await is_admin(client, chat_id, user.id if user else 0, session):
                return await message.reply_text("❌ Only group administrators can stop playback and clear the queue.")

    await playback_manager.stop(chat_id)
    await message.reply_text("⏹ **Playback stopped and Qinxiao queue cleared.**")


@rate_limit("command", 1.0)
async def volume_command(client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        queue = await queue_manager.get_queue(chat_id)
        return await message.reply_text(f"🔊 **Current Qinxiao volume:** `{queue.volume}%`\nUse `/volume <0-200>` to change.")

    if not await _check_playback_permission(client, chat_id, message.from_user):
        return await message.reply_text("❌ Only group administrators or the song requester can change playback volume.")

    try:
        vol = int(message.command[1])
        if vol < 0 or vol > 200:
            return await message.reply_text("❌ Volume must be between 0 and 200.")

        queue = await queue_manager.get_queue(chat_id)
        queue.volume = vol

        if queue.current_item and vc_client.is_connected(chat_id):
            resolved = queue.current_item.song
            await vc_client.join_and_play(
                chat_id=chat_id,
                stream_url=resolved.stream_url or resolved.url,
                volume=queue.volume,
                equalizer=queue.equalizer,
                bass_boost=queue.bass_boost,
                normalize=queue.normalize,
                bitrate=queue.bitrate
            )

        await playback_manager.update_player_ui(chat_id)
        await message.reply_text(f"🔊 **Volume updated to:** `{vol}%`")
    except ValueError:
        await message.reply_text("❌ Invalid volume number.")

