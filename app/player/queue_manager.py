import time
import random
import asyncio
from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field

from app.config.settings import settings
from app.providers.base import SongMetadata


class LoopMode(str, Enum):
    OFF = "off"
    TRACK = "track"
    QUEUE = "queue"


@dataclass
class QueueItem:
    song: SongMetadata
    requested_by_id: int
    requested_by_name: str
    added_at: float = field(default_factory=time.monotonic)


class GroupQueue:
    def __init__(self, chat_id: int, max_size: int = 50):
        self.chat_id = chat_id
        self.max_size = max_size
        self.items: List[QueueItem] = []
        self.current_item: Optional[QueueItem] = None
        self.loop_mode: LoopMode = LoopMode.OFF
        self.autoplay: bool = False
        self.volume: int = settings.DEFAULT_VOLUME
        self.quality: str = settings.DEFAULT_QUALITY
        self.bitrate: str = settings.DEFAULT_BITRATE
        self.equalizer: str = "off"
        self.bass_boost: int = 0
        self.normalize: bool = False
        self.active_player_message_id: Optional[int] = None
        self.lock = asyncio.Lock()

    async def add(self, item: QueueItem, allow_duplicate: bool = False) -> Tuple[bool, str]:
        async with self.lock:
            if len(self.items) >= self.max_size:
                return False, f"Queue limit ({self.max_size}) reached."

            if not allow_duplicate:
                for existing in self.items:
                    if existing.song.song_id == item.song.song_id:
                        return False, "This song is already in the queue."

            self.items.append(item)
            return True, "Added to queue."

    async def get_next(self) -> Optional[QueueItem]:
        async with self.lock:
            if self.loop_mode == LoopMode.TRACK and self.current_item:
                return self.current_item

            if self.loop_mode == LoopMode.QUEUE and self.current_item:
                self.items.append(self.current_item)

            if not self.items:
                self.current_item = None
                return None

            self.current_item = self.items.pop(0)
            return self.current_item

    async def remove(self, index: int) -> Optional[QueueItem]:
        async with self.lock:
            if 0 <= index < len(self.items):
                return self.items.pop(index)
            return None

    async def clear(self) -> int:
        async with self.lock:
            count = len(self.items)
            self.items.clear()
            return count

    async def shuffle(self) -> bool:
        async with self.lock:
            if len(self.items) <= 1:
                return False
            random.shuffle(self.items)
            return True

    def get_queue_list(self) -> List[QueueItem]:
        return list(self.items)


class QueueManager:
    def __init__(self):
        self._queues: Dict[int, GroupQueue] = {}
        self._lock = asyncio.Lock()

    async def get_queue(self, chat_id: int) -> GroupQueue:
        async with self._lock:
            if chat_id not in self._queues:
                self._queues[chat_id] = GroupQueue(chat_id=chat_id, max_size=settings.MAX_QUEUE_SIZE)
            return self._queues[chat_id]

    async def remove_queue(self, chat_id: int) -> None:
        async with self._lock:
            if chat_id in self._queues:
                del self._queues[chat_id]


queue_manager = QueueManager()
