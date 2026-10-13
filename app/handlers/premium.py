from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.premium.manager import premium_manager, PREMIUM_PLANS
from app.permissions.checker import is_owner
from app.database.session import get_session
from app.repositories.premium_repo import PremiumRepository


@rate_limit("command", 1.0)
async def premium_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        sub = await PremiumRepository(session).get_subscription(user.id, "user")

    if sub:
        text = (
            f"✨ **Qingxiao Premium Active**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Plan: `{sub.plan_name.title()}`\n"
            f"Activated On: `{sub.activated_at.strftime('%Y-%m-%d')}`\n"
            f"Expires On: `{sub.expires_at.strftime('%Y-%m-%d %H:%M UTC')}`"
        )
    else:
        text = (
            f"🆓 **Qingxiao Free Account**\n\n"
            f"Upgrade to Qingxiao Premium to unlock:\n"
            f"• 24/7 continuous voice chat playback\n"
            f"• Maximum queue limit up to 500 tracks\n"
            f"• High quality 320k audio streams & custom EQ\n"
            f"• Unlimited autoplay recommendations\n\n"
            f"Use `/plans` to check available plans or `/activate <key>` to redeem!"
        )

    await message.reply_text(text)


@rate_limit("command", 1.0)
async def plans_command(client, message: Message):
    text = f"⭐ **Qingxiao Music Premium Plans**\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for code, p in PREMIUM_PLANS.items():
        text += (
            f"✨ **{p['name']}** (`{code}`)\n"
            f"• Duration: `{p['duration']} days`\n"
            f"• Max Queue: `{p['max_queue']} songs`\n"
            f"• 24/7 Access: `Included`\n\n"
        )
    text += "Contact bot owner to purchase activation keys or redeem via `/activate <key>`!"
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def activate_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/activate <your_premium_key>`")

    key_str = message.command[1].strip()
    async with get_session() as session:
        success, msg_text = await premium_manager.activate(session, key_str, user.id)

    await message.reply_text(msg_text)


@rate_limit("command", 1.0)
async def myplan_command(client, message: Message):
    await premium_command(client, message)


# Owner-Only Commands
@rate_limit("command", 1.0)
async def genkey_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    plan = message.command[1].lower() if len(message.command) > 1 else "standard"
    if plan not in PREMIUM_PLANS:
        valid_plans = ", ".join(f"`{k}`" for k in PREMIUM_PLANS.keys())
        return await message.reply_text(f"❌ Invalid plan `{plan}`. Choose from: {valid_plans}")

    default_duration = PREMIUM_PLANS[plan]["duration"]
    if len(message.command) > 2:
        try:
            duration = int(message.command[2])
            if duration < 1 or duration > 3650:
                raise ValueError
        except ValueError:
            return await message.reply_text("❌ Invalid duration. Please specify between 1 and 3650 days.")
    else:
        duration = default_duration

    async with get_session() as session:
        key_obj = await premium_manager.generate_key(session, user.id, plan, duration)

    text = (
        f"🔑 **Generated Premium Key**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Key: `{key_obj.key}`\n"
        f"Plan: `{key_obj.plan_name.title()}`\n"
        f"Duration: `{key_obj.duration_days} days`\n\n"
        f"Redeem via: `/activate {key_obj.key}`"
    )
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def revokekey_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/revokekey <key>`")

    key_str = message.command[1].strip()
    async with get_session() as session:
        revoked = await premium_manager.revoke(session, key_str)

    if revoked:
        await message.reply_text(f"🗑 **Key `{key_str}` successfully revoked.**")
    else:
        await message.reply_text("❌ Key not found.")
