from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.song import SongModel


class SongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_or_update(self, song_id: str, title: str, artist: str, duration: int, url: str, source: str = "youtube", thumbnail: Optional[str] = None, album: Optional[str] = None) -> SongModel:
        stmt = select(SongModel).where(SongModel.song_id == song_id)
        res = await self.session.execute(stmt)
        song = res.scalar_one_or_none()

        if not song:
            song = SongModel(
                song_id=song_id,
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                url=url,
                source=source,
                thumbnail=thumbnail,
                play_count=1,
                last_played_at=datetime.utcnow()
            )
            self.session.add(song)
        else:
            song.play_count += 1
            song.last_played_at = datetime.utcnow()
            if thumbnail:
                song.thumbnail = thumbnail

        await self.session.flush()
        return song

    async def get_top_songs(self, limit: int = 10) -> List[SongModel]:
        stmt = select(SongModel).order_by(SongModel.play_count.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_top_artists(self, limit: int = 10) -> List[Tuple[str, int]]:
        stmt = (
            select(SongModel.artist, func.sum(SongModel.play_count).label("total_plays"))
            .group_by(SongModel.artist)
            .order_by(func.sum(SongModel.play_count).desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in res.all()]
