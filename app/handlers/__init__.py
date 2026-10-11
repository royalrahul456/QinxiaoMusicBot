from pyrogram import filters
from pyrogram.handlers import MessageHandler, InlineQueryHandler

from app.handlers.start import start_command, help_command, about_command
from app.handlers.play import (
    play_command,
    pause_command,
    resume_command,
    skip_command,
    stop_command,
    volume_command,
)
from app.handlers.queue import (
    queue_command,
    nowplaying_command,
    shuffle_command,
    clear_command,
    loop_command,
    loopqueue_command,
    autoplay_command,
)
from app.handlers.audio_settings import (
    quality_command,
    bitrate_command,
    equalizer_command,
    bassboost_command,
    normalizer_command,
    audioinfo_command,
)
from app.handlers.lyrics import lyrics_command, syncedlyrics_command
from app.handlers.favorites import fav_command, unfav_command, favorites_command
from app.handlers.user_settings import profile_command, mystats_command, history_command, settings_command
from app.handlers.group_settings import join_command, leave_command, vc_command, player_command, toggle_247_command, autoleave_command
from app.handlers.inline import inline_search_handler
from app.handlers.statistics import top_command, topsongs_command, topartists_command, groupstats_command, listeningtime_command
from app.handlers.premium import premium_command, plans_command, activate_command, myplan_command, genkey_command, revokekey_command
from app.handlers.owner import (
    broadcast_command,
    botstats_command,
    activevc_command,
    leaveall_command,
    maintenance_command,
    restart_command,
    cache_command,
    clearcache_command,
    speedtest_command,
    addsudo_command,
    delsudo_command,
    sudolist_command,
)


def register_all_handlers(app):
    """Register all Pyrogram message and inline handlers for Qinxiao Music."""
    # Start / Help / About
    app.add_handler(MessageHandler(start_command, filters.command("start")))
    app.add_handler(MessageHandler(help_command, filters.command("help")))
    app.add_handler(MessageHandler(about_command, filters.command("about")))

    # Playback & Controls
    app.add_handler(MessageHandler(play_command, filters.command(["play", "search", "yt", "spotify", "soundcloud", "playlist", "artist", "album", "recommend", "trending"])))
    app.add_handler(MessageHandler(pause_command, filters.command("pause")))
    app.add_handler(MessageHandler(resume_command, filters.command("resume")))
    app.add_handler(MessageHandler(skip_command, filters.command("skip")))
    app.add_handler(MessageHandler(stop_command, filters.command("stop")))
    app.add_handler(MessageHandler(volume_command, filters.command(["volume", "vol"])))

    # Queue
    app.add_handler(MessageHandler(queue_command, filters.command("queue")))
    app.add_handler(MessageHandler(nowplaying_command, filters.command(["nowplaying", "np"])))
    app.add_handler(MessageHandler(shuffle_command, filters.command("shuffle")))
    app.add_handler(MessageHandler(clear_command, filters.command("clear")))
    app.add_handler(MessageHandler(loop_command, filters.command("loop")))
    app.add_handler(MessageHandler(loopqueue_command, filters.command("loopqueue")))
    app.add_handler(MessageHandler(autoplay_command, filters.command("autoplay")))

    # Audio & Quality
    app.add_handler(MessageHandler(quality_command, filters.command("quality")))
    app.add_handler(MessageHandler(bitrate_command, filters.command("bitrate")))
    app.add_handler(MessageHandler(equalizer_command, filters.command(["equalizer", "eq"])))
    app.add_handler(MessageHandler(bassboost_command, filters.command(["bassboost", "bass"])))
    app.add_handler(MessageHandler(normalizer_command, filters.command(["normalizer", "loudnorm"])))
    app.add_handler(MessageHandler(audioinfo_command, filters.command("audioinfo")))

    # Lyrics & Favorites
    app.add_handler(MessageHandler(lyrics_command, filters.command("lyrics")))
    app.add_handler(MessageHandler(syncedlyrics_command, filters.command("syncedlyrics")))
    app.add_handler(MessageHandler(fav_command, filters.command("fav")))
    app.add_handler(MessageHandler(unfav_command, filters.command("unfav")))
    app.add_handler(MessageHandler(favorites_command, filters.command(["favorites", "favs"])))

    # User & Group Settings
    app.add_handler(MessageHandler(profile_command, filters.command("profile")))
    app.add_handler(MessageHandler(mystats_command, filters.command("mystats")))
    app.add_handler(MessageHandler(history_command, filters.command("history")))
    app.add_handler(MessageHandler(settings_command, filters.command("settings")))
    app.add_handler(MessageHandler(join_command, filters.command("join")))
    app.add_handler(MessageHandler(leave_command, filters.command("leave")))
    app.add_handler(MessageHandler(vc_command, filters.command("vc")))
    app.add_handler(MessageHandler(player_command, filters.command("player")))
    app.add_handler(MessageHandler(toggle_247_command, filters.command("247")))
    app.add_handler(MessageHandler(autoleave_command, filters.command("autoleave")))

    # Statistics
    app.add_handler(MessageHandler(top_command, filters.command("top")))
    app.add_handler(MessageHandler(topsongs_command, filters.command("topsongs")))
    app.add_handler(MessageHandler(topartists_command, filters.command("topartists")))
    app.add_handler(MessageHandler(groupstats_command, filters.command("groupstats")))
    app.add_handler(MessageHandler(listeningtime_command, filters.command("listeningtime")))

    # Premium
    app.add_handler(MessageHandler(premium_command, filters.command("premium")))
    app.add_handler(MessageHandler(plans_command, filters.command("plans")))
    app.add_handler(MessageHandler(activate_command, filters.command("activate")))
    app.add_handler(MessageHandler(myplan_command, filters.command("myplan")))
    app.add_handler(MessageHandler(genkey_command, filters.command("genkey")))
    app.add_handler(MessageHandler(revokekey_command, filters.command("revokekey")))

    # Owner & Sudo
    app.add_handler(MessageHandler(broadcast_command, filters.command("broadcast")))
    app.add_handler(MessageHandler(botstats_command, filters.command("botstats")))
    app.add_handler(MessageHandler(activevc_command, filters.command("activevc")))
    app.add_handler(MessageHandler(leaveall_command, filters.command("leaveall")))
    app.add_handler(MessageHandler(maintenance_command, filters.command("maintenance")))
    app.add_handler(MessageHandler(restart_command, filters.command("restart")))
    app.add_handler(MessageHandler(cache_command, filters.command("cache")))
    app.add_handler(MessageHandler(clearcache_command, filters.command("clearcache")))
    app.add_handler(MessageHandler(speedtest_command, filters.command("speedtest")))
    app.add_handler(MessageHandler(addsudo_command, filters.command("addsudo")))
    app.add_handler(MessageHandler(delsudo_command, filters.command("delsudo")))
    app.add_handler(MessageHandler(sudolist_command, filters.command("sudolist")))

    # Inline Query
    app.add_handler(InlineQueryHandler(inline_search_handler))
