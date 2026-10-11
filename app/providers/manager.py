import logging
from typing import List, Optional, Dict
from app.providers.base import BaseMusicProvider, SongMetadata
from app.providers.youtube import YouTubeProvider
from app.providers.spotify import SpotifyProvider
from app.providers.soundcloud import SoundCloudProvider
from app.cache.redis_cache import cache
from app.utils.validators import get_url_provider_type

logger = logging.getLogger("QinxiaoMusic.Providers.Manager")


class ProviderManager:
    def __init__(self):
        self.youtube = YouTubeProvider()
        self.spotify = SpotifyProvider()
        self.soundcloud = SoundCloudProvider()
        self._providers: Dict[str, BaseMusicProvider] = {
            "youtube": self.youtube,
            "spotify": self.spotify,
            "soundcloud": self.soundcloud,
        }

    async def search(self, query: str, provider_name: str = "auto", limit: int = 5) -> List[SongMetadata]:
        cache_key = f"search:{provider_name}:{query}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return [SongMetadata.from_dict(d) for d in cached]

        results: List[SongMetadata] = []
        p_name = provider_name.lower()

        if p_name == "auto":
            detected = get_url_provider_type(query)
            if detected in self._providers:
                p_name = detected

        if p_name in self._providers:
            results = await self._providers[p_name].search(query, limit=limit)
        else:
            # Auto / default order: YouTube -> Spotify -> SoundCloud
            results = await self.youtube.search(query, limit=limit)
            if not results and self.spotify:
                results = await self.spotify.search(query, limit=limit)
            if not results:
                results = await self.soundcloud.search(query, limit=limit)

        if results:
            await cache.set(cache_key, [r.to_dict() for r in results], ttl=600)

        return results

    async def get_playlist(self, url: str, limit: int = 50) -> List[SongMetadata]:
        p_type = get_url_provider_type(url)
        if p_type == "youtube":
            return await self.youtube.get_playlist(url, limit=limit)
        elif p_type == "spotify":
            return await self.spotify.get_playlist(url, limit=limit)
        elif p_type == "soundcloud":
            return await self.soundcloud.get_playlist(url, limit=limit)
        return []

    async def resolve_stream(self, meta: SongMetadata) -> Optional[SongMetadata]:
        """Ensure SongMetadata has a valid direct stream URL."""
        if meta.stream_url:
            return meta

        cache_key = f"stream:{meta.song_id}"
        cached = await cache.get(cache_key)
        if cached:
            meta.stream_url = cached
            return meta

        resolved: Optional[SongMetadata] = None

        if meta.source == "youtube" or get_url_provider_type(meta.url) == "youtube":
            resolved = await self.youtube.extract_stream(meta.url)
        elif meta.source == "soundcloud" or get_url_provider_type(meta.url) == "soundcloud":
            resolved = await self.soundcloud.extract_stream(meta.url)

        if not resolved or not resolved.stream_url:
            # Fallback for Spotify or unresolvable URLs: search YouTube by Title + Artist
            search_query = f"{meta.title} {meta.artist}"
            logger.info(f"Resolving stream via YouTube search fallback for '{search_query}'")
            yt_results = await self.youtube.search(search_query, limit=1)
            if yt_results:
                resolved = await self.youtube.extract_stream(yt_results[0].url)

        if resolved and resolved.stream_url:
            meta.stream_url = resolved.stream_url
            if not meta.thumbnail:
                meta.thumbnail = resolved.thumbnail
            if resolved.duration and not meta.duration:
                meta.duration = resolved.duration
            await cache.set(cache_key, meta.stream_url, ttl=3600)
            return meta

        return None

    async def get_recommendations(self, meta: SongMetadata, limit: int = 5) -> List[SongMetadata]:
        query = f"{meta.artist} {meta.title} similar tracks"
        return await self.search(query, provider_name="youtube", limit=limit)

    async def get_trending(self, limit: int = 10) -> List[SongMetadata]:
        return await self.search("trending music top hits", provider_name="youtube", limit=limit)


provider_manager = ProviderManager()
