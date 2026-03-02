"""学情诊断相关的 Pydantic 数据模式。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DiagnosisResponse(BaseModel):
    """诊断分析响应。"""

    report_id: str | None = None
    overall_score: float | None = None
    knowledge_gaps: list[dict[str, Any]] = []
    thinking_patterns: list[dict[str, Any]] = []
    concept_links: list[dict[str, Any]] = []
    habit_analysis: list[dict[str, Any]] = []
    cognitive_level: dict[str, Any] = {}
    error: str | None = None


class ExamImportResponse(BaseModel):
    """试卷导入响应。"""

    imported_count: int = 0
    questions: list[dict[str, Any]] = []
    error: str | None = None


class DiagnosisReportSummary(BaseModel):
    """诊断报告摘要。"""

    id: str
    scope: str
    subject: str | None = None
    overall_score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiagnosisReportDetail(BaseModel):
    """诊断报告详情。"""

    id: str
    scope: str
    subject: str | None = None
    overall_score: float | None = None
    knowledge_gaps: str | None = None
    thinking_patterns: str | None = None
    habit_analysis: str | None = None
    cognitive_level: str | None = None
    recommendations: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
