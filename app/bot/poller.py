import asyncio
import logging
import aiohttp
from typing import Optional

from app.config.settings import settings
from app.handlers import (
    start_command,
    help_command,
    about_command,
    play_command,
    pause_command,
    resume_command,
    skip_command,
    stop_command,
    volume_command,
    queue_command,
    nowplaying_command,
    shuffle_command,
    clear_command,
    loop_command,
    loopqueue_command,
    autoplay_command,
    quality_command,
    bitrate_command,
    equalizer_command,
    bassboost_command,
    normalizer_command,
    audioinfo_command,
    lyrics_command,
    syncedlyrics_command,
    fav_command,
    unfav_command,
    favorites_command,
    profile_command,
    mystats_command,
    history_command,
    settings_command,
    join_command,
    leave_command,
    vc_command,
    player_command,
    toggle_247_command,
    autoleave_command,
    top_command,
    topsongs_command,
    topartists_command,
    groupstats_command,
    listeningtime_command,
    premium_command,
    plans_command,
    activate_command,
    myplan_command,
    genkey_command,
    revokekey_command,
    broadcast_command,
    botstats_command,
    activevc_command,
    leaveall_command,
    maintenance_command,
    restart_command,
    cache_command,
    clearcache_command,
    speedtest_command,
    addsudo_command,
    delsudo_command,
    sudolist_command,
)
from app.callbacks.player_cb import player_callback_handler
from app.callbacks.settings_cb import settings_callback_handler
from app.callbacks.pagination_cb import pagination_callback_handler

logger = logging.getLogger("QinxiaoMusic.BotPoller")


class MockUser:
    def __init__(self, d: dict):
        self.id = d.get("id", 0)
        self.username = d.get("username")
        self.first_name = d.get("first_name", "User")


class MockChat:
    def __init__(self, d: dict):
        self.id = d.get("id", 0)
        self.title = d.get("title")
        self.type = d.get("type")


class MockMessage:
    def __init__(self, d: dict, bot_token: str, session: aiohttp.ClientSession):
        self._raw = d
        self._bot_token = bot_token
        self._session = session
        self.message_id = d.get("message_id", 0)
        self.id = self.message_id
        self.chat = MockChat(d.get("chat", {}))
        user_dict = d.get("from") or d.get("from_user") or {}
        self.from_user = MockUser(user_dict)
        self.text = d.get("text", "")
        self.command = self.text.split() if self.text else []
        self.reply_to_message = MockMessage(d.get("reply_to_message"), bot_token, session) if d.get("reply_to_message") else None

    @staticmethod
    def _serialize_reply_markup(reply_markup):
        if reply_markup and hasattr(reply_markup, "inline_keyboard"):
            kb = []
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
            return {"inline_keyboard": kb}
        return None

    async def reply_text(self, text: str, reply_markup=None, disable_web_page_preview=False, parse_mode=None):
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        mode = parse_mode
        if mode is None:
            mode = "HTML" if ("<" in text and ">" in text) else "Markdown"
        elif hasattr(mode, "value"):
            mode = mode.value
        elif hasattr(mode, "name"):
            mode = mode.name

        payload = {
            "chat_id": self.chat.id,
            "text": text,
            "parse_mode": mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        serialized_kb = self._serialize_reply_markup(reply_markup)
        if serialized_kb:
            payload["reply_markup"] = serialized_kb

        try:
            async with self._session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    return MockMessage(data["result"], self._bot_token, self._session)
                else:
                    # Fallback plain text if markup error
                    payload["parse_mode"] = None
                    async with self._session.post(url, json=payload) as r2:
                        res2 = await r2.json()
                        if res2.get("ok"):
                            return MockMessage(res2["result"], self._bot_token, self._session)
        except Exception as e:
            logger.error(f"Error replying text via HTTP Bot API: {e}")

    async def edit_text(self, text: str, reply_markup=None, disable_web_page_preview=False, parse_mode=None):
        url = f"https://api.telegram.org/bot{self._bot_token}/editMessageText"
        mode = parse_mode
        if mode is None:
            mode = "HTML" if ("<" in text and ">" in text) else "Markdown"
        elif hasattr(mode, "value"):
            mode = mode.value
        elif hasattr(mode, "name"):
            mode = mode.name

        payload = {
            "chat_id": self.chat.id,
            "message_id": self.message_id,
            "text": text,
            "parse_mode": mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        serialized_kb = self._serialize_reply_markup(reply_markup)
        if serialized_kb:
            payload["reply_markup"] = serialized_kb

        try:
            async with self._session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    return MockMessage(data["result"], self._bot_token, self._session)
                else:
                    payload["parse_mode"] = None
                    async with self._session.post(url, json=payload) as r2:
                        res2 = await r2.json()
                        if res2.get("ok"):
                            return MockMessage(res2["result"], self._bot_token, self._session)
        except Exception as e:
            logger.error(f"Error editing text via HTTP Bot API: {e}")

    async def delete(self):
        url = f"https://api.telegram.org/bot{self._bot_token}/deleteMessage"
        payload = {"chat_id": self.chat.id, "message_id": self.message_id}
        try:
            await self._session.post(url, json=payload)
        except Exception:
            pass


class MockCallbackQuery:
    def __init__(self, d: dict, bot_token: str, session: aiohttp.ClientSession):
        self.id = d.get("id")
        user_dict = d.get("from") or d.get("from_user") or {}
        self.from_user = MockUser(user_dict)
        self.message = MockMessage(d.get("message", {}), bot_token, session)
        self.data = d.get("data", "")
        self._bot_token = bot_token
        self._session = session

    async def answer(self, text: str = "", show_alert: bool = False):
        url = f"https://api.telegram.org/bot{self._bot_token}/answerCallbackQuery"
        payload = {"callback_query_id": self.id, "text": text, "show_alert": show_alert}
        try:
            await self._session.post(url, json=payload)
        except Exception:
            pass


class TelegramBotPoller:
    """HTTP Bot API Poller providing instant update processing for Qinxiao Music."""

    def __init__(self):
        self._offset = 0
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False

        # Command map
        self._commands = {
            "/start": start_command,
            "/help": help_command,
            "/about": about_command,
            "/play": play_command,
            "/search": play_command,
            "/yt": play_command,
            "/spotify": play_command,
            "/soundcloud": play_command,
            "/playlist": play_command,
            "/artist": play_command,
            "/album": play_command,
            "/recommend": play_command,
            "/trending": play_command,
            "/pause": pause_command,
            "/resume": resume_command,
            "/skip": skip_command,
            "/stop": stop_command,
            "/volume": volume_command,
            "/vol": volume_command,
            "/queue": queue_command,
            "/nowplaying": nowplaying_command,
            "/np": nowplaying_command,
            "/shuffle": shuffle_command,
            "/clear": clear_command,
            "/loop": loop_command,
            "/loopqueue": loopqueue_command,
            "/autoplay": autoplay_command,
            "/quality": quality_command,
            "/bitrate": bitrate_command,
            "/equalizer": equalizer_command,
            "/eq": equalizer_command,
            "/bassboost": bassboost_command,
            "/bass": bassboost_command,
            "/normalizer": normalizer_command,
            "/loudnorm": normalizer_command,
            "/audioinfo": audioinfo_command,
            "/lyrics": lyrics_command,
            "/syncedlyrics": syncedlyrics_command,
            "/fav": fav_command,
            "/unfav": unfav_command,
            "/favorites": favorites_command,
            "/favs": favorites_command,
            "/profile": profile_command,
            "/mystats": mystats_command,
            "/history": history_command,
            "/settings": settings_command,
            "/join": join_command,
            "/leave": leave_command,
            "/vc": vc_command,
            "/player": player_command,
            "/247": toggle_247_command,
            "/autoleave": autoleave_command,
            "/top": top_command,
            "/topsongs": topsongs_command,
            "/topartists": topartists_command,
            "/groupstats": groupstats_command,
            "/listeningtime": listeningtime_command,
            "/premium": premium_command,
            "/plans": plans_command,
            "/activate": activate_command,
            "/myplan": myplan_command,
            "/genkey": genkey_command,
            "/revokekey": revokekey_command,
            "/broadcast": broadcast_command,
            "/botstats": botstats_command,
            "/activevc": activevc_command,
            "/leaveall": leaveall_command,
            "/maintenance": maintenance_command,
            "/restart": restart_command,
            "/cache": cache_command,
            "/clearcache": clearcache_command,
            "/speedtest": speedtest_command,
            "/addsudo": addsudo_command,
            "/delsudo": delsudo_command,
            "/sudolist": sudolist_command,
        }

    async def get_chat_member(self, chat_id: int, user_id: int):
        """HTTP Bot API fallback for get_chat_member used in permission checks."""
        if not self._session or self._session.closed:
            return None
        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getChatMember"
        payload = {"chat_id": chat_id, "user_id": user_id}
        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()
            if data.get("ok") and "result" in data:
                status_str = data["result"].get("status", "member")
                return type("MockChatMember", (), {"status": status_str})()
        return None

    async def start(self):
        if not settings.BOT_TOKEN:
            logger.error("BOT_TOKEN is not configured; TelegramBotPoller cannot start.")
            return

        self._session = aiohttp.ClientSession()
        self._running = True

        # Drop pending updates
        try:
            url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/deleteWebhook?drop_pending_updates=True"
            await self._session.get(url)
        except Exception:
            pass

        logger.info("TelegramBotPoller started HTTP long-polling loop.")

        while self._running:
            try:
                url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getUpdates?offset={self._offset}&timeout=10"
                async with self._session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            for update in data.get("result", []):
                                self._offset = update["update_id"] + 1
                                asyncio.create_task(self._process_update(update))
            except Exception:
                await asyncio.sleep(2)

    async def _process_update(self, update: dict):
        if "message" in update:
            msg_dict = update["message"]
            msg = MockMessage(msg_dict, settings.BOT_TOKEN, self._session)
            text = msg.text.strip() if msg.text else ""

            if text.startswith("/"):
                cmd_part = text.split()[0].lower().split("@")[0]
                handler = self._commands.get(cmd_part)
                if handler:
                    logger.info(f"Poller processing command {cmd_part} from user {msg.from_user.id}")
                    try:
                        await handler(self, msg)
                    except Exception as e:
                        logger.error(f"Error handling command {cmd_part}: {e}", exc_info=True)

        elif "callback_query" in update:
            cb_dict = update["callback_query"]
            cb = MockCallbackQuery(cb_dict, settings.BOT_TOKEN, self._session)
            data = cb.data
            logger.info(f"Poller processing callback {data} from user {cb.from_user.id}")

            try:
                if data.startswith("cb_player_"):
                    await player_callback_handler(self, cb)
                elif data.startswith("cb_page_"):
                    await pagination_callback_handler(self, cb)
                elif data.startswith("cb_"):
                    await settings_callback_handler(self, cb)
            except Exception as e:
                logger.error(f"Error handling callback {data}: {e}", exc_info=True)

    async def stop(self):
        self._running = False
        if self._session and not self._session.closed:
            await self._session.close()


bot_poller = TelegramBotPoller()
