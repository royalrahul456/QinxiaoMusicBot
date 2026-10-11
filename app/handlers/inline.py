import logging
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.config.settings import settings
from app.middleware.anti_spam import rate_limit
from app.providers.manager import provider_manager
from app.utils.formatting import format_duration

logger = logging.getLogger("QinxiaoMusic.Handlers.Inline")


@rate_limit("search", 1.5)
async def inline_search_handler(client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        # Default prompt when query is empty
        results = [
            InlineQueryResultArticle(
                title="🎵 Qinxiao Music Inline Search",
                description="Type a song title or artist to search!",
                input_message_content=InputTextMessageContent(
                    f"🎵 **Qinxiao Music (@QinxiaoMusicBot)**\nUse inline search to find and share music directly in any chat!"
                ),
                thumb_url="https://raw.githubusercontent.com/telegram/pyrogram/master/docs/source/_static/pyrogram.png"
            )
        ]
        return await inline_query.answer(results, cache_time=10)

    # Perform music search
    tracks = await provider_manager.search(query, provider_name="auto", limit=10)
    results = []

    for t in tracks:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ Play on Qinxiao Music", url=f"https://t.me/{settings.BOT_USERNAME.replace('@', '')}?start=play_{t.song_id}"),
                InlineKeyboardButton("🎵 Open Song Link", url=t.url),
            ]
        ])

        msg_content = InputTextMessageContent(
            f"🎵 **Qinxiao Music Track Share**\n"
            f"📌 **Title:** [{t.title}]({t.url})\n"
            f"🎙 **Artist:** `{t.artist}`\n"
            f"⏱ **Duration:** `{format_duration(t.duration)}`\n"
            f"🎧 **Source:** `{t.source.title()}`\n\n"
            f"Play on **Qinxiao Music (@QinxiaoMusicBot)**",
            disable_web_page_preview=False
        )

        results.append(
            InlineQueryResultArticle(
                title=t.title,
                description=f"{t.artist} ({format_duration(t.duration)})",
                input_message_content=msg_content,
                reply_markup=keyboard,
                thumb_url=t.thumbnail or "https://raw.githubusercontent.com/telegram/pyrogram/master/docs/source/_static/pyrogram.png"
            )
        )

    await inline_query.answer(results, cache_time=300)
