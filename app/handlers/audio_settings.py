from pyrogram import filters
from pyrogram.types import Message

from app.middleware.anti_spam import rate_limit
from app.player.queue_manager import queue_manager
from app.player.vc_client import vc_client
from app.permissions.checker import is_admin
from app.database.session import get_session
from app.audio.quality import EQUALIZER_PRESETS, VALID_BITRATES


async def _require_group_admin(client, message: Message) -> bool:
    if message.chat.id > 0:
        return True
    user = message.from_user
    async with get_session() as session:
        return await is_admin(client, message.chat.id, user.id if user else 0, session)


@rate_limit("command", 1.0)
async def quality_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if len(message.command) < 2:
        return await message.reply_text(
            f"🌐 **Current Audio Quality:** `{queue.quality.title()}` (Bitrate: `{queue.bitrate}`)\n\n"
            f"Available options:\n• `/quality low` (64k)\n• `/quality medium` (128k)\n• `/quality high` (320k)"
        )

    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change audio quality.")

    val = message.command[1].lower()
    mapping = {"low": "64k", "medium": "128k", "high": "320k"}
    if val not in mapping:
        return await message.reply_text("❌ Invalid quality profile. Options: `low`, `medium`, `high`.")

    queue.quality = val
    queue.bitrate = mapping[val]
    await message.reply_text(f"🌐 **Audio quality updated to:** `{val.title()}` ({queue.bitrate})")


@rate_limit("command", 1.0)
async def bitrate_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if len(message.command) < 2:
        return await message.reply_text(
            f"🎵 **Current Bitrate:** `{queue.bitrate}`\n\n"
            f"Supported bitrates: `64k`, `128k`, `192k`, `256k`, `320k`\n"
            f"Example: `/bitrate 320k`"
        )

    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change bitrate.")

    val = message.command[1].lower()
    if not val.endswith("k"):
        val += "k"

    if val not in VALID_BITRATES:
        return await message.reply_text(f"❌ Invalid bitrate. Choose from: {', '.join(VALID_BITRATES)}")

    queue.bitrate = val
    await message.reply_text(f"🎵 **Bitrate set to:** `{val}`")


@rate_limit("command", 1.0)
async def equalizer_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if len(message.command) < 2:
        presets = ", ".join([f"`{p}`" for p in EQUALIZER_PRESETS.keys()])
        return await message.reply_text(
            f"🎛 **Current Equalizer:** `{queue.equalizer.title()}`\n\n"
            f"Available EQ Presets: {presets}\n"
            f"Example: `/equalizer rock`"
        )

    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change equalizer settings.")

    preset = message.command[1].lower()
    if preset not in EQUALIZER_PRESETS:
        return await message.reply_text("❌ Invalid EQ preset name.")

    queue.equalizer = preset
    await message.reply_text(f"🎛 **Equalizer preset set to:** `{preset.title()}`")


@rate_limit("command", 1.0)
async def bassboost_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    if len(message.command) < 2:
        level = queue.bass_boost
        status = f"Level {level}" if level > 0 else "Off"
        return await message.reply_text(
            f"⚡ **Current Bass Boost:** `{status}`\n"
            f"Use `/bassboost <0-10>` to set level (0 = off)."
        )

    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can change bass boost.")

    try:
        level = int(message.command[1])
        if level < 0 or level > 10:
            return await message.reply_text("❌ Level must be between 0 and 10.")

        queue.bass_boost = level
        status = f"Level {level}" if level > 0 else "Off"
        await message.reply_text(f"⚡ **Bass Boost set to:** `{status}`")
    except ValueError:
        await message.reply_text("❌ Invalid level number.")


@rate_limit("command", 1.0)
async def normalizer_command(client, message: Message):
    if not await _require_group_admin(client, message):
        return await message.reply_text("❌ Only group administrators can toggle audio normalization.")

    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    queue.normalize = not queue.normalize
    status = "Enabled" if queue.normalize else "Disabled"
    await message.reply_text(f"🔊 **Audio Normalization (Loudnorm):** `{status}`")


@rate_limit("command", 1.0)
async def audioinfo_command(client, message: Message):
    chat_id = message.chat.id
    queue = await queue_manager.get_queue(chat_id)

    info = (
        f"📊 **Qinxiao Music Audio Information**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔊 **Volume:** `{queue.volume}%`\n"
        f"🌐 **Quality Profile:** `{queue.quality.title()}`\n"
        f"🎵 **Bitrate:** `{queue.bitrate}`\n"
        f"🎛 **Equalizer:** `{queue.equalizer.title()}`\n"
        f"⚡ **Bass Boost:** `{queue.bass_boost}/10`\n"
        f"🔊 **Normalization:** `{'On' if queue.normalize else 'Off'}`\n"
        f"📻 **Sample Rate:** `48000 Hz (Stereo)`\n"
        f"🔌 **VC Status:** `{'Connected' if vc_client.is_connected(chat_id) else 'Disconnected'}`"
    )
    await message.reply_text(info)
