"""学情诊断 ORM 模型。"""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aixue.db.base import Base, TimestampMixin


class DiagnosticReport(Base, TimestampMixin):
    """诊断报告表：存储学情分析结果。"""

    __tablename__ = "diagnostic_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    scope: Mapped[str] = mapped_column(String(20))  # full / subject / recent
    subject: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    knowledge_gaps: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    thinking_patterns: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    habit_analysis: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    cognitive_level: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    recommendations: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON - 推荐题目 ID 列表

    # 关联
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="diagnostics"
    )
