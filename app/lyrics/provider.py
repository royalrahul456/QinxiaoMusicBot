import aiohttp
import logging
from typing import Optional
from urllib.parse import quote

from app.lyrics.base import BaseLyricsProvider, LyricsResult
from app.lyrics.parser import parse_lrc
from app.cache.redis_cache import cache

logger = logging.getLogger("QinxiaoMusic.Lyrics.Provider")


class LyricsProvider(BaseLyricsProvider):
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_lyrics(self, title: str, artist: Optional[str] = None) -> Optional[LyricsResult]:
        query = f"{artist} - {title}" if artist else title
        cache_key = f"lyrics:{query.lower()}"

        cached = await cache.get(cache_key)
        if cached:
            return LyricsResult(
                title=cached["title"],
                artist=cached["artist"],
                plain_lyrics=cached["plain_lyrics"],
                synced_lines=[],
                source=cached.get("source", "Cache")
            )

        # Primary API fetch (Lyrist / Public API)
        url = f"https://lyrist.vercel.app/api/{quote(title)}/{quote(artist or '')}"
        try:
            session = await self._get_session()
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics_text = data.get("lyrics")
                    if lyrics_text:
                        result = LyricsResult(
                            title=data.get("title", title),
                            artist=data.get("artist", artist or "Unknown"),
                            plain_lyrics=lyrics_text,
                            synced_lines=parse_lrc(lyrics_text),
                            source="Lyrist"
                        )
                        await cache.set(cache_key, {
                            "title": result.title,
                            "artist": result.artist,
                            "plain_lyrics": result.plain_lyrics,
                            "source": result.source
                        }, ttl=86400)
                        return result
        except Exception as e:
            logger.debug(f"Lyrist lyrics API error for '{query}': {e}")

        return None


lyrics_provider = LyricsProvider()
