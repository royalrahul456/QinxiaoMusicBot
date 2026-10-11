from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SongMetadata:
    song_id: str
    title: str
    artist: str
    duration: int  # in seconds
    url: str       # original query/web URL
    stream_url: Optional[str] = None  # direct stream URL extracted
    thumbnail: Optional[str] = None
    source: str = "youtube"  # youtube, spotify, soundcloud
    album: Optional[str] = None
    extra_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "url": self.url,
            "stream_url": self.stream_url,
            "thumbnail": self.thumbnail,
            "source": self.source,
            "album": self.album,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SongMetadata":
        return cls(**d)


class BaseMusicProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[SongMetadata]:
        pass

    @abstractmethod
    async def extract_stream(self, url_or_id: str) -> Optional[SongMetadata]:
        pass

    @abstractmethod
    async def get_playlist(self, url: str, limit: int = 50) -> List[SongMetadata]:
        pass
