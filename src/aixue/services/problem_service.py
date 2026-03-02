"""题库管理服务：CRUD 操作和题目生成。"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.models.problem import Problem
from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ProblemService:
    """题库管理服务。"""

    def __init__(self) -> None:
        self.llm = LLMService()

    async def list_problems(
        self,
        db: AsyncSession,
        subject: str | None = None,
        grade_level: str | None = None,
        difficulty: int | None = None,
        knowledge_point: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Problem]:
        """查询题目列表。"""
        query = select(Problem).offset(offset).limit(limit)

        if subject:
            query = query.where(Problem.subject == subject)
        if grade_level:
            query = query.where(Problem.grade_level == grade_level)
        if difficulty is not None:
            query = query.where(Problem.difficulty == difficulty)
        if knowledge_point:
            query = query.where(
                Problem.knowledge_points.contains(knowledge_point)
            )

        query = query.order_by(Problem.difficulty, Problem.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_problem(
        self, db: AsyncSession, problem_id: str
    ) -> Problem | None:
        """获取题目详情。"""
        result = await db.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        return result.scalar_one_or_none()

    async def generate_variant(
        self,
        db: AsyncSession,
        source_problem_id: str | None = None,
        subject: str | None = None,
        knowledge_points: str | None = None,
        grade_level: str = "",
        difficulty: int = 3,
    ) -> dict[str, Any]:
        """使用 LLM 生成变式题。

        Args:
            db: 数据库会话
            source_problem_id: 原题 ID(基于此题生成变式)
            subject: 学科
            knowledge_points: 目标知识点
            grade_level: 年级
            difficulty: 难度(1-5)

        Returns:
            生成的题目信息
        """
        # 获取原题信息
        source_text = ""
        if source_problem_id:
            source = await self.get_problem(db, source_problem_id)
            if source:
                source_text = f"\n原题:\n{source.content}\n"
                subject = subject or source.subject
                knowledge_points = knowledge_points or source.knowledge_points
                grade_level = grade_level or source.grade_level

        prompt = (
            f"请生成一道{subject or '数学'}变式练习题。\n"
            f"{source_text}\n"
            f"知识点: {knowledge_points or '综合'}\n"
            f"年级: {grade_level}\n"
            f"难度: {difficulty}/5\n\n"
            "要求:\n"
            "1. 题型和知识点与原题相似, 但数据和情境不同\n"
            "2. 数学公式用 LaTeX\n"
            "3. 提供详细解答\n\n"
            "返回 JSON 格式:\n"
            '{"content": "题目内容", "solution": "详细解答", '
            '"knowledge_points": "知识点", "difficulty": 3}'
        )

        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1]
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()
            problem_data = json.loads(clean)

            # 保存到题库
            problem = Problem(
                subject=subject or "数学",
                grade_level=grade_level,
                knowledge_points=problem_data.get("knowledge_points", ""),
                difficulty=problem_data.get("difficulty", difficulty),
                content=problem_data.get("content", ""),
                solution=problem_data.get("solution"),
                source="generated",
            )
            db.add(problem)
            await db.commit()
            await db.refresh(problem)

            return {
                "id": problem.id,
                "content": problem.content,
                "solution": problem.solution,
                "knowledge_points": problem.knowledge_points,
                "difficulty": problem.difficulty,
            }

        except json.JSONDecodeError:
            logger.warning("LLM 变式题 JSON 解析失败")
            return {"error": "题目生成失败, 请重试", "raw": response}

    async def batch_import(
        self,
        db: AsyncSession,
        problems: list[dict],
    ) -> int:
        """批量导入题目。

        Args:
            db: 数据库会话
            problems: 题目数据列表

        Returns:
            成功导入的数量
        """
        count = 0
        for p_data in problems:
            problem = Problem(
                subject=p_data.get("subject", "数学"),
                grade_level=p_data.get("grade_level", ""),
                knowledge_points=json.dumps(
                    p_data.get("knowledge_points", []), ensure_ascii=False
                )
                if isinstance(p_data.get("knowledge_points"), list)
                else p_data.get("knowledge_points", ""),
                difficulty=p_data.get("difficulty", 3),
                content=p_data.get("content", ""),
                solution=p_data.get("solution"),
                source=p_data.get("source", "imported"),
                image_url=p_data.get("image_url"),
            )
            db.add(problem)
            count += 1

        await db.commit()
        logger.info("批量导入题目: count=%d", count)
        return count
