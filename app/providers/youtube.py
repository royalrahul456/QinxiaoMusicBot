import asyncio
import logging
from typing import List, Optional
import yt_dlp

from app.providers.base import BaseMusicProvider, SongMetadata
from app.utils.validators import get_url_provider_type

logger = logging.getLogger("QinxiaoMusic.Providers.YouTube")

YTDL_SEARCH_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": "in_playlist",
    "skip_download": True,
    "default_search": "ytsearch",
    "ignoreerrors": True,
    "source_address": "0.0.0.0",
}

YTDL_STREAM_OPTIONS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "ignoreerrors": True,
    "geo_bypass": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"]
        }
    },
}


class YouTubeProvider(BaseMusicProvider):
    @property
    def provider_name(self) -> str:
        return "youtube"

    async def search(self, query: str, limit: int = 5) -> List[SongMetadata]:
        loop = asyncio.get_event_loop()

        def _fetch():
            is_yt_url = get_url_provider_type(query) == "youtube"
            search_query = query if is_yt_url else f"ytsearch{limit}:{query}"
            with yt_dlp.YoutubeDL(YTDL_SEARCH_OPTIONS) as ytdl:
                info = ytdl.extract_info(search_query, download=False)
                results = []
                if not info:
                    return results

                entries = info.get("entries", [info])
                for entry in entries:
                    if not entry:
                        continue
                    song_id = entry.get("id") or entry.get("url", "")
                    title = entry.get("title", "Unknown Title")
                    artist = entry.get("uploader") or entry.get("artist") or "YouTube Artist"
                    duration = int(entry.get("duration") or 0)
                    url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={song_id}"
                    thumbnail = entry.get("thumbnail")

                    results.append(SongMetadata(
                        song_id=f"yt_{song_id}",
                        title=title,
                        artist=artist,
                        duration=duration,
                        url=url,
                        thumbnail=thumbnail,
                        source="youtube"
                    ))
                return results

        try:
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.error(f"YouTube search error for '{query}': {e}")
            return []

    async def extract_stream(self, url_or_id: str) -> Optional[SongMetadata]:
        loop = asyncio.get_event_loop()

        def _extract():
            target_url = url_or_id
            if url_or_id.startswith("yt_"):
                song_id = url_or_id.replace("yt_", "")
                target_url = f"https://www.youtube.com/watch?v={song_id}"
            elif get_url_provider_type(target_url) != "youtube":
                return None

            with yt_dlp.YoutubeDL(YTDL_STREAM_OPTIONS) as ytdl:
                info = ytdl.extract_info(target_url, download=False)
                if not info:
                    return None

                # Handle playlist entry if returned single entry
                if "entries" in info:
                    info = info["entries"][0]

                stream_url = info.get("url")
                song_id = info.get("id")
                title = info.get("title", "Unknown Title")
                artist = info.get("uploader") or info.get("artist") or "YouTube Artist"
                duration = int(info.get("duration") or 0)
                web_url = info.get("webpage_url") or target_url
                thumbnail = info.get("thumbnail")

                http_headers = info.get("http_headers") or {}
                return SongMetadata(
                    song_id=f"yt_{song_id}",
                    title=title,
                    artist=artist,
                    duration=duration,
                    url=web_url,
                    stream_url=stream_url,
                    thumbnail=thumbnail,
                    source="youtube",
                    extra_info={"http_headers": http_headers}
                )

        try:
            return await loop.run_in_executor(None, _extract)
        except Exception as e:
            logger.error(f"YouTube stream extraction error for '{url_or_id}': {e}")
            return None

    async def get_playlist(self, url: str, limit: int = 50) -> List[SongMetadata]:
        if get_url_provider_type(url) != "youtube":
            return []

        loop = asyncio.get_event_loop()

        def _playlist():
            opts = dict(YTDL_SEARCH_OPTIONS)
            opts["extract_flat"] = True
            with yt_dlp.YoutubeDL(opts) as ytdl:
                info = ytdl.extract_info(url, download=False)
                results = []
                if not info or "entries" not in info:
                    return results

                for entry in info["entries"][:limit]:
                    if not entry:
                        continue
                    song_id = entry.get("id")
                    title = entry.get("title", "Unknown Track")
                    artist = entry.get("uploader") or "YouTube Playlist"
                    duration = int(entry.get("duration") or 0)
                    web_url = f"https://www.youtube.com/watch?v={song_id}"

                    results.append(SongMetadata(
                        song_id=f"yt_{song_id}",
                        title=title,
                        artist=artist,
                        duration=duration,
                        url=web_url,
                        source="youtube"
                    ))
                return results

        try:
            return await loop.run_in_executor(None, _playlist)
        except Exception as e:
            logger.error(f"YouTube playlist extraction error for '{url}': {e}")
            return []
