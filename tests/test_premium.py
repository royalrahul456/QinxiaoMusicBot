import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base
from app.repositories.premium_repo import PremiumRepository
from app.premium.manager import premium_manager


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_premium_key_lifecycle(async_session):
    owner_id = 123456789
    user_id = 987654321

    # 1. Generate key
    key_obj = await premium_manager.generate_key(async_session, owner_id, plan_name="pro", duration_days=30)
    assert key_obj.key.startswith("QINXIAO-")
    assert key_obj.is_used is False

    # 2. Check non-premium status
    is_prem_before = await premium_manager.is_premium(async_session, user_id)
    assert is_prem_before is False

    # 3. Activate key
    success, msg = await premium_manager.activate(async_session, key_obj.key, user_id)
    assert success is True
    assert "Pro Plan" in msg

    # 4. Check active premium status
    is_prem_after = await premium_manager.is_premium(async_session, user_id)
    assert is_prem_after is True

    # 5. Prevent key reuse
    reuse_success, reuse_msg = await premium_manager.activate(async_session, key_obj.key, user_id)
    assert reuse_success is False
    assert "already been activated" in reuse_msg
