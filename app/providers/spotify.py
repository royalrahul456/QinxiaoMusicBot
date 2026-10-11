import asyncio
import logging
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.config.settings import settings
from app.providers.base import BaseMusicProvider, SongMetadata

logger = logging.getLogger("QinxiaoMusic.Providers.Spotify")


class SpotifyProvider(BaseMusicProvider):
    def __init__(self):
        self._sp: Optional[spotipy.Spotify] = None
        self._init_spotify()

    def _init_spotify(self):
        if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
            try:
                auth = SpotifyClientCredentials(
                    client_id=settings.SPOTIFY_CLIENT_ID,
                    client_secret=settings.SPOTIFY_CLIENT_SECRET
                )
                self._sp = spotipy.Spotify(auth_manager=auth)
                logger.info("Spotify Provider initialized with Client Credentials.")
            except Exception as e:
                logger.warning(f"Failed to initialize Spotify credentials: {e}")
                self._sp = None

    @property
    def provider_name(self) -> str:
        return "spotify"

    async def search(self, query: str, limit: int = 5) -> List[SongMetadata]:
        if not self._sp:
            logger.debug("Spotify client credentials missing. Skipping Spotify direct API search.")
            return []

        loop = asyncio.get_event_loop()

        def _search():
            try:
                res = self._sp.search(q=query, limit=limit, type="track")
                tracks = res.get("tracks", {}).get("items", [])
                results = []
                for item in tracks:
                    title = item.get("name", "Unknown Track")
                    artists = ", ".join([a.get("name") for a in item.get("artists", []) if a.get("name")])
                    duration = int(item.get("duration_ms", 0) / 1000)
                    url = item.get("external_urls", {}).get("spotify", "")
                    album_obj = item.get("album", {})
                    album_name = album_obj.get("name")
                    images = album_obj.get("images", [])
                    thumbnail = images[0].get("url") if images else None

                    results.append(SongMetadata(
                        song_id=f"sp_{item.get('id')}",
                        title=title,
                        artist=artists or "Spotify Artist",
                        duration=duration,
                        url=url,
                        thumbnail=thumbnail,
                        source="spotify",
                        album=album_name
                    ))
                return results
            except Exception as e:
                logger.error(f"Spotify search error: {e}")
                return []

        return await loop.run_in_executor(None, _search)

    async def extract_stream(self, url_or_id: str) -> Optional[SongMetadata]:
        # Spotify does not provide raw stream URLs directly without DRM.
        # Spotify metadata is extracted and returned as metadata.
        # Stream URL resolution is delegated to audio resolution pipeline.
        return None

    async def get_playlist(self, url: str, limit: int = 50) -> List[SongMetadata]:
        if not self._sp:
            return []

        loop = asyncio.get_event_loop()

        def _playlist():
            try:
                if "playlist" in url:
                    res = self._sp.playlist_items(url, limit=limit)
                    items = res.get("items", [])
                elif "album" in url:
                    res = self._sp.album_tracks(url, limit=limit)
                    items = [{"track": t} for t in res.get("items", [])]
                else:
                    return []

                results = []
                for entry in items:
                    track = entry.get("track")
                    if not track:
                        continue
                    title = track.get("name")
                    artists = ", ".join([a.get("name") for a in track.get("artists", []) if a.get("name")])
                    duration = int(track.get("duration_ms", 0) / 1000)
                    track_url = track.get("external_urls", {}).get("spotify", "")

                    results.append(SongMetadata(
                        song_id=f"sp_{track.get('id')}",
                        title=title,
                        artist=artists,
                        duration=duration,
                        url=track_url,
                        source="spotify"
                    ))
                return results
            except Exception as e:
                logger.error(f"Spotify playlist error: {e}")
                return []

        return await loop.run_in_executor(None, _playlist)
