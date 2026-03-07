"""解题会话相关的 Pydantic 数据模式。"""

from datetime import datetime

from pydantic import BaseModel


class SolveResponse(BaseModel):
    """解题响应。"""

    session_id: str
    subject: str
    question: str
    content: str
    mode: str
    verified: bool = False
    attempts: int = 1
    sympy_result: str | None = None
    error: str | None = None


class FollowUpRequest(BaseModel):
    """追问请求。"""

    message: str


class FollowUpResponse(BaseModel):
    """追问响应。"""

    session_id: str
    content: str
    mode: str
    error: str | None = None


class MessageOut(BaseModel):
    """对话消息输出。"""

    id: str
    role: str
    content: str
    image_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    """会话摘要（列表页）。"""

    id: str
    subject: str
    mode: str
    question_text: str | None = None
    verification_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionInfo(BaseModel):
    """检测到的单道题目信息。"""

    index: int
    label: str
    summary: str
    complete: bool


class DetectResponse(BaseModel):
    """多题检测响应。"""

    question_count: int
    questions: list[QuestionInfo]
    message: str


class SessionDetail(BaseModel):
    """会话详情（含完整对话记录）。"""

    id: str
    subject: str
    mode: str
    question_text: str | None = None
    verified_answer: str | None = None
    verification_status: str
    confidence: float | None = None
    created_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
