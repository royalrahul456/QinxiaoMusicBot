from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class SyncedLine:
    timestamp_ms: int
    text: str


@dataclass
class LyricsResult:
    title: str
    artist: str
    plain_lyrics: str
    synced_lines: List[SyncedLine]
    source: str = "Genius"


class BaseLyricsProvider(ABC):
    @abstractmethod
    async def fetch_lyrics(self, title: str, artist: Optional[str] = None) -> Optional[LyricsResult]:
        pass
