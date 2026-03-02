"""用户相关的 Pydantic 数据模式。"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户 profile 更新请求。"""

    name: str | None = Field(None, max_length=100)
    grade: str | None = Field(None, max_length=20)
    subjects: str | None = Field(None, max_length=200)


class UserResponse(BaseModel):
    """用户信息响应。"""

    id: str
    username: str
    name: str
    grade: str
    subjects: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStats(BaseModel):
    """用户解题统计。"""

    total_sessions: int = 0
    math_sessions: int = 0
    physics_sessions: int = 0
    chemistry_sessions: int = 0
    biology_sessions: int = 0
    verified_count: int = 0
    total_diagnostics: int = 0
