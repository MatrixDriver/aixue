# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AIXue（爱学）— AI 辅助学生学习的教育平台，面向初中和高中学生。

核心功能：
- **智能解题**：上传题目图片或输入文本 → OCR 识别 → 学科判定 → 分策略解题（数学用 SymPy 验证，其他学科走通用解题器）→ 支持苏格拉底式引导和直接解答两种模式
- **学情诊断**：基于解题记录的五维错因分析（知识盲区、思维模式、概念关联、习惯分析、认知水平），支持试卷图片导入

## 技术栈

- **后端**：FastAPI + SQLAlchemy (async) + PostgreSQL (生产) / SQLite (测试)
- **前端**：Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 + KaTeX (数学公式渲染)
- **LLM**：通过 OpenRouter (OpenAI 兼容 API) 调用多模型，默认 Gemini 系列
- **数学验证**：SymPy（LaTeX 解析 → 符号求解 → 答案比对）
- **部署**：Railway (Docker)，双远程源 GitHub + Gitee
- **包管理**：后端 uv，前端 npm

## 开发命令

```bash
# 后端
uv sync                                    # 安装依赖
uv run uvicorn aixue.main:app --reload     # 启动开发服务器 (端口 8000)
uv run pytest                              # 运行全部测试
uv run pytest tests/test_api/test_auth.py  # 运行单个测试文件
uv run pytest -k "test_login"              # 按名称匹配运行测试
uv run ruff check src/                     # Lint
uv run mypy .                              # 类型检查

# 前端
cd frontend && npm install                 # 安装依赖
cd frontend && npm run dev                 # 启动开发服务器
cd frontend && npm run build               # 构建

# Docker（本地完整环境含 PostgreSQL）
docker compose up
```

## 架构

### 后端 (`src/aixue/`)

```
main.py              — FastAPI 入口，lifespan 自动建表，CORS，全局异常处理
config.py            — pydantic-settings 配置，从 .env 加载
dependencies.py      — JWT 认证依赖注入
api/router.py        — 路由聚合（auth, users, solver, diagnosis, problems）
api/endpoints/       — 各 API 端点
services/
  llm_service.py     — OpenRouter LLM 封装（chat/stream/图片识别），空 choices 自动重试
  solver_service.py  — 解题主控：协调 OCR → 学科判定 → 解题器 → 保存记录
  ocr_service.py     — 多模态 LLM 图片识别，支持聚焦指定题目
  math_solver.py     — 数学解题：SymPy 前置求解 → LLM 生成 → 验证重试循环
  general_solver.py  — 非数学学科通用解题器
  verifier.py        — SymPy 数学验证（前置求解、步骤验证、答案比对）
  diagnosis_service.py — 学情诊断：记录聚合 → LLM 五维分析 → 报告保存
  auth_service.py    — JWT 签发/验证，bcrypt 密码哈希
  user_service.py    — 用户 CRUD
prompts/             — LLM Prompt 模板（system, socratic, direct, diagnosis）
models/              — SQLAlchemy ORM 模型（User, SolvingSession, Message, Problem, DiagnosticReport）
db/                  — 数据库引擎和会话工厂（自动修正 Railway 的 postgresql:// → asyncpg://）
migrations/          — Alembic 迁移（当前使用 lifespan 自动建表，暂无版本迁移文件）
```

### 前端 (`frontend/src/`)

Next.js App Router 结构，主要页面：`(auth)` 登录注册、`(main)` 主界面、`chat` 解题对话、`diagnosis` 学情诊断、`question_bank` 题库。KaTeX 渲染数学公式，Recharts 渲染图表。

### 关键数据流

1. **解题流程**：`solver endpoint` → `SolverService.solve()` → `OCRService`（图片识别）→ `detect_subject()`（学科判定，用 light 模型）→ `MathSolver`/`GeneralSolver` → 保存 `SolvingSession` + `Message`
2. **数学验证**：`MathVerifier.pre_solve()` 用 SymPy 获取真值 → LLM 解题时附带 SymPy hint → 结果通过 `\boxed{}` 提取答案与 SymPy 结果比对 → 不一致则重试（最多 3 次）

## 测试

- 测试使用 SQLite 内存数据库（`sqlite+aiosqlite:///:memory:`），通过 FastAPI 依赖覆盖注入
- `conftest.py` 提供 `db_session`、`client`、`auth_token`、`auth_headers` 等 fixtures
- pytest-asyncio 使用 `asyncio_mode = "auto"`

## 仓库信息

- 主分支：master
- 远程源：GitHub (zhuqingxun/aixue) + Gitee (sean515/aixue)，推送时需同步两个远程源
- 环境变量参考：`.env.example`

## 代码规范

- 所有注释和文档使用中文，变量名和函数名使用英文
- Python 代码使用类型提示，遵循 PEP 8
- Ruff：target Python 3.12，line-length 100
- 使用 `logging.getLogger(__name__)` 创建模块级 logger，日志配置集中在 `main.py`
