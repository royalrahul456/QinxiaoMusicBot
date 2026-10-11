from pyrogram import filters
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

    caption = (
        f"🎵 **Welcome to Qinxiao Music!** (@QinxiaoMusicBot)\n\n"
        f"Hello {user.first_name if user else 'there'}! I am **Qinxiao Music**, your high-quality Telegram Music Bot.\n\n"
        f"✨ **Key Features:**\n"
        f"• High quality voice-chat audio streaming\n"
        f"• Search YouTube, Spotify metadata & SoundCloud\n"
        f"• Smart Queue, Loop, Autoplay & Equalizer\n"
        f"• Synchronized Lyrics & Favorites\n"
        f"• Multi-tier Premium System & 24/7 Mode\n\n"
        f"Use the buttons below or send `/help` to view all available commands."
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Qinxiao Music to Group", url=f"https://t.me/{settings.BOT_USERNAME.replace('@', '')}?startgroup=true"),
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

    await message.reply_text(caption, reply_markup=buttons, disable_web_page_preview=True)


@rate_limit("command", 1.0)
async def help_command(client, message: Message):
    help_text = (
        f"📚 **Qinxiao Music (@QinxiaoMusicBot) Command Guide**\n\n"
        f"🎵 **Music Commands:**\n"
        f"• `/play <query/URL>` - Search and play music\n"
        f"• `/search <query>` - Interactive music search\n"
        f"• `/yt <query>` - Search & play from YouTube\n"
        f"• `/spotify <query>` - Search Spotify metadata\n"
        f"• `/soundcloud <query>` - Search SoundCloud\n"
        f"• `/playlist <url>` - Play supported playlists\n"
        f"• `/recommend` - Play music recommendations\n"
        f"• `/trending` - Play top trending music\n"
        f"• `/pause` / `/resume` - Pause or resume playback\n"
        f"• `/skip` - Skip current track\n"
        f"• `/stop` - Stop music & clear queue\n"
        f"• `/replay` - Restart current track\n"
        f"• `/seek <seconds>` - Jump to timestamp\n"
        f"• `/volume <0-200>` - Set playback volume\n"
        f"• `/mute` / `/unmute` - Mute/unmute audio\n\n"
        f"📋 **Queue Commands:**\n"
        f"• `/queue` - Show current queue\n"
        f"• `/nowplaying` - Show currently playing song\n"
        f"• `/shuffle` - Shuffle current queue\n"
        f"• `/clear` - Clear all queued songs\n"
        f"• `/loop` - Enable/disable track loop\n"
        f"• `/loopqueue` - Enable/disable queue loop\n"
        f"• `/autoplay` - Toggle autoplay recommendations\n\n"
        f"🎛 **Audio & Settings:**\n"
        f"• `/quality` - Select audio quality\n"
        f"• `/bitrate` - Select bitrate (64k-320k)\n"
        f"• `/equalizer` - Set EQ preset (rock, pop, jazz, etc.)\n"
        f"• `/bassboost` - Toggle bass boost\n"
        f"• `/normalizer` - Toggle volume normalization\n"
        f"• `/player` - Open interactive player UI\n"
        f"• `/247` - Toggle 24/7 voice chat presence\n"
        f"• `/autoleave` - Toggle auto-leave when empty\n"
    )
    await message.reply_text(help_text)


@rate_limit("command", 1.0)
async def about_command(client, message: Message):
    about_text = (
        f"ℹ️ **About Qinxiao Music (@QinxiaoMusicBot)**\n\n"
        f"**Qinxiao Music** is a next-generation Telegram Music Bot built for high-performance audio playback in voice chats.\n\n"
        f"• **Version:** `1.0.0`\n"
        f"• **Identity:** `@QinxiaoMusicBot`\n"
        f"• **Audio Engine:** PyTgCalls + FFmpeg Real-Time Filter Engine\n"
        f"• **Database:** SQLAlchemy Async + SQLite/PostgreSQL\n"
        f"• **Providers:** YouTube, Spotify Metadata, SoundCloud\n"
    )
    await message.reply_text(about_text)
