"""题库相关的 Pydantic 数据模式。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProblemOut(BaseModel):
    """题目输出。"""

    id: str
    subject: str
    grade_level: str
    knowledge_points: str
    difficulty: int
    content: str
    solution: str | None = None
    source: str
    image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    """变式题生成请求。"""

    source_problem_id: str | None = None
    subject: str | None = Field(None, max_length=20)
    knowledge_points: str | None = None
    grade_level: str = Field("", max_length=20)
    difficulty: int = Field(3, ge=1, le=5)


class GenerateResponse(BaseModel):
    """变式题生成响应。"""

    id: str | None = None
    content: str = ""
    solution: str | None = None
    knowledge_points: str | None = None
    difficulty: int = 3
    error: str | None = None
    raw: str | None = None
