import asyncio
from typing import Set, Dict, Tuple


class VoteSkipTracker:
    def __init__(self):
        # chat_id -> set of user_ids who voted
        self._votes: Dict[int, Set[int]] = {}
        self._lock = asyncio.Lock()

    async def reset(self, chat_id: int) -> None:
        async with self._lock:
            if chat_id in self._votes:
                self._votes[chat_id].clear()

    async def add_vote(self, chat_id: int, user_id: int, total_listeners: int, required_percentage: int = 50) -> Tuple[bool, int, int]:
        """
        Adds a vote to skip.
        Returns: (has_passed, current_votes, needed_votes)
        """
        async with self._lock:
            if chat_id not in self._votes:
                self._votes[chat_id] = set()

            votes_set = self._votes[chat_id]
            votes_set.add(user_id)

            current_votes = len(votes_set)
            listeners = max(1, total_listeners)
            needed_votes = max(1, int((listeners * required_percentage) / 100))

            passed = current_votes >= needed_votes
            return passed, current_votes, needed_votes

    async def get_vote_status(self, chat_id: int, total_listeners: int, required_percentage: int = 50) -> Tuple[int, int]:
        async with self._lock:
            votes_set = self._votes.get(chat_id, set())
            current_votes = len(votes_set)
            listeners = max(1, total_listeners)
            needed_votes = max(1, int((listeners * required_percentage) / 100))
            return current_votes, needed_votes


vote_skip_tracker = VoteSkipTracker()
