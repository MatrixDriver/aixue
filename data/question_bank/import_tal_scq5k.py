#!/usr/bin/env python3
"""TAL-SCQ5K-CN 数据集导入脚本。

用法:
    uv run python data/question_bank/import_tal_scq5k.py --dry-run
    uv run python data/question_bank/import_tal_scq5k.py --file data.json

TAL-SCQ5K-CN 是好未来(TAL)发布的中国小学/初中数学选择题数据集。
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_tal_scq5k(file_path: str) -> list[dict]:
    """解析 TAL-SCQ5K-CN 数据集文件。

    Args:
        file_path: JSON/JSONL 数据文件路径

    Returns:
        标准化的题目列表
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("文件不存在: %s", file_path)
        return []

    problems = []

    # 支持 JSON 和 JSONL 格式
    if path.suffix == ".jsonl":
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    problems.append(_normalize(item))
    else:
        with open(path, encoding="utf-8") as f:
            raw_data = json.load(f)
        if isinstance(raw_data, list):
            for item in raw_data:
                problems.append(_normalize(item))

    return problems


def _normalize(item: dict) -> dict:
    """将 TAL-SCQ5K 格式标准化为统一格式。"""
    # TAL-SCQ5K 格式: question_text, options, answer, knowledge_points
    content = item.get("question_text", item.get("question", ""))

    # 拼接选项
    options = item.get("options", [])
    if options:
        option_labels = "ABCDEFGH"
        option_text = "\n".join(
            f"{option_labels[i]}. {opt}" for i, opt in enumerate(options)
        )
        content = f"{content}\n\n{option_text}"

    # 拼接答案
    answer = item.get("answer", "")
    solution = f"正确答案: {answer}"
    if item.get("solution"):
        solution = item["solution"]

    return {
        "subject": "数学",
        "grade_level": item.get("grade", item.get("grade_level", "")),
        "knowledge_points": json.dumps(
            item.get("knowledge_points", []), ensure_ascii=False
        )
        if isinstance(item.get("knowledge_points"), list)
        else item.get("knowledge_points", ""),
        "difficulty": item.get("difficulty", 3),
        "content": content,
        "solution": solution,
        "source": "tal-scq5k",
        "image_url": item.get("image_url"),
    }


def main() -> None:
    """入口函数。"""
    parser = argparse.ArgumentParser(description="导入 TAL-SCQ5K-CN 数据集")
    parser.add_argument("--file", type=str, help="TAL-SCQ5K JSON/JSONL 数据文件路径")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅解析和验证，不写入数据库",
    )
    args = parser.parse_args()

    if args.dry_run:
        logger.info("[DRY RUN] TAL-SCQ5K-CN 导入脚本验证通过")
        logger.info("使用方式: --file <path> 指定数据文件路径")
        logger.info("支持的格式: JSON 数组 或 JSONL, 每项包含 question_text/options/answer/knowledge_points")
        sys.exit(0)

    if not args.file:
        logger.error("请指定数据文件: --file <path>")
        sys.exit(1)

    problems = parse_tal_scq5k(args.file)
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
