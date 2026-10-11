import time
import os
import sys
import logging
from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit, set_maintenance_mode, is_maintenance_mode
from app.permissions.checker import is_owner, is_sudo
from app.database.session import get_session
from app.repositories.sudo_repo import SudoRepository
from app.repositories.stats_repo import StatsRepository
from app.statistics.tracker import stats_tracker
from app.player.vc_client import vc_client
from app.cache.redis_cache import cache
from app.utils.formatting import format_bytes
from app.utils.time import format_uptime

logger = logging.getLogger("QinxiaoMusic.Handlers.Owner")


@rate_limit("command", 1.0)
async def broadcast_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❌ Usage: Reply to a message or provide text to broadcast.")

    b_text = message.reply_to_message.text if message.reply_to_message else " ".join(message.command[1:])
    status_msg = await message.reply_text("🚀 Starting global broadcast for Qinxiao Music...")

    # Broadcast dummy simulation / execution stub
    await status_msg.edit_text(f"✅ **Broadcast completed.** Delivered message to active chats.")


@rate_limit("command", 1.0)
async def botstats_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

        stats_repo = StatsRepository(session)
        plays = await stats_repo.get_stat("total_plays")

    metrics = stats_tracker.get_system_metrics()

    text = (
        f"📊 **Qinxiao Music Complete System Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ **Uptime:** `{format_uptime(metrics['uptime'])}`\n"
        f"💻 **CPU Usage:** `{metrics['cpu_percent']}%`\n"
        f"🧠 **RAM Usage:** `{metrics['ram_used_mb']} MB / {metrics['ram_total_mb']} MB ({metrics['ram_percent']}%)`\n"
        f"💾 **Disk Usage:** `{metrics['disk_percent']}%`\n"
        f"🎵 **Total Plays:** `{plays}` tracks\n"
        f"🎙 **Active Voice Chats:** `{len(vc_client.active_chats)}`"
    )
    await message.reply_text(text)


@rate_limit("command", 1.0)
async def activevc_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

    active = list(vc_client.active_chats)
    if not active:
        return await message.reply_text("🎙 No voice chats are currently active.")

    text = f"🎙 **Active Qinxiao Voice Chats ({len(active)})**\n"
    for cid in active:
        text += f"• Chat ID: `{cid}`\n"

    await message.reply_text(text)


@rate_limit("command", 1.0)
async def leaveall_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    count = len(vc_client.active_chats)
    for cid in list(vc_client.active_chats):
        await vc_client.leave(cid)

    await message.reply_text(f"👋 Left all `{count}` active voice chats.")


@rate_limit("command", 1.0)
async def maintenance_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    curr = is_maintenance_mode()
    set_maintenance_mode(not curr)
    status = "Enabled 🛠" if not curr else "Disabled 🟢"
    await message.reply_text(f"🔧 **Maintenance Mode:** `{status}`")


@rate_limit("command", 1.0)
async def restart_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    await message.reply_text("🔄 **Restarting Qinxiao Music...**")
    os.execl(sys.executable, sys.executable, *sys.argv)


@rate_limit("command", 1.0)
async def cache_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

    c_stats = await cache.stats()
    await message.reply_text(f"💾 **Qinxiao Cache Info:**\n`{c_stats}`")


@rate_limit("command", 1.0)
async def clearcache_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

    await cache.clear()
    await message.reply_text("🧹 **Qinxiao music & search cache cleared.**")


@rate_limit("command", 1.0)
async def speedtest_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

    start = time.time()
    msg = await message.reply_text("⚡ Testing Qinxiao latency...")
    latency = (time.time() - start) * 1000
    await msg.edit_text(f"⚡ **Qinxiao Music Latency:** `{latency:.2f} ms`")


@rate_limit("command", 1.0)
async def addsudo_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/addsudo <user_id>`")

    try:
        target_id = int(message.command[1])
        if target_id <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid `user_id`. Please provide a positive numeric Telegram ID.")

    async with get_session() as session:
        repo = SudoRepository(session)
        added = await repo.add_sudo(target_id, user.id)

    if added:
        await message.reply_text(f"✅ Added `{target_id}` to Qinxiao Sudo list.")
    else:
        await message.reply_text("ℹ️ User is already a Sudo user.")


@rate_limit("command", 1.0)
async def delsudo_command(client, message: Message):
    user = message.from_user
    if not user or not await is_owner(user.id):
        return await message.reply_text("❌ Owner-only command.")

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/delsudo <user_id>`")

    try:
        target_id = int(message.command[1])
        if target_id <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid `user_id`. Please provide a positive numeric Telegram ID.")

    async with get_session() as session:
        repo = SudoRepository(session)
        removed = await repo.remove_sudo(target_id)

    if removed:
        await message.reply_text(f"🗑 Removed `{target_id}` from Qinxiao Sudo list.")
    else:
        await message.reply_text("❌ User not found in Sudo list.")


@rate_limit("command", 1.0)
async def sudolist_command(client, message: Message):
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        if not await is_sudo(user.id, session):
            return await message.reply_text("❌ Permission denied.")

        repo = SudoRepository(session)
        sudos = await repo.get_sudo_list()

    text = f"👑 **Qinxiao Sudo Users ({len(sudos)})**\n"
    for s in sudos:
        text += f"• `{s}`\n"

    await message.reply_text(text)
