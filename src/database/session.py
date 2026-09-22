"""Database session maker."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.engine import engine


async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
