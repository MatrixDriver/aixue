"""知识追踪服务：pyKT 集成封装。

MVP 阶段提供接口骨架，实际 pyKT 模型在数据积累充足后启用。
当前退化为基于统计的简单追踪。
"""

import logging

logger = logging.getLogger(__name__)


class KnowledgeTracer:
    """知识追踪器。

    MVP 初期使用简单统计方法估算知识点掌握度。
    后续数据积累后切换到 pyKT 深度知识追踪模型。
    """

    def __init__(self) -> None:
        self._pykt_available = False
        logger.info(
            "KnowledgeTracer 初始化: pyKT=%s",
            "可用" if self._pykt_available else "未启用(数据不足)",
        )

    async def estimate_mastery(
        self,
        user_id: str,
        knowledge_points: list[str],
        solve_history: list[dict],
    ) -> dict[str, float]:
        """估算用户对各知识点的掌握度。

        Args:
            user_id: 用户 ID
            knowledge_points: 待评估的知识点列表
            solve_history: 解题历史记录

        Returns:
            知识点 -> 掌握度(0.0~1.0) 的映射
        """
        if self._pykt_available:
            return await self._pykt_estimate(
                user_id, knowledge_points, solve_history
            )
        return self._statistical_estimate(knowledge_points, solve_history)

    def _statistical_estimate(
        self,
        knowledge_points: list[str],
        solve_history: list[dict],
    ) -> dict[str, float]:
        """基于简单统计的掌握度估算。

        对每个知识点，统计正确率作为掌握度近似。
        """
        mastery: dict[str, float] = {}

        for kp in knowledge_points:
            total = 0
            correct = 0
            for record in solve_history:
                record_kps = record.get("knowledge_points", "")
                if kp in record_kps:
                    total += 1
                    if record.get("status") == "verified":
                        correct += 1
            # 默认掌握度 0.5（无数据时）
            mastery[kp] = correct / total if total > 0 else 0.5

        return mastery

    async def _pykt_estimate(
        self,
        user_id: str,
        knowledge_points: list[str],
        solve_history: list[dict],
    ) -> dict[str, float]:
        """使用 pyKT 模型估算掌握度（预留接口）。"""
        # TODO: 数据充足后集成 pyKT 模型
        logger.warning("pyKT 模型尚未集成, 降级为统计估算")
        return self._statistical_estimate(knowledge_points, solve_history)
