from pyrogram.types import CallbackQuery

from app.middleware.anti_spam import rate_limit
from app.database.session import get_session
from app.repositories.user_repo import UserRepository


@rate_limit("callback", 0.5)
async def settings_callback_handler(client, query: CallbackQuery):
    user = query.from_user
    data = query.data

    if data == "cb_help_main":
        await query.answer()
        await query.message.reply_text("📚 Send `/help` in chat for the full command manual.")

    elif data == "cb_about":
        await query.answer()
        await query.message.reply_text("ℹ️ **Qinxiao Music (@QinxiaoMusicBot)** v1.0.0\nHigh performance Telegram Music Bot.")

    elif data == "cb_premium_plans":
        await query.answer()
        await query.message.reply_text("⭐ Send `/plans` to view all available Qinxiao Premium tiers!")

    elif data == "cb_user_settings":
        await query.answer()
        await query.message.reply_text("⚙️ Send `/settings` to manage your personal audio profile.")

    elif data == "cb_set_usr_quality":
        async with get_session() as session:
            repo = UserRepository(session)
            usr = await repo.get_or_create(user.id)
            nxt = "medium" if usr.default_quality == "high" else ("low" if usr.default_quality == "medium" else "high")
            await repo.update_settings(user.id, default_quality=nxt)
        await query.answer(f"🌐 Default quality updated to: {nxt.title()}")

    elif data == "cb_set_usr_vol":
        async with get_session() as session:
            repo = UserRepository(session)
            usr = await repo.get_or_create(user.id)
            nxt_vol = 50 if usr.default_volume >= 150 else usr.default_volume + 25
            await repo.update_settings(user.id, default_volume=nxt_vol)
        await query.answer(f"🔊 Default volume set to: {nxt_vol}%")

    elif data == "cb_set_usr_source":
        sources = ["youtube", "spotify", "soundcloud"]
        async with get_session() as session:
            repo = UserRepository(session)
            usr = await repo.get_or_create(user.id)
            idx = sources.index(usr.preferred_source) if usr.preferred_source in sources else 0
            nxt_src = sources[(idx + 1) % len(sources)]
            await repo.update_settings(user.id, preferred_source=nxt_src)
        await query.answer(f"🎧 Preferred source set to: {nxt_src.title()}")

    elif data == "cb_set_usr_autoplay":
        async with get_session() as session:
            repo = UserRepository(session)
            usr = await repo.get_or_create(user.id)
            nxt_auto = not usr.autoplay
            await repo.update_settings(user.id, autoplay=nxt_auto)
        await query.answer(f"📻 Autoplay {'Enabled' if nxt_auto else 'Disabled'}")

