import asyncio
import logging
from typing import List, Optional
import yt_dlp

from app.providers.base import BaseMusicProvider, SongMetadata
from app.utils.validators import get_url_provider_type

logger = logging.getLogger("QinxiaoMusic.Providers.SoundCloud")

SCL_SEARCH_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
    "default_search": "scsearch",
    "ignoreerrors": True,
}


class SoundCloudProvider(BaseMusicProvider):
    @property
    def provider_name(self) -> str:
        return "soundcloud"

    async def search(self, query: str, limit: int = 5) -> List[SongMetadata]:
        loop = asyncio.get_event_loop()

        def _search():
            is_sc_url = get_url_provider_type(query) == "soundcloud"
            search_query = query if is_sc_url else f"scsearch{limit}:{query}"
            with yt_dlp.YoutubeDL(SCL_SEARCH_OPTIONS) as ytdl:
                info = ytdl.extract_info(search_query, download=False)
                results = []
                if not info:
                    return results

                entries = info.get("entries", [info])
                for entry in entries:
                    if not entry:
                        continue
                    song_id = entry.get("id") or entry.get("url", "")
                    title = entry.get("title", "Unknown SoundCloud Track")
                    artist = entry.get("uploader") or entry.get("artist") or "SoundCloud Artist"
                    duration = int(entry.get("duration") or 0)
                    url = entry.get("webpage_url") or entry.get("url", "")
                    thumbnail = entry.get("thumbnail")

                    results.append(SongMetadata(
                        song_id=f"sc_{song_id}",
                        title=title,
                        artist=artist,
                        duration=duration,
                        url=url,
                        thumbnail=thumbnail,
                        source="soundcloud"
                    ))
                return results

        try:
            return await loop.run_in_executor(None, _search)
        except Exception as e:
            logger.error(f"SoundCloud search error for '{query}': {e}")
            return []

    async def extract_stream(self, url_or_id: str) -> Optional[SongMetadata]:
        if get_url_provider_type(url_or_id) != "soundcloud":
            return None

        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL({"format": "bestaudio/best", "quiet": True}) as ytdl:
                info = ytdl.extract_info(url_or_id, download=False)
                if not info:
                    return None

                stream_url = info.get("url")
                song_id = info.get("id")
                title = info.get("title", "Unknown Track")
                artist = info.get("uploader") or "SoundCloud Artist"
                duration = int(info.get("duration") or 0)
                web_url = info.get("webpage_url") or url_or_id
                thumbnail = info.get("thumbnail")

                return SongMetadata(
                    song_id=f"sc_{song_id}",
                    title=title,
                    artist=artist,
                    duration=duration,
                    url=web_url,
                    stream_url=stream_url,
                    thumbnail=thumbnail,
                    source="soundcloud"
                )

        try:
            return await loop.run_in_executor(None, _extract)
        except Exception as e:
            logger.error(f"SoundCloud extraction error: {e}")
            return None

    async def get_playlist(self, url: str, limit: int = 50) -> List[SongMetadata]:
        return await self.search(url, limit=limit)
