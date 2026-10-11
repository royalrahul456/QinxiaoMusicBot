"""
Qinxiao Music Bot (@QinxiaoMusicBot)
"""
import asyncio
import shutil

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass

__version__ = "1.0.0"
__author__ = "Qinxiao Team"
__bot_name__ = "Qinxiao Music"
__bot_username__ = "@QinxiaoMusicBot"
