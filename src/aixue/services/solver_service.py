"""解题主控服务：协调 OCR、学科判定、解题器、验证。"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from aixue.models.message import Message
from aixue.models.session import SolvingSession
from aixue.services.general_solver import GeneralSolver
from aixue.services.llm_service import LLMService
from aixue.services.math_solver import MathSolver
from aixue.services.ocr_service import OCRService
from aixue.services.verifier import MathVerifier

logger = logging.getLogger(__name__)


class SolverService:
    """解题服务主控：协调完整解题流程。"""

    def __init__(
        self,
        llm: LLMService | None = None,
        verifier: MathVerifier | None = None,
    ) -> None:
        self.llm = llm or LLMService()
        self.verifier = verifier or MathVerifier()
        self.ocr = OCRService(self.llm)
        self.math_solver = MathSolver(self.llm, self.verifier)
        self.general_solver = GeneralSolver(self.llm)

    async def solve(
        self,
        image: bytes | None,
        media_type: str | None,
        text: str | None,
        subject: str | None,
        mode: str,
        session_id: str | None,
        user_profile: dict,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """完整解题流程。

        Args:
            image: 图片二进制数据
            media_type: 图片 MIME 类型
            text: 题目文本(和 image 二选一)
            subject: 学科(可选, 不传则自动判定)
            mode: 解题模式 "socratic" / "direct"
            session_id: 已有会话 ID(追问时传入)
            user_profile: 用户信息
            db: 数据库会话

        Returns:
            解题结果字典
        """
        # 1. 题目识别
        question = await self._recognize(image, media_type, text)
        if not question:
            return {"error": "无法识别题目内容, 请重新上传清晰图片或输入题目文字"}

        # 2. 学科判定
        if not subject:
            subject = await self.ocr.detect_subject(question)

        # 3. 分策略解题
        if subject == "数学":
            result = await self.math_solver.solve(question, mode, user_profile)
        else:
            result = await self.general_solver.solve(
                question, subject, mode, user_profile
            )

        # 4. 保存记录
        session = await self._save_session(
            db=db,
            user_id=user_profile["id"],
            subject=subject,
            mode=mode,
            question_text=question,
            image_path=None,  # 图片存储逻辑后续完善
            result=result,
            session_id=session_id,
        )

        result["session_id"] = session.id
        result["subject"] = subject
        result["question"] = question
        return result

    async def follow_up(
        self,
        session_id: str,
        message_text: str,
        user_profile: dict,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """多轮追问。

        Args:
            session_id: 会话 ID
            message_text: 追问内容
            user_profile: 用户信息
            db: 数据库会话

        Returns:
            响应结果
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 获取会话和历史消息
        result = await db.execute(
            select(SolvingSession)
            .options(selectinload(SolvingSession.messages))
            .where(SolvingSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            return {"error": "会话不存在"}

        if session.user_id != user_profile["id"]:
            return {"error": "无权访问此会话"}

        # 构建历史消息上下文
        from aixue.prompts.system import build_system_prompt

        system_prompt = build_system_prompt(
            student_name=user_profile.get("name", "同学"),
            grade=user_profile.get("grade", ""),
            subjects=user_profile.get("subjects", ""),
        )

        messages = []
        for msg in session.messages:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message_text})

        # 调用 LLM
        response = await self.llm.chat(messages, system=system_prompt)

        # 保存消息
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=message_text,
        )
        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=response,
        )
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()

        return {
            "session_id": session_id,
            "content": response,
            "mode": session.mode,
        }

    async def _recognize(
        self,
        image: bytes | None,
        media_type: str | None,
        text: str | None,
    ) -> str:
        """题目识别：图片 OCR + 用户文本合并。

        - 仅文本: 直接返回
        - 仅图片: OCR 识别
        - 图片+文本: 将用户文本作为 OCR 聚焦提示（如 "第14题"），
          让模型只识别指定题目，减少无关内容和处理时间
        """
        ocr_text = ""
        if image and media_type:
            ocr_text = await self.ocr.recognize(
                image, media_type, user_hint=text
            )

        if ocr_text and text:
            return f"{ocr_text}\n\n【用户补充说明】{text}"
        if ocr_text:
            return ocr_text
        if text:
            return text
        return ""

    async def _save_session(
        self,
        db: AsyncSession,
        user_id: str,
        subject: str,
        mode: str,
        question_text: str,
        image_path: str | None,
        result: dict[str, Any],
        session_id: str | None = None,
    ) -> SolvingSession:
        """保存解题会话和消息到数据库。"""
        if session_id:
            from sqlalchemy import select

            q = await db.execute(
                select(SolvingSession).where(SolvingSession.id == session_id)
            )
            session = q.scalar_one_or_none()
            if session:
                # 更新已有会话
                session.verified_answer = result.get("sympy_result")
                session.verification_status = (
                    "verified" if result.get("verified") else "pending"
                )
                session.confidence = (
                    1.0 if result.get("verified") else 0.5
                )
                await db.commit()
                return session

        # 创建新会话
        session = SolvingSession(
            user_id=user_id,
            subject=subject,
            mode=mode,
            question_text=question_text,
            image_path=image_path,
            verified_answer=result.get("sympy_result"),
            verification_status=(
                "verified" if result.get("verified") else "pending"
            ),
            confidence=1.0 if result.get("verified") else 0.5,
        )
        db.add(session)
        await db.flush()

        # 保存消息
        user_msg = Message(
            session_id=session.id,
            role="user",
            content=question_text,
        )
        assistant_msg = Message(
            session_id=session.id,
            role="assistant",
            content=result.get("content", ""),
        )
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()

        return session
