import secrets
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.premium import PremiumKeyModel, PremiumSubModel


class PremiumRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_key(self, generated_by: int, plan_name: str = "standard", duration_days: int = 30) -> PremiumKeyModel:
        raw_key = f"QINXIAO-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        key_obj = PremiumKeyModel(
            key=raw_key,
            plan_name=plan_name,
            duration_days=duration_days,
            generated_by=generated_by,
            is_used=False
        )
        self.session.add(key_obj)
        await self.session.flush()
        return key_obj

    async def activate_key(self, key_str: str, entity_id: int, entity_type: str = "user") -> Tuple[bool, str]:
        stmt = select(PremiumKeyModel).where(PremiumKeyModel.key == key_str)
        res = await self.session.execute(stmt)
        key_obj = res.scalar_one_or_none()

        if not key_obj:
            return False, "Invalid premium key."
        if key_obj.is_used:
            return False, "This key has already been activated."

        # Atomic conditional update to prevent concurrent double-activation
        upd_stmt = (
            update(PremiumKeyModel)
            .where(PremiumKeyModel.key == key_str, PremiumKeyModel.is_used == False)
            .values(is_used=True, used_by=entity_id, used_at=datetime.utcnow())
        )
        upd_res = await self.session.execute(upd_stmt)
        if upd_res.rowcount == 0:
            return False, "This key has already been activated."
        key_obj.is_used = True
        key_obj.used_by = entity_id
        key_obj.used_at = datetime.utcnow()

        # Check existing subscription
        sub_stmt = select(PremiumSubModel).where(
            PremiumSubModel.entity_id == entity_id,
            PremiumSubModel.entity_type == entity_type
        )
        sub_res = await self.session.execute(sub_stmt)
        sub = sub_res.scalar_one_or_none()

        now = datetime.utcnow()
        duration = timedelta(days=key_obj.duration_days)

        if sub and sub.expires_at > now:
            sub.expires_at += duration
            sub.plan_name = key_obj.plan_name
        else:
            if not sub:
                sub = PremiumSubModel(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    plan_name=key_obj.plan_name,
                    activated_at=now,
                    expires_at=now + duration
                )
                self.session.add(sub)
            else:
                sub.plan_name = key_obj.plan_name
                sub.activated_at = now
                sub.expires_at = now + duration

        await self.session.flush()
        exp_str = sub.expires_at.strftime("%Y-%m-%d %H:%M UTC")
        return True, f"Premium successfully activated ({sub.plan_name.title()} Plan)! Expires on {exp_str}."

    async def revoke_key(self, key_str: str) -> bool:
        stmt = select(PremiumKeyModel).where(PremiumKeyModel.key == key_str)
        res = await self.session.execute(stmt)
        key_obj = res.scalar_one_or_none()
        if key_obj:
            await self.session.delete(key_obj)
            await self.session.flush()
            return True
        return False

    async def get_subscription(self, entity_id: int, entity_type: str = "user") -> Optional[PremiumSubModel]:
        stmt = select(PremiumSubModel).where(
            PremiumSubModel.entity_id == entity_id,
            PremiumSubModel.entity_type == entity_type
        )
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()
        if sub and sub.expires_at < datetime.utcnow():
            return None
        return sub

    async def is_premium(self, entity_id: int, entity_type: str = "user") -> bool:
        sub = await self.get_subscription(entity_id, entity_type)
        return sub is not None
