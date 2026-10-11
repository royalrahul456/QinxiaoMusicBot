import pytest
from app.player.queue_manager import GroupQueue, QueueItem, LoopMode
from app.providers.base import SongMetadata


@pytest.mark.asyncio
async def test_queue_add_and_get_next():
    queue = GroupQueue(chat_id=-100123456789, max_size=5)

    song1 = SongMetadata(song_id="yt_1", title="Song 1", artist="Artist 1", duration=200, url="http://song1.com")
    song2 = SongMetadata(song_id="yt_2", title="Song 2", artist="Artist 2", duration=180, url="http://song2.com")

    item1 = QueueItem(song=song1, requested_by_id=111, requested_by_name="Alice")
    item2 = QueueItem(song=song2, requested_by_id=222, requested_by_name="Bob")

    # Add items
    added1, _ = await queue.add(item1)
    added2, _ = await queue.add(item2)

    assert added1 is True
    assert added2 is True
    assert len(queue.items) == 2

    # Duplicate check
    added_dup, msg = await queue.add(item1, allow_duplicate=False)
    assert added_dup is False
    assert "already in the queue" in msg

    # Get next item
    next_item = await queue.get_next()
    assert next_item.song.song_id == "yt_1"
    assert queue.current_item.song.song_id == "yt_1"
    assert len(queue.items) == 1


@pytest.mark.asyncio
async def test_queue_loop_modes():
    queue = GroupQueue(chat_id=-100123456789)
    song = SongMetadata(song_id="yt_10", title="Test Track", artist="Artist", duration=120, url="http://test.com")
    item = QueueItem(song=song, requested_by_id=1, requested_by_name="User")

    await queue.add(item)
    await queue.get_next()  # current_item = item

    # Track loop mode
    queue.loop_mode = LoopMode.TRACK
    next_track = await queue.get_next()
    assert next_track.song.song_id == "yt_10"

    # Queue loop mode
    queue.loop_mode = LoopMode.QUEUE
    queue.items.clear()
    next_queue_item = await queue.get_next()
    assert next_queue_item.song.song_id == "yt_10"
    assert queue.current_item.song.song_id == "yt_10"


@pytest.mark.asyncio
async def test_queue_clear_and_shuffle():
    queue = GroupQueue(chat_id=-100123456789)
    for i in range(10):
        s = SongMetadata(song_id=f"yt_{i}", title=f"Track {i}", artist="Artist", duration=100, url="http://test.com")
        await queue.add(QueueItem(song=s, requested_by_id=1, requested_by_name="User"), allow_duplicate=True)

    assert len(queue.items) == 10
    shuffled = await queue.shuffle()
    assert shuffled is True

    cleared_count = await queue.clear()
    assert cleared_count == 10
    assert len(queue.items) == 0
