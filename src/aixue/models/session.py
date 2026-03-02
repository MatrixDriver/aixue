"""解题会话 ORM 模型。"""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aixue.db.base import Base, TimestampMixin


class SolvingSession(Base, TimestampMixin):
    """解题会话表：一次解题交互的完整上下文。"""

    __tablename__ = "solving_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(20))  # 数学/物理/化学/生物
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mode: Mapped[str] = mapped_column(
        String(20), default="socratic"
    )  # socratic / direct
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending / verified / failed
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 关联
    user: Mapped["User"] = relationship("User", back_populates="sessions")  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="session", order_by="Message.created_at"
    )
