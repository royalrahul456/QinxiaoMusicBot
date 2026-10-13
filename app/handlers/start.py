from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.config.settings import settings
from app.middleware.anti_spam import rate_limit
from app.database.session import get_session
from app.repositories.user_repo import UserRepository


@rate_limit("command", 1.0)
async def start_command(client, message: Message):
    user = message.from_user
    if user:
        async with get_session() as session:
            repo = UserRepository(session)
            await repo.get_or_create(user.id, user.username, user.first_name)

    start_text = (
        f"<blockquote>"
        f"🎧 <b>╭─[ 🎵 {settings.BOT_NAME.upper()} ]</b>\n"
        f"<b>│</b>\n"
        f"<b>├── 🎶 ⇢ HIGH-QUALITY MUSIC</b>\n"
        f"<b>├── ⚡ ⇢ FAST & SMOOTH PLAYBACK</b>\n"
        f"<b>├── 🎼 ⇢ YOUR MUSIC, YOUR VIBE</b>\n"
        f"<b>│</b>\n"
        f"<b>├── [ 🎛 QUICK GUIDE ]</b>\n"
        f"<b>├── 🎵 ⇢ PLAY YOUR FAVOURITE SONGS</b>\n"
        f"<b>├── 🎧 ⇢ SIT BACK & ENJOY THE MUSIC</b>\n"
        f"<b>│</b>\n"
        f"<b>╰── ✦ POWERED BY {settings.BOT_USERNAME}</b>"
        f"</blockquote>\n\n"
        f"👋 <b>Hey {user.first_name if user else 'there'}!</b>\n"
        f"Welcome to <b>{settings.BOT_NAME}</b> — your high-performance Telegram Voice Chat Music Player.\n\n"
        f"✨ <i>Add me to your group, open voice chat, and use <code>/play &lt;song&gt;</code> to start listening!</i>"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"➕ Add {settings.BOT_NAME} to Group", url=f"https://t.me/{settings.BOT_USERNAME.replace('@', '')}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("📚 Help & Commands", callback_data="cb_help_main"),
            InlineKeyboardButton("ℹ️ About", callback_data="cb_about"),
        ],
        [
            InlineKeyboardButton("⭐ Premium Plans", callback_data="cb_premium_plans"),
            InlineKeyboardButton("⚙️ Personal Settings", callback_data="cb_user_settings"),
        ]
    ])

    await message.reply_text(start_text, reply_markup=buttons, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


@rate_limit("command", 1.0)
async def help_command(client, message: Message):
    help_text = (
        f"<blockquote>"
        f"🎧 <b>╭─[ 📚 COMMAND MANUAL ]</b>\n"
        f"<b>│</b>\n"
        f"<b>├── 🎵 /play &lt;song/url&gt; ⇢ Play in Voice Chat</b>\n"
        f"<b>├── ⏸ /pause ⇢ Pause current playback</b>\n"
        f"<b>├── ▶️ /resume ⇢ Resume current track</b>\n"
        f"<b>├── ⏭ /skip ⇢ Skip to next track</b>\n"
        f"<b>├── ⏹ /stop ⇢ Stop & clear queue</b>\n"
        f"<b>├── 📋 /queue ⇢ View queued tracks</b>\n"
        f"<b>├── 🔊 /volume &lt;0-200&gt; ⇢ Adjust volume</b>\n"
        f"<b>├── 🔂 /loop ⇢ Loop single song</b>\n"
        f"<b>├── 🔁 /loopqueue ⇢ Loop entire queue</b>\n"
        f"<b>├── 📻 /autoplay ⇢ Smart autoplay</b>\n"
        f"<b>├── 🎛 /equalizer ⇢ Sound presets</b>\n"
        f"<b>├── ⚡ /player ⇢ Open interactive UI</b>\n"
        f"<b>│</b>\n"
        f"<b>╰── ✦ {settings.BOT_NAME.upper()}</b>"
        f"</blockquote>"
    )
    await message.reply_text(help_text, parse_mode=ParseMode.HTML)


@rate_limit("command", 1.0)
async def about_command(client, message: Message):
    about_text = (
        f"<blockquote>"
        f"🎧 <b>╭─[ ℹ️ ABOUT {settings.BOT_NAME.upper()} ]</b>\n"
        f"<b>│</b>\n"
        f"<b>├── 🤖 ⇢ NAME : {settings.BOT_NAME}</b>\n"
        f"<b>├── 🆔 ⇢ BOT : {settings.BOT_USERNAME}</b>\n"
        f"<b>├── ⚡ ⇢ ENGINE : PyTgCalls 3.0 + FFmpeg</b>\n"
        f"<b>├── 🌐 ⇢ SOURCES : YouTube • Spotify • SoundCloud</b>\n"
        f"<b>├── 🛡 ⇢ FRAMEWORK : Kurigram Layer 229</b>\n"
        f"<b>│</b>\n"
        f"<b>╰── ✦ HIGH QUALITY TELEGRAM AUDIO</b>"
        f"</blockquote>\n\n"
        f"💡 <i>Tip: Add me to your group and start a voice chat to begin!</i>"
    )
    await message.reply_text(about_text, parse_mode=ParseMode.HTML)
