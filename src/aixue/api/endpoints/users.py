"""用户管理 API 端点。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.db.session import get_db
from aixue.dependencies import get_current_user
from aixue.models.user import User
from aixue.schemas.user import UserProfile, UserResponse, UserStats
from aixue.services.user_service import get_user_stats, update_user_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户信息。"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    profile: UserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """更新个人信息。"""
    updated = await update_user_profile(db, current_user.id, profile)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return UserResponse.model_validate(updated)


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserStats:
    """获取解题统计。"""
    return await get_user_stats(db, current_user.id)
