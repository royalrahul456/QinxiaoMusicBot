from pyrogram.types import CallbackQuery
from app.middleware.anti_spam import rate_limit


@rate_limit("callback", 0.5)
async def pagination_callback_handler(client, query: CallbackQuery):
    await query.answer("📄 Page updated.")
