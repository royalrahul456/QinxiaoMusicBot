import asyncio
import logging
import aiohttp
from typing import Optional

from app.config.settings import settings
from app.player.queue_manager import queue_manager, GroupQueue, QueueItem, LoopMode
from app.player.vc_client import vc_client
from app.player.vote_skip import vote_skip_tracker
from app.player.ui import build_player_text, build_player_keyboard
from app.providers.manager import provider_manager
from app.database.session import get_session
from app.repositories.user_repo import UserRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.song_repo import SongRepository
from app.repositories.stats_repo import StatsRepository

logger = logging.getLogger("QinxiaoMusic.Player.Playback")


class PlaybackManager:
    def __init__(self):
        self._bot_client = None
        self._auto_leave_tasks: dict = {}

    def init_bot(self, bot_client):
        self._bot_client = bot_client
        vc_client.set_stream_end_handler(self._on_stream_end)

    async def play_next(self, chat_id: int, _retry_count: int = 0) -> bool:
        if _retry_count >= 3:
            logger.error(f"Exceeded max stream resolution/playback retries (3) in chat {chat_id}. Stopping playback.")
            queue = await queue_manager.get_queue(chat_id)
            queue.current_item = None
            return False

        queue = await queue_manager.get_queue(chat_id)
        next_item = await queue.get_next()

        if not next_item:
            if queue.autoplay and queue.current_item:
                logger.info(f"Autoplay active in chat {chat_id}. Fetching recommendations...")
                recs = await provider_manager.get_recommendations(queue.current_item.song, limit=1)
                if recs:
                    auto_item = QueueItem(
                        song=recs[0],
                        requested_by_id=0,
                        requested_by_name="Qinxiao Autoplay"
                    )
                    queue.current_item = auto_item
                    next_item = auto_item

        if not next_item:
            logger.info(f"Queue empty in chat {chat_id}.")
            async with get_session() as session:
                chat_repo = ChatRepository(session)
                chat_db = await chat_repo.get_or_create(chat_id)
                if not chat_db.is_247 and chat_db.autoleave:
                    self._schedule_auto_leave(chat_id, chat_db.autoleave_delay)
            return False

        self._cancel_auto_leave(chat_id)
        await vote_skip_tracker.reset(chat_id)

        # Resolve stream URL
        resolved_song = await provider_manager.resolve_stream(next_item.song)
        if not resolved_song or not resolved_song.stream_url:
            logger.error(f"Failed to resolve stream for song: {next_item.song.title}")
            if queue.loop_mode == LoopMode.TRACK:
                queue.current_item = None
            return await self.play_next(chat_id, _retry_count=_retry_count + 1)

        next_item.song = resolved_song

        success = await vc_client.join_and_play(
            chat_id=chat_id,
            stream_url=resolved_song.stream_url,
            volume=queue.volume,
            equalizer=queue.equalizer,
            bass_boost=queue.bass_boost,
            normalize=queue.normalize,
            bitrate=queue.bitrate
        )

        if success:
            await self._record_playback_stats(chat_id, next_item)
            await self.update_player_ui(chat_id)
            return True
        else:
            logger.error(f"Failed to play stream in chat {chat_id}. Attempting next...")
            if queue.loop_mode == LoopMode.TRACK:
                queue.current_item = None
            return await self.play_next(chat_id, _retry_count=_retry_count + 1)

    async def _on_stream_end(self, chat_id: int):
        logger.info(f"Stream end callback received for chat {chat_id}")
        await self.play_next(chat_id)

    async def update_player_ui(self, chat_id: int, is_paused: bool = False):
        from pyrogram.enums import ParseMode
        queue = await queue_manager.get_queue(chat_id)
        if not queue.current_item:
            if queue.active_player_message_id:
                await self._delete_active_player_message(chat_id, queue)
            return

        text = build_player_text(queue, is_paused=is_paused)
        reply_markup = build_player_keyboard(queue, is_paused=is_paused)
        song = queue.current_item.song
        thumb = song.thumbnail or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600"

        bot_connected = bool(self._bot_client and getattr(self._bot_client, "is_connected", False))

        # 1. If message already exists and just updating pause/resume state, try edit_caption
        if bot_connected and queue.active_player_message_id and is_paused:
            try:
                await self._bot_client.edit_message_caption(
                    chat_id=chat_id,
                    message_id=queue.active_player_message_id,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                return
            except Exception as e:
                logger.debug(f"Pyrogram edit_message_caption failed: {e}")

        # 2. For a new song or if edit failed, delete old player message and send new photo
        if bot_connected:
            if queue.active_player_message_id:
                try:
                    await self._bot_client.delete_messages(chat_id, queue.active_player_message_id)
                except Exception:
                    pass
                queue.active_player_message_id = None

            try:
                msg = await self._bot_client.send_photo(
                    chat_id=chat_id,
                    photo=thumb,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                queue.active_player_message_id = msg.id
                return
            except Exception as e:
                logger.warning(f"Pyrogram send_photo failed: {e}. Trying fallback...")
                try:
                    msg = await self._bot_client.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    queue.active_player_message_id = msg.id
                    return
                except Exception as ex2:
                    logger.error(f"Pyrogram fallback send_message failed: {ex2}")

        # 3. HTTP Bot API Fallback
        await self._send_http_player_ui(chat_id, thumb, text, reply_markup, queue, is_paused=is_paused)

    async def _delete_active_player_message(self, chat_id: int, queue: GroupQueue):
        msg_id = queue.active_player_message_id
        if not msg_id:
            return
        queue.active_player_message_id = None
        if self._bot_client and getattr(self._bot_client, "is_connected", False):
            try:
                await self._bot_client.delete_messages(chat_id, msg_id)
                return
            except Exception:
                pass
        try:
            async with aiohttp.ClientSession() as session:
                del_url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/deleteMessage"
                await session.post(del_url, json={"chat_id": chat_id, "message_id": msg_id})
        except Exception:
            pass

    async def _send_http_player_ui(self, chat_id: int, photo: str, text: str, reply_markup, queue: GroupQueue, is_paused: bool = False):
        token = settings.BOT_TOKEN
        kb = []
        if reply_markup and hasattr(reply_markup, "inline_keyboard"):
            for row in reply_markup.inline_keyboard:
                r = []
                for b in row:
                    item = {"text": b.text}
                    if getattr(b, "url", None):
                        item["url"] = b.url
                    elif getattr(b, "callback_data", None):
                        item["callback_data"] = b.callback_data
                    r.append(item)
                kb.append(r)

        async with aiohttp.ClientSession() as session:
            # Try editing caption if message exists
            if queue.active_player_message_id and is_paused:
                edit_caption_url = f"https://api.telegram.org/bot{token}/editMessageCaption"
                payload = {
                    "chat_id": chat_id,
                    "message_id": queue.active_player_message_id,
                    "caption": text,
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": kb}
                }
                try:
                    async with session.post(edit_caption_url, json=payload) as resp:
                        res = await resp.json()
                        if res.get("ok"):
                            return
                except Exception as e:
                    logger.debug(f"HTTP edit caption failed: {e}")

            # Delete previous message
            if queue.active_player_message_id:
                del_url = f"https://api.telegram.org/bot{token}/deleteMessage"
                try:
                    await session.post(del_url, json={"chat_id": chat_id, "message_id": queue.active_player_message_id})
                except Exception:
                    pass
                queue.active_player_message_id = None

            # Send new photo
            send_photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
            photo_payload = {
                "chat_id": chat_id,
                "photo": photo,
                "caption": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": kb}
            }
            try:
                async with session.post(send_photo_url, json=photo_payload) as resp:
                    res = await resp.json()
                    if res.get("ok"):
                        queue.active_player_message_id = res["result"]["message_id"]
                        return
            except Exception as e:
                logger.warning(f"HTTP sendPhoto failed: {e}")

            # Text fallback if photo fails
            send_text_url = f"https://api.telegram.org/bot{token}/sendMessage"
            text_payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": {"inline_keyboard": kb}
            }
            try:
                async with session.post(send_text_url, json=text_payload) as r2:
                    d2 = await r2.json()
                    if d2.get("ok"):
                        queue.active_player_message_id = d2["result"]["message_id"]
            except Exception as ex2:
                logger.error(f"HTTP text fallback failed: {ex2}")

    async def stop(self, chat_id: int) -> bool:
        queue = await queue_manager.get_queue(chat_id)
        await self._delete_active_player_message(chat_id, queue)
        await queue.clear()
        queue.current_item = None
        await vc_client.leave(chat_id)

        async with get_session() as session:
            chat_repo = ChatRepository(session)
            chat_db = await chat_repo.get_or_create(chat_id)
            if not chat_db.is_247:
                await queue_manager.remove_queue(chat_id)

        return True

    def _schedule_auto_leave(self, chat_id: int, delay_seconds: int = 180):
        self._cancel_auto_leave(chat_id)

        async def _leave_job():
            await asyncio.sleep(delay_seconds)
            logger.info(f"Auto-leave triggered for idle chat {chat_id}")
            await self.stop(chat_id)

        self._auto_leave_tasks[chat_id] = asyncio.create_task(_leave_job())

    def _cancel_auto_leave(self, chat_id: int):
        if chat_id in self._auto_leave_tasks:
            self._auto_leave_tasks[chat_id].cancel()
            del self._auto_leave_tasks[chat_id]

    async def _record_playback_stats(self, chat_id: int, item: QueueItem):
        try:
            async with get_session() as session:
                user_repo = UserRepository(session)
                song_repo = SongRepository(session)
                stats_repo = StatsRepository(session)

                song = item.song
                if item.requested_by_id > 0:
                    await user_repo.add_history(
                        user_id=item.requested_by_id,
                        chat_id=chat_id,
                        song_id=song.song_id,
                        title=song.title,
                        artist=song.artist,
                        duration=song.duration,
                        url=song.url,
                        thumbnail=song.thumbnail
                    )
                    await user_repo.add_stats(item.requested_by_id, float(song.duration))

                await song_repo.add_or_update(
                    song_id=song.song_id,
                    title=song.title,
                    artist=song.artist,
                    duration=song.duration,
                    url=song.url,
                    source=song.source,
                    thumbnail=song.thumbnail,
                    album=song.album
                )

                await stats_repo.record_group_play(chat_id, song.duration)
                await stats_repo.increment_stat("total_plays", 1)
        except Exception as e:
            logger.error(f"Error recording stats: {e}")


playback_manager = PlaybackManager()
