"""异步 SQLAlchemy 引擎和会话工厂。"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from aixue.config import Settings

settings = Settings()


def _fix_database_url(url: str) -> str:
    """Railway 提供 postgresql:// 格式，asyncpg 需要 postgresql+asyncpg://"""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(_fix_database_url(settings.database_url), echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
