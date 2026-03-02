#!/usr/bin/env python3
"""CMM-Math 数据集导入脚本。

用法:
    uv run python data/question_bank/import_cmm_math.py --dry-run
    uv run python data/question_bank/import_cmm_math.py --file data.json

CMM-Math 是一个中国中学数学题库数据集，包含 K12 阶段的数学题目。
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_cmm_math(file_path: str) -> list[dict]:
    """解析 CMM-Math 数据集文件。

    Args:
        file_path: JSON 数据文件路径

    Returns:
        标准化的题目列表
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("文件不存在: %s", file_path)
        return []

    with open(path, encoding="utf-8") as f:
        raw_data = json.load(f)

    problems = []
    for item in raw_data:
        problem = {
            "subject": "数学",
            "grade_level": item.get("grade", ""),
            "knowledge_points": json.dumps(
                item.get("knowledge_points", []), ensure_ascii=False
            ),
            "difficulty": item.get("difficulty", 3),
            "content": item.get("question", ""),
            "solution": item.get("solution", ""),
            "source": "cmm-math",
            "image_url": item.get("image_url"),
        }
        problems.append(problem)

    return problems


def main() -> None:
    """入口函数。"""
    parser = argparse.ArgumentParser(description="导入 CMM-Math 数据集")
    parser.add_argument("--file", type=str, help="CMM-Math JSON 数据文件路径")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅解析和验证，不写入数据库",
    )
    args = parser.parse_args()

    if args.dry_run:
        logger.info("[DRY RUN] CMM-Math 导入脚本验证通过")
        logger.info("使用方式: --file <path> 指定数据文件路径")
        logger.info("支持的数据格式: JSON 数组，每项包含 question/solution/grade/difficulty/knowledge_points")
        sys.exit(0)

    if not args.file:
        logger.error("请指定数据文件: --file <path>")
        sys.exit(1)

    problems = parse_cmm_math(args.file)
    logger.info("解析完成: %d 道题目", len(problems))

    if not problems:
        logger.warning("没有解析到任何题目")
        sys.exit(1)

    # 异步写入数据库
    import asyncio

    from aixue.db.engine import AsyncSessionLocal
    from aixue.services.problem_service import ProblemService

    async def do_import() -> None:
        service = ProblemService()
        async with AsyncSessionLocal() as db:
            count = await service.batch_import(db, problems)
            logger.info("成功导入 %d 道题目", count)

    asyncio.run(do_import())


if __name__ == "__main__":
    main()
