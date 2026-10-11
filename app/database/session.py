import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.database.base import Base

logger = logging.getLogger("QinxiaoMusic.Database")

# Create engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Import models to ensure they register on Base.metadata
            import app.models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async transactional database session context."""
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
