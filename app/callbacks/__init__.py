from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler

from app.callbacks.player_cb import player_callback_handler
from app.callbacks.settings_cb import settings_callback_handler
from app.callbacks.pagination_cb import pagination_callback_handler


def register_all_callbacks(app):
    """Register all callback query handlers for Qinxiao Music."""
    app.add_handler(CallbackQueryHandler(player_callback_handler, filters.regex(r"^cb_player_")))
    app.add_handler(CallbackQueryHandler(settings_callback_handler, filters.regex(r"^cb_(help|about|premium|user|set_)")))
    app.add_handler(CallbackQueryHandler(pagination_callback_handler, filters.regex(r"^cb_page_")))
