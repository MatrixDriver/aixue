"""题库 ORM 模型。"""

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aixue.db.base import Base, TimestampMixin


class Problem(Base, TimestampMixin):
    """题目表：题库中的每道题目。"""

    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject: Mapped[str] = mapped_column(String(20), index=True)
    grade_level: Mapped[str] = mapped_column(String(20))
    knowledge_points: Mapped[str] = mapped_column(Text)  # JSON 数组
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    content: Mapped[str] = mapped_column(Text)  # LaTeX 格式题目
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50)
    )  # cmm-math / tal-scq5k / user / generated
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
