"""认证服务：密码加密、JWT 令牌生成与验证。"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from aixue.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()


def hash_password(password: str) -> str:
    """使用 bcrypt 对密码进行哈希加密。"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """验证明文密码是否与哈希值匹配。"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    """生成 JWT 访问令牌。"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """解码并验证 JWT 令牌，返回 user_id。

    Raises:
        jwt.ExpiredSignatureError: 令牌已过期
        jwt.InvalidTokenError: 令牌无效
    """
    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    user_id: str = payload["sub"]
    return user_id
