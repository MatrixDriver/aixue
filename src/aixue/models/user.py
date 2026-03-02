"""用户 ORM 模型。"""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aixue.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表：存储注册信息和 profile。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(100))
    grade: Mapped[str] = mapped_column(String(20))  # 初一~高三
    subjects: Mapped[str] = mapped_column(String(200))  # 逗号分隔的学科列表

    # 关联
    sessions: Mapped[list["SolvingSession"]] = relationship(  # noqa: F821
        "SolvingSession", back_populates="user"
    )
    diagnostics: Mapped[list["DiagnosticReport"]] = relationship(  # noqa: F821
        "DiagnosticReport", back_populates="user"
    )
