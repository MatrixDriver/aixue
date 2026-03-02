"""认证 API 端点：注册 / 登录。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.db.session import get_db
from aixue.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from aixue.services.auth_service import create_access_token, verify_password
from aixue.services.user_service import create_user, get_user_by_username

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """用户注册。"""
    existing = await get_user_by_username(db, data.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    user = await create_user(db, data)
    token = create_access_token(user.id)
    logger.info("用户注册成功: %s", user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """用户登录。"""
    user = await get_user_by_username(db, data.username)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(user.id)
    logger.info("用户登录成功: %s", user.username)
    return TokenResponse(access_token=token)
