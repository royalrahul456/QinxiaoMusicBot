import asyncio
import logging
from typing import Optional, Callable, Dict, Any

try:
    from pytgcalls import PyTgCalls, filters as pytg_filters
    from pytgcalls.types import MediaStream, StreamEnded
    HAS_PYTGCALLS = True
except ImportError:
    PyTgCalls = None
    pytg_filters = None
    MediaStream = None
    StreamEnded = None
    HAS_PYTGCALLS = False

from pyrogram.enums import ChatMemberStatus

from app.audio.processor import AudioProcessor

logger = logging.getLogger("QinxiaoMusic.Player.VCClient")


class VoiceChatClient:
    def __init__(self):
        self.bot_client = None
        self.assistant_client = None
        self.pytgcalls_app: Optional[Any] = None
        self._on_stream_end_cb: Optional[Callable[[int], Any]] = None
        self._on_user_left_cb: Optional[Callable[[int], Any]] = None
        self.active_chats: set = set()

    def init_app(self, bot_client, assistant_client=None):
        self.bot_client = bot_client
        self.assistant_client = assistant_client

        if self.assistant_client and HAS_PYTGCALLS:
            try:
                self.pytgcalls_app = PyTgCalls(self.assistant_client)
                stream_end_filter = (
                    pytg_filters.stream_end()
                    if isinstance(pytg_filters.stream_end, type)
                    else pytg_filters.stream_end
                )

                @self.pytgcalls_app.on_update(stream_end_filter)
                async def _on_stream_ended(client, update):
                    logger.info(f"PyTgCalls stream ended in chat {update.chat_id}")
                    self.active_chats.discard(update.chat_id)
                    if self._on_stream_end_cb:
                        asyncio.create_task(self._on_stream_end_cb(update.chat_id))

                logger.info("VoiceChatClient PyTgCalls wrapper initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize PyTgCalls wrapper: {e}")

    def set_stream_end_handler(self, cb: Callable[[int], Any]):
        self._on_stream_end_cb = cb

    def set_user_left_handler(self, cb: Callable[[int], Any]):
        self._on_user_left_cb = cb

    async def start(self):
        if self.pytgcalls_app:
            try:
                await self.pytgcalls_app.start()
                logger.info("VoiceChatClient PyTgCalls engine started successfully.")
            except Exception as e:
                logger.error(f"Failed to start PyTgCalls engine: {e}")

    async def ensure_assistant_in_chat(self, chat_id: int) -> bool:
        """Ensure assistant user account is in the group chat."""
        if not self.assistant_client:
            logger.warning(
                f"Assistant client is not configured (ASSISTANT_SESSION missing in .env); "
                f"cannot invite assistant to chat {chat_id}."
            )
            return True

        try:
            import aiohttp
            from app.config.settings import settings

            assistant_me = await self.assistant_client.get_me()
            token = settings.BOT_TOKEN
            base_url = f"https://api.telegram.org/bot{token}"

            async with aiohttp.ClientSession() as session:
                # 1. Check membership status via HTTP Bot API (avoids Pyrogram PeerIdInvalid)
                async with session.post(
                    f"{base_url}/getChatMember",
                    json={"chat_id": chat_id, "user_id": assistant_me.id}
                ) as resp:
                    data = await resp.json()
                    if data.get("ok") and "result" in data:
                        status = data["result"].get("status", "")
                        if status in ("member", "administrator", "creator"):
                            return True
                        if status in ("kicked", "banned"):
                            logger.info(f"Unbanning assistant {assistant_me.id} in chat {chat_id}...")
                            await session.post(
                                f"{base_url}/unbanChatMember",
                                json={"chat_id": chat_id, "user_id": assistant_me.id, "only_if_banned": True}
                            )

                logger.info(f"Assistant (@{assistant_me.username or assistant_me.id}) not in chat {chat_id}. Auto-joining...")

                # 2. Check chat username or existing invite_link via HTTP getChat
                async with session.post(f"{base_url}/getChat", json={"chat_id": chat_id}) as resp:
                    chat_data = await resp.json()
                    if chat_data.get("ok") and "result" in chat_data:
                        chat_info = chat_data["result"]
                        username = chat_info.get("username")
                        if username:
                            await self.assistant_client.join_chat(username)
                            logger.info(f"Assistant joined chat {chat_id} via @{username}")
                            return True
                        invite_link = chat_info.get("invite_link")
                        if invite_link:
                            await self.assistant_client.join_chat(invite_link)
                            logger.info(f"Assistant joined chat {chat_id} via existing invite link.")
                            return True

                # 3. Export or create invite link via HTTP Bot API
                for endpoint in ("exportChatInviteLink", "createChatInviteLink"):
                    async with session.post(f"{base_url}/{endpoint}", json={"chat_id": chat_id}) as resp:
                        link_data = await resp.json()
                        if link_data.get("ok") and link_data.get("result"):
                            res = link_data["result"]
                            link = res if isinstance(res, str) else res.get("invite_link")
                            if link:
                                await self.assistant_client.join_chat(link)
                                logger.info(f"Assistant joined chat {chat_id} via {endpoint}.")
                                return True

            # 4. Fallback: Try adding assistant directly via Pyrogram if peer is cached
            if self.bot_client and getattr(self.bot_client, "is_connected", False):
                try:
                    await self.bot_client.add_chat_members(chat_id, assistant_me.id)
                    logger.info(f"Bot added assistant {assistant_me.id} to chat {chat_id}")
                    return True
                except Exception as ae:
                    logger.warning(f"Could not add assistant user directly: {ae}")

            return True
        except Exception as e:
            logger.error(f"Error ensuring assistant in chat {chat_id}: {e}")
            return True

    async def join_and_play(
        self,
        chat_id: int,
        stream_url: str,
        volume: int = 100,
        equalizer: str = "off",
        bass_boost: int = 0,
        normalize: bool = False,
        bitrate: str = "320k",
        seek_sec: Optional[int] = None,
        headers: Optional[dict] = None
    ) -> bool:
        logger.info(f"Joining and playing stream in chat {chat_id} (url={stream_url[:40]}...)")
        await self.ensure_assistant_in_chat(chat_id)

        ffmpeg_params = AudioProcessor.build_ffmpeg_parameters(
            equalizer=equalizer,
            bass_boost=bass_boost,
            normalize=normalize,
            volume=volume,
            bitrate=bitrate,
            seek_sec=seek_sec
        )

        if self.pytgcalls_app:
            try:
                stream = MediaStream(
                    media_path=stream_url,
                    video_flags=MediaStream.Flags.IGNORE,
                    ffmpeg_parameters=ffmpeg_params or None,
                    headers=headers
                )
                await self.pytgcalls_app.play(chat_id, stream)
                if volume != 100:
                    try:
                        await self.pytgcalls_app.change_volume_call(chat_id, volume)
                    except Exception:
                        pass
                self.active_chats.add(chat_id)
                logger.info(f"PyTgCalls stream active in chat {chat_id}")
                return True
            except Exception as e:
                logger.error(f"PyTgCalls play error in chat {chat_id}: {e}")
                return False
        else:
            logger.warning(f"PyTgCalls engine is not initialized; running in UI-only fallback mode for chat {chat_id}.")
            self.active_chats.add(chat_id)
            return True

    async def pause(self, chat_id: int) -> bool:
        if self.pytgcalls_app:
            try:
                await self.pytgcalls_app.pause(chat_id)
                logger.info(f"Paused PyTgCalls in chat {chat_id}")
                return True
            except Exception as e:
                logger.error(f"Pause error in chat {chat_id}: {e}")
        return True

    async def resume(self, chat_id: int) -> bool:
        if self.pytgcalls_app:
            try:
                await self.pytgcalls_app.resume(chat_id)
                logger.info(f"Resumed PyTgCalls in chat {chat_id}")
                return True
            except Exception as e:
                logger.error(f"Resume error in chat {chat_id}: {e}")
        return True

    async def change_volume(self, chat_id: int, volume: int) -> bool:
        if self.pytgcalls_app:
            try:
                await self.pytgcalls_app.change_volume_call(chat_id, volume)
                logger.info(f"Volume changed to {volume} in chat {chat_id}")
                return True
            except Exception as e:
                logger.error(f"Change volume error in chat {chat_id}: {e}")
        return True

    async def leave(self, chat_id: int) -> bool:
        if self.pytgcalls_app:
            try:
                await self.pytgcalls_app.leave_call(chat_id)
                logger.info(f"Left voice chat call {chat_id}")
            except Exception as e:
                logger.debug(f"Leave voice chat call error: {e}")
        self.active_chats.discard(chat_id)
        await self.leave_group(chat_id)
        return True

    async def leave_group(self, chat_id: int) -> bool:
        """Make assistant user account leave the Telegram group cleanly without banning."""
        if not self.assistant_client:
            return True

        try:
            await self.assistant_client.leave_chat(chat_id)
            logger.info(f"Assistant user left group {chat_id} cleanly.")
            return True
        except Exception as e:
            logger.debug(f"Assistant leave_chat error (may have already left): {e}")
            return False

    def is_connected(self, chat_id: int) -> bool:
        return chat_id in self.active_chats


vc_client = VoiceChatClient()
