import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base
from app.repositories.user_repo import UserRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.favorite_repo import FavoriteRepository


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
async def test_user_repository(async_session):
    repo = UserRepository(async_session)
    user = await repo.get_or_create(1001, "testuser", "Test User")
    assert user.user_id == 1001
    assert user.username == "testuser"
    assert user.default_volume == 100

    # Update settings
    updated = await repo.update_settings(1001, default_volume=80, default_quality="medium")
    assert updated.default_volume == 80
    assert updated.default_quality == "medium"


@pytest.mark.asyncio
async def test_chat_repository(async_session):
    repo = ChatRepository(async_session)
    chat = await repo.get_or_create(-100999, "Music Lounge")
    assert chat.chat_id == -100999
    assert chat.is_247 is False

    await repo.update_settings(-100999, is_247=True)
    chats_247 = await repo.get_247_chats()
    assert len(chats_247) == 1
    assert chats_247[0].chat_id == -100999


@pytest.mark.asyncio
async def test_favorite_repository(async_session):
    repo = FavoriteRepository(async_session)
    fav, created = await repo.add_favorite(
        user_id=500,
        song_id="yt_abc",
        title="Faded",
        artist="Alan Walker",
        duration=212,
        url="http://youtube.com/watch?v=abc"
    )
    assert created is True
    assert fav.title == "Faded"

    # Duplicate check
    _, dup_created = await repo.add_favorite(
        user_id=500,
        song_id="yt_abc",
        title="Faded",
        artist="Alan Walker",
        duration=212,
        url="http://youtube.com/watch?v=abc"
    )
    assert dup_created is False

    # Check is_favorite
    assert await repo.is_favorite(500, "yt_abc") is True

    # Remove favorite
    removed = await repo.remove_favorite(500, "yt_abc")
    assert removed is True
    assert await repo.is_favorite(500, "yt_abc") is False
