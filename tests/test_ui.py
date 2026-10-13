import pytest
from app.player.queue_manager import GroupQueue, QueueItem
from app.providers.base import SongMetadata
from app.player.ui import build_player_text, build_player_keyboard


def test_build_player_text_image2_layout():
    queue = GroupQueue(chat_id=-100123456789)
    song = SongMetadata(
        song_id="mood123",
        title="24kGoldn - Mood (Lyrics) ft. Iann Dior",
        artist="24kGoldn",
        duration=139,
        url="https://youtube.com/watch?v=mood123",
        thumbnail="https://i.ytimg.com/vi/mood123/hqdefault.jpg"
    )
    item = QueueItem(
        song=song,
        requested_by_id=12345,
        requested_by_name="IOVANNI"
    )
    queue.current_item = item

    text = build_player_text(queue, is_paused=False)
    assert "| <u>Started streaming</u>" in text
    assert "<b>Title:</b> <a href=\"https://youtube.com/watch?v=mood123\">24kGoldn - Mood (Lyrics) ft. Iann Dior</a>" in text
    assert "<b>Duration:</b> 2:19 min" in text
    assert "<b>Requested by:</b> IOVANNI" in text

    # When paused
    paused_text = build_player_text(queue, is_paused=True)
    assert "| <u>Stream paused</u>" in paused_text


def test_build_player_keyboard_image2_layout():
    queue = GroupQueue(chat_id=-100123456789)

    kb_playing = build_player_keyboard(queue, is_paused=False)
    assert len(kb_playing.inline_keyboard) == 2
    row1 = [b.text for b in kb_playing.inline_keyboard[0]]
    assert row1 == ["▸▸I", "◽", "II"]
    row2 = [b.text for b in kb_playing.inline_keyboard[1]]
    assert row2 == ["➕", "Close"]

    # When paused, II becomes ▷
    kb_paused = build_player_keyboard(queue, is_paused=True)
    row1_paused = [b.text for b in kb_paused.inline_keyboard[0]]
    assert row1_paused == ["▸▸I", "◽", "▷"]
