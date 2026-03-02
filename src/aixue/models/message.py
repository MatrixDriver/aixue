"""对话消息 ORM 模型。"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aixue.db.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    """消息表：解题会话中的每条对话消息。"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(ForeignKey("solving_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / system
    content: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 关联
    session: Mapped["SolvingSession"] = relationship(  # noqa: F821
        "SolvingSession", back_populates="messages"
    )
