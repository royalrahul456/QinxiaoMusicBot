from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserModel
from app.models.favorite import FavoriteModel
from app.models.history import HistoryModel


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> UserModel:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = UserModel(user_id=user_id, username=username, first_name=first_name)
            self.session.add(user)
            await self.session.flush()
        else:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if updated:
                await self.session.flush()

        return user

    async def update_settings(self, user_id: int, **kwargs) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            for key, val in kwargs.items():
                if hasattr(user, key) and val is not None:
                    setattr(user, key, val)
            await self.session.flush()
        return user

    async def add_stats(self, user_id: int, duration_sec: float) -> None:
        user = await self.get_or_create(user_id)
        user.total_play_count += 1
        user.total_listening_time += max(0.0, duration_sec)
        await self.session.flush()

    async def get_history(self, user_id: int, limit: int = 20, offset: int = 0) -> List[HistoryModel]:
        stmt = (
            select(HistoryModel)
            .where(HistoryModel.user_id == user_id)
            .order_by(HistoryModel.played_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_history(self, user_id: int, chat_id: int, song_id: str, title: str, artist: str, duration: int, url: str, thumbnail: Optional[str]) -> HistoryModel:
        history_item = HistoryModel(
            user_id=user_id,
            chat_id=chat_id,
            song_id=song_id,
            title=title,
            artist=artist,
            duration=duration,
            url=url,
            thumbnail=thumbnail,
            played_at=datetime.utcnow()
        )
        self.session.add(history_item)
        await self.session.flush()
        return history_item
