import psutil
import time
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats_repo import StatsRepository
from app.repositories.song_repo import SongRepository

_START_TIME = time.time()


class SystemStatsTracker:
    @staticmethod
    def get_uptime_seconds() -> int:
        return int(time.time() - _START_TIME)

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_mb": int(mem.used / (1024 * 1024)),
            "ram_total_mb": int(mem.total / (1024 * 1024)),
            "disk_percent": disk.percent,
            "uptime": SystemStatsTracker.get_uptime_seconds(),
        }

    @staticmethod
    async def get_bot_leaderboards(session: AsyncSession):
        song_repo = SongRepository(session)
        top_songs = await song_repo.get_top_songs(limit=10)
        top_artists = await song_repo.get_top_artists(limit=10)
        return top_songs, top_artists


stats_tracker = SystemStatsTracker()
