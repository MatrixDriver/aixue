"""
AIXue MVP 测试共享 fixtures。

提供异步数据库会话、测试客户端、测试用户等公共设施。
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from aixue.db.base import Base
from aixue.db.session import get_db
from aixue.main import app


# ---------------------------------------------------------------------------
# 数据库 fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    """创建内存 SQLite 异步引擎，测试结束后销毁。"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """提供一个事务隔离的异步数据库会话。"""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# FastAPI 测试客户端
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_engine):
    """覆盖数据库依赖的异步 HTTP 测试客户端。"""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 测试数据 fixtures
# ---------------------------------------------------------------------------

TEST_USERS = [
    {
        "username": "test_grade8",
        "password": "TestPass123",
        "name": "测试初二",
        "grade": "初二",
        "subjects": "数学,物理",
    },
    {
        "username": "test_grade9",
        "password": "TestPass456",
        "name": "测试初三",
        "grade": "初三",
        "subjects": "数学,化学",
    },
    {
        "username": "test_admin",
        "password": "AdminPass789",
        "name": "测试管理",
        "grade": "高一",
        "subjects": "数学,物理,化学,生物",
    },
]


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    """注册一个测试用户并返回其信息。"""
    user_data = TEST_USERS[0]
    resp = await client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 201 or resp.status_code == 200
    return user_data


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, registered_user: dict):
    """获取已注册用户的 JWT token。"""
    resp = await client.post(
        "/api/auth/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token: str):
    """构造带 JWT 的请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# 测试图片 fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_math_image() -> bytes:
    """返回一张最小的合法 PNG 图片（用于测试上传逻辑）。"""
    # 1x1 白色 PNG
    import base64

    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "2mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(png_b64)


@pytest.fixture
def oversized_image() -> bytes:
    """返回一张超过大小限制的伪图片。"""
    return b"\x00" * (6 * 1024 * 1024)  # 6MB
