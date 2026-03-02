"""数据库会话依赖注入。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from aixue.db.engine import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：提供一个请求级别的数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session
