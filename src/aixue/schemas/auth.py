"""认证相关的 Pydantic 数据模式。"""

from pydantic import BaseModel, Field, field_validator

VALID_GRADES = {"初一", "初二", "初三", "高一", "高二", "高三"}


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)
    grade: str = Field(..., max_length=20)
    subjects: str = Field(..., max_length=200)

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        if v not in VALID_GRADES:
            raise ValueError(
                f"无效的年级, 有效值: {', '.join(sorted(VALID_GRADES))}"
            )
        return v


class TokenResponse(BaseModel):
    """令牌响应。"""

    access_token: str
    token_type: str = "bearer"
