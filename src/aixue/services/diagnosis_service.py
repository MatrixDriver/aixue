"""学情诊断服务：五维错因分析、试卷导入、报告生成。"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.models.diagnosis import DiagnosticReport
from aixue.models.session import SolvingSession
from aixue.models.user import User
from aixue.prompts.diagnosis import build_diagnosis_prompt
from aixue.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DiagnosisService:
    """学情诊断服务。"""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    async def analyze(
        self,
        user_id: str,
        scope: str,
        subject: str | None,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """五维错因分析。

        Args:
            user_id: 用户 ID
            scope: 分析范围 "full" / "subject" / "recent"
            subject: 指定学科(scope=subject 时必传)
            db: 数据库会话

        Returns:
            诊断结果字典
        """
        # 1. 获取用户信息
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            return {"error": "用户不存在"}

        # 2. 获取解题记录
        records = await self._get_solve_records(db, user_id, scope, subject)

        # 3. 数据量判断
        if len(records) == 0:
            return {
                "error": "暂无解题记录, 请先做几道题后再进行诊断",
                "min_required": 5,
            }

        # 4. LLM 分析（MVP 阶段统一使用 LLM 分析）
        analysis = await self._llm_analyze(
            records, user.grade, subject or "综合"
        )

        # 5. 保存报告
        report = await self._save_report(
            db, user_id, scope, subject, analysis
        )

        analysis["report_id"] = report.id
        return analysis

    async def import_exam(
        self,
        user_id: str,
        images: list[tuple[bytes, str]],
        db: AsyncSession,
    ) -> dict[str, Any]:
        """试卷导入：识别题目和答案，自动判定对错。

        Args:
            user_id: 用户 ID
            images: 图片列表 [(image_data, media_type), ...]
            db: 数据库会话

        Returns:
            导入结果
        """
        all_questions: list[dict] = []

        for image_data, media_type in images:
            # 多模态 LLM 识别试卷
            prompt = (
                "请识别这张试卷图片中的所有题目。\n"
                "对每道题, 提取:\n"
                "1. 题号\n"
                "2. 题目内容(数学公式用 LaTeX)\n"
                "3. 学生的作答(如可见)\n"
                "4. 正确答案(如可见)\n"
                "5. 判定对错: correct / incorrect / unknown\n\n"
                "返回 JSON 数组格式:\n"
                '[{"number": 1, "question": "...", "student_answer": "...", '
                '"correct_answer": "...", "status": "correct/incorrect/unknown"}]'
            )
            result = await self.llm.recognize_image(
                image_data, media_type, prompt
            )

            # 解析 JSON
            try:
                # 清理可能的 markdown 代码块标记
                clean = result.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1]
                if clean.endswith("```"):
                    clean = clean.rsplit("```", 1)[0]
                clean = clean.strip()
                questions = json.loads(clean)
                all_questions.extend(questions)
            except json.JSONDecodeError:
                logger.warning("试卷识别结果 JSON 解析失败")
                continue

        return {
            "imported_count": len(all_questions),
            "questions": all_questions,
        }

    async def _get_solve_records(
        self,
        db: AsyncSession,
        user_id: str,
        scope: str,
        subject: str | None,
    ) -> list[SolvingSession]:
        """获取用户解题记录。"""
        query = (
            select(SolvingSession)
            .where(SolvingSession.user_id == user_id)
            .order_by(SolvingSession.created_at.desc())
        )

        if scope == "subject" and subject:
            query = query.where(SolvingSession.subject == subject)
        elif scope == "recent":
            query = query.limit(20)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _llm_analyze(
        self,
        records: list[SolvingSession],
        grade: str,
        subject: str,
    ) -> dict[str, Any]:
        """使用 LLM 进行五维分析。"""
        # 构建记录摘要
        records_summary = self._build_records_summary(records)

        prompt = build_diagnosis_prompt(
            grade=grade, subject=subject, records_summary=records_summary
        )
        messages = [{"role": "user", "content": prompt}]

        response = await self.llm.chat(messages)

        # 解析 JSON 响应
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1]
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()
            analysis = json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("诊断结果 JSON 解析失败, 返回原始文本")
            analysis = {
                "overall_score": None,
                "knowledge_gaps": [],
                "thinking_patterns": [],
                "concept_links": [],
                "habit_analysis": [],
                "cognitive_level": {},
                "raw_text": response,
            }

        return analysis

    def _build_records_summary(
        self, records: list[SolvingSession]
    ) -> str:
        """将解题记录构建为 LLM 可读的摘要。"""
        lines = []
        for i, record in enumerate(records[:50], 1):  # 最多 50 条
            status_map = {
                "verified": "正确(已验证)",
                "failed": "错误",
                "pending": "待验证",
            }
            status_text = status_map.get(
                record.verification_status, record.verification_status
            )
            q_text = (record.question_text or "")[:200]
            lines.append(
                f"{i}. [{record.subject}] {q_text} | 结果: {status_text}"
            )
        return "\n".join(lines)

    async def _save_report(
        self,
        db: AsyncSession,
        user_id: str,
        scope: str,
        subject: str | None,
        analysis: dict[str, Any],
    ) -> DiagnosticReport:
        """保存诊断报告到数据库。"""
        report = DiagnosticReport(
            user_id=user_id,
            scope=scope,
            subject=subject,
            overall_score=analysis.get("overall_score"),
            knowledge_gaps=json.dumps(
                analysis.get("knowledge_gaps", []), ensure_ascii=False
            ),
            thinking_patterns=json.dumps(
                analysis.get("thinking_patterns", []), ensure_ascii=False
            ),
            habit_analysis=json.dumps(
                analysis.get("habit_analysis", []), ensure_ascii=False
            ),
            cognitive_level=json.dumps(
                analysis.get("cognitive_level", {}), ensure_ascii=False
            ),
            recommendations=json.dumps(
                analysis.get("recommendations", []), ensure_ascii=False
            ),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        logger.info("诊断报告已保存: report_id=%s, user_id=%s", report.id, user_id)
        return report
