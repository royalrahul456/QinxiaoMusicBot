import pytest
from app.providers.base import SongMetadata


def test_song_metadata_to_dict():
    meta = SongMetadata(
        song_id="yt_test",
        title="Test Song",
        artist="Test Artist",
        duration=180,
        url="http://example.com/test",
        source="youtube"
    )

    d = meta.to_dict()
    assert d["song_id"] == "yt_test"
    assert d["title"] == "Test Song"
    assert d["duration"] == 180

    reconstructed = SongMetadata.from_dict(d)
    assert reconstructed.song_id == meta.song_id
    assert reconstructed.title == meta.title
