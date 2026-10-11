from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.statistics import BotStatsModel, GroupStatsModel


class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def increment_stat(self, key: str, amount: int = 1) -> None:
        stmt = select(BotStatsModel).where(BotStatsModel.stat_key == key)
        res = await self.session.execute(stmt)
        stat = res.scalar_one_or_none()

        if not stat:
            stat = BotStatsModel(stat_key=key, stat_value=amount)
            self.session.add(stat)
        else:
            stat.stat_value += amount

        await self.session.flush()

    async def get_stat(self, key: str) -> int:
        stmt = select(BotStatsModel).where(BotStatsModel.stat_key == key)
        res = await self.session.execute(stmt)
        stat = res.scalar_one_or_none()
        return stat.stat_value if stat else 0

    async def record_group_play(self, chat_id: int, duration_sec: int = 0) -> None:
        stmt = select(GroupStatsModel).where(GroupStatsModel.chat_id == chat_id)
        res = await self.session.execute(stmt)
        grp = res.scalar_one_or_none()

        if not grp:
            grp = GroupStatsModel(chat_id=chat_id, total_plays=1, total_time_seconds=duration_sec)
            self.session.add(grp)
        else:
            grp.total_plays += 1
            grp.total_time_seconds += duration_sec

        await self.session.flush()

    async def record_group_skip(self, chat_id: int) -> None:
        stmt = select(GroupStatsModel).where(GroupStatsModel.chat_id == chat_id)
        res = await self.session.execute(stmt)
        grp = res.scalar_one_or_none()

        if not grp:
            grp = GroupStatsModel(chat_id=chat_id, total_skips=1)
            self.session.add(grp)
        else:
            grp.total_skips += 1

        await self.session.flush()

    async def get_group_stats(self, chat_id: int) -> Optional[GroupStatsModel]:
        stmt = select(GroupStatsModel).where(GroupStatsModel.chat_id == chat_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
