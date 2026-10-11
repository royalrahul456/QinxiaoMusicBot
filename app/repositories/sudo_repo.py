from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sudo import SudoUserModel


class SudoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sudo(self, user_id: int, added_by: int) -> bool:
        stmt = select(SudoUserModel).where(SudoUserModel.user_id == user_id)
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            return False

        sudo_user = SudoUserModel(user_id=user_id, added_by=added_by)
        self.session.add(sudo_user)
        await self.session.flush()
        return True

    async def remove_sudo(self, user_id: int) -> bool:
        stmt = delete(SudoUserModel).where(SudoUserModel.user_id == user_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def is_sudo(self, user_id: int) -> bool:
        stmt = select(SudoUserModel).where(SudoUserModel.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def get_sudo_list(self) -> List[int]:
        stmt = select(SudoUserModel.user_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
