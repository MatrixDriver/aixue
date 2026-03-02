"""练习题推荐服务：基于薄弱知识点推荐练习题。"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.models.problem import Problem
from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class Recommender:
    """练习题推荐引擎。"""

    def __init__(self) -> None:
        self.llm = LLMService()

    async def recommend(
        self,
        weak_points: list[dict],
        user_id: str,
        subject: str | None,
        grade: str,
        db: AsyncSession,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """基于薄弱知识点推荐练习题。

        Args:
            weak_points: 薄弱知识点列表
            user_id: 用户 ID
            subject: 学科
            grade: 年级
            db: 数据库会话
            limit: 推荐数量

        Returns:
            推荐题目列表
        """
        if not weak_points:
            return []

        # 提取薄弱知识点关键词
        keywords = [wp.get("point", "") for wp in weak_points if wp.get("point")]
        if not keywords:
            return []

        # 1. 从题库匹配
        matched_problems = await self._match_from_bank(
            db, keywords, subject, limit
        )

        # 2. 如题库不足，LLM 生成变式题
        if len(matched_problems) < limit:
            generated = await self._generate_problems(
                keywords, grade, subject, limit - len(matched_problems)
            )
            matched_problems.extend(generated)

        return matched_problems[:limit]

    async def _match_from_bank(
        self,
        db: AsyncSession,
        keywords: list[str],
        subject: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """从题库中匹配相关题目。"""
        query = select(Problem)
        if subject:
            query = query.where(Problem.subject == subject)

        # 按知识点关键词模糊匹配
        conditions = []
        for kw in keywords:
            conditions.append(Problem.knowledge_points.contains(kw))

        if conditions:
            from sqlalchemy import or_

            query = query.where(or_(*conditions))

        query = query.order_by(Problem.difficulty).limit(limit)

        result = await db.execute(query)
        problems = result.scalars().all()

        return [
            {
                "id": p.id,
                "content": p.content,
                "subject": p.subject,
                "difficulty": p.difficulty,
                "knowledge_points": p.knowledge_points,
                "source": p.source,
            }
            for p in problems
        ]

    async def _generate_problems(
        self,
        keywords: list[str],
        grade: str,
        subject: str | None,
        count: int,
    ) -> list[dict[str, Any]]:
        """使用 LLM 生成变式练习题。"""
        if count <= 0:
            return []

        prompt = (
            f"请为{grade}学生生成{count}道{subject or '综合'}练习题。\n\n"
            f"要针对的薄弱知识点: {', '.join(keywords)}\n\n"
            "要求:\n"
            "1. 难度循序渐进\n"
            "2. 数学公式用 LaTeX\n"
            "3. 提供参考答案\n\n"
            "返回 JSON 数组格式:\n"
            '[{"content": "题目内容", "solution": "参考答案", '
            '"difficulty": 3, "knowledge_points": "知识点"}]'
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
            problems = json.loads(clean)
            # 标记为 LLM 生成
            for p in problems:
                p["source"] = "generated"
                p["subject"] = subject or "综合"
            return problems
        except json.JSONDecodeError:
            logger.warning("LLM 生成题目 JSON 解析失败")
            return []
