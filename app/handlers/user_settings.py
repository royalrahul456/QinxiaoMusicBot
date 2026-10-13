from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.middleware.anti_spam import rate_limit
from app.database.session import get_session
from app.repositories.user_repo import UserRepository
from app.repositories.premium_repo import PremiumRepository
from app.utils.formatting import format_duration
from app.utils.time import format_uptime


@rate_limit("command", 1.0)
async def profile_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        prem_repo = PremiumRepository(session)

        usr_db = await user_repo.get_or_create(user.id, user.username, user.first_name)
        sub = await prem_repo.get_subscription(user.id, "user")

    prem_status = f"✨ **{sub.plan_name.title()} Plan** (Expires {sub.expires_at.strftime('%Y-%m-%d')})" if sub else "🆓 Free User"

    text = (
        f"👤 **Qingxiao Music User Profile**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"👤 **Name:** `{usr_db.first_name or 'User'}`\n"
        f"🏷 **Username:** `@{usr_db.username or 'N/A'}`\n"
        f"💎 **Subscription:** {prem_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Plays:** `{usr_db.total_play_count}` tracks\n"
        f"⏱ **Listening Time:** `{format_uptime(int(usr_db.total_listening_time))}`\n"
        f"⚙️ **Default Quality:** `{usr_db.default_quality.title()}` | **Vol:** `{usr_db.default_volume}%`\n"
        f"🎧 **Preferred Source:** `{usr_db.preferred_source.title()}`"
    )
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def mystats_command(client, message: Message):
    await profile_command(client, message)


@rate_limit("command", 1.0)
async def history_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        hist = await user_repo.get_history(user.id, limit=15)

    if not hist:
        return await message.reply_text("📜 You have no recently played history on Qingxiao Music.")

    text = f"📜 **Your Qingxiao Play History**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, h in enumerate(hist, start=1):
        text += f"`{idx}.` [{h.title}]({h.url}) - `{h.artist}` (`{format_duration(h.duration)}`)\n"

    await message.reply_text(text, disable_web_page_preview=True)


@rate_limit("command", 1.0)
async def settings_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        usr_db = await user_repo.get_or_create(user.id, user.username, user.first_name)

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🌐 Quality: {usr_db.default_quality.title()}", callback_data="cb_set_usr_quality"),
            InlineKeyboardButton(f"🔊 Vol: {usr_db.default_volume}%", callback_data="cb_set_usr_vol"),
        ],
        [
            InlineKeyboardButton(f"🎧 Source: {usr_db.preferred_source.title()}", callback_data="cb_set_usr_source"),
            InlineKeyboardButton(f"📻 Autoplay: {'On' if usr_db.autoplay else 'Off'}", callback_data="cb_set_usr_autoplay"),
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="cb_player_close"),
        ]
    ])

    text = f"⚙️ **Personal Settings for Qingxiao Music (@QinxiaoMusicBot)**"
    await message.reply_text(text, reply_markup=buttons)
