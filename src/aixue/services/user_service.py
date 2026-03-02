"""用户管理服务：注册、查询、更新。"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.models.diagnosis import DiagnosticReport
from aixue.models.session import SolvingSession
from aixue.models.user import User
from aixue.schemas.auth import RegisterRequest
from aixue.schemas.user import UserProfile, UserStats
from aixue.services.auth_service import hash_password

logger = logging.getLogger(__name__)


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    """创建新用户。"""
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        grade=data.grade,
        subjects=data.subjects,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("新用户注册: username=%s, grade=%s", data.username, data.grade)
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """按用户名查询用户。"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """按 ID 查询用户。"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession, user_id: str, profile: UserProfile
) -> User | None:
    """更新用户 profile，只修改非 None 字段。"""
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None

    update_data = profile.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    logger.info("用户 profile 已更新: user_id=%s, fields=%s", user_id, list(update_data.keys()))
    return user


async def get_user_stats(db: AsyncSession, user_id: str) -> UserStats:
    """获取用户的解题统计信息。"""
    # 总会话数
    total_q = await db.execute(
        select(func.count()).where(SolvingSession.user_id == user_id)
    )
    total_sessions = total_q.scalar() or 0

    # 各学科会话数
    stats: dict[str, int] = {}
    for subj in ["数学", "物理", "化学", "生物"]:
        q = await db.execute(
            select(func.count()).where(
                SolvingSession.user_id == user_id,
                SolvingSession.subject == subj,
            )
        )
        stats[subj] = q.scalar() or 0

    # 验证通过数
    verified_q = await db.execute(
        select(func.count()).where(
            SolvingSession.user_id == user_id,
            SolvingSession.verification_status == "verified",
        )
    )
    verified_count = verified_q.scalar() or 0

    # 诊断报告数
    diag_q = await db.execute(
        select(func.count()).where(DiagnosticReport.user_id == user_id)
    )
    total_diagnostics = diag_q.scalar() or 0

    return UserStats(
        total_sessions=total_sessions,
        math_sessions=stats.get("数学", 0),
        physics_sessions=stats.get("物理", 0),
        chemistry_sessions=stats.get("化学", 0),
        biology_sessions=stats.get("生物", 0),
        verified_count=verified_count,
        total_diagnostics=total_diagnostics,
    )
