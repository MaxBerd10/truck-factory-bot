"""SQLAlchemy async engine va session factory."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings


# ==== Engine ====
engine: AsyncEngine = create_async_engine(
    settings.DB_URL,
    echo=settings.is_development,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)


# ==== Session factory ====
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ==== Dependency ====
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Har bir so'rov uchun yangi session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==== Yopish ====
async def close_engine() -> None:
    """Engine ni yopish."""
    await engine.dispose()
