from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.premium_repo import PremiumRepository

PREMIUM_PLANS: Dict[str, Dict[str, Any]] = {
    "standard": {
        "name": "Standard Plan",
        "duration": 30,
        "max_queue": 100,
        "allow_247": True,
        "max_quality": "high",
    },
    "pro": {
        "name": "Pro Plan",
        "duration": 90,
        "max_queue": 250,
        "allow_247": True,
        "max_quality": "high",
    },
    "ultimate": {
        "name": "Ultimate Plan",
        "duration": 365,
        "max_queue": 500,
        "allow_247": True,
        "max_quality": "high",
    }
}


class PremiumManager:
    @staticmethod
    async def generate_key(session: AsyncSession, owner_id: int, plan_name: str = "standard", duration_days: int = 30):
        repo = PremiumRepository(session)
        return await repo.generate_key(generated_by=owner_id, plan_name=plan_name, duration_days=duration_days)

    @staticmethod
    async def activate(session: AsyncSession, key_str: str, user_id: int) -> Tuple[bool, str]:
        repo = PremiumRepository(session)
        return await repo.activate_key(key_str=key_str, entity_id=user_id, entity_type="user")

    @staticmethod
    async def revoke(session: AsyncSession, key_str: str) -> bool:
        repo = PremiumRepository(session)
        return await repo.revoke_key(key_str)

    @staticmethod
    async def is_premium(session: AsyncSession, user_id: int) -> bool:
        repo = PremiumRepository(session)
        return await repo.is_premium(user_id, "user")


premium_manager = PremiumManager()
