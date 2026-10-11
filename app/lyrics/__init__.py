from app.lyrics.base import BaseLyricsProvider, LyricsResult, SyncedLine
from app.lyrics.parser import parse_lrc
from app.lyrics.provider import lyrics_provider, LyricsProvider

__all__ = [
    "BaseLyricsProvider",
    "LyricsResult",
    "SyncedLine",
    "parse_lrc",
    "lyrics_provider",
    "LyricsProvider",
]
