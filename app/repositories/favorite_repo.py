from typing import Optional, List, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import FavoriteModel


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite(self, user_id: int, song_id: str, title: str, artist: str, duration: int, url: str, thumbnail: Optional[str] = None, source: str = "youtube") -> Tuple[FavoriteModel, bool]:
        """Returns (favorite, created) tuple. Prevents duplicates."""
        stmt = select(FavoriteModel).where(FavoriteModel.user_id == user_id, FavoriteModel.song_id == song_id)
        res = await self.session.execute(stmt)
        fav = res.scalar_one_or_none()

        if fav:
            return fav, False

        fav = FavoriteModel(
            user_id=user_id,
            song_id=song_id,
            title=title,
            artist=artist,
            duration=duration,
            url=url,
            thumbnail=thumbnail,
            source=source
        )
        self.session.add(fav)
        await self.session.flush()
        return fav, True

    async def remove_favorite(self, user_id: int, song_id: str) -> bool:
        stmt = delete(FavoriteModel).where(FavoriteModel.user_id == user_id, FavoriteModel.song_id == song_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def is_favorite(self, user_id: int, song_id: str) -> bool:
        stmt = select(FavoriteModel).where(FavoriteModel.user_id == user_id, FavoriteModel.song_id == song_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def get_favorites(self, user_id: int, limit: int = 20, offset: int = 0) -> List[FavoriteModel]:
        stmt = (
            select(FavoriteModel)
            .where(FavoriteModel.user_id == user_id)
            .order_by(FavoriteModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def count_favorites(self, user_id: int) -> int:
        stmt = select(FavoriteModel).where(FavoriteModel.user_id == user_id)
        res = await self.session.execute(stmt)
        return len(res.scalars().all())
