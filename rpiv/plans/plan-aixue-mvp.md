---
description: "功能实施计划: AIXue MVP"
status: pending
created_at: 2026-03-02T18:45:00
updated_at: 2026-03-02T18:45:00
archived_at: null
related_files:
  - rpiv/requirements/prd-aixue-mvp.md
  - rpiv/research-aixue-mvp.md
---

# 功能：AIXue MVP 全功能实现

以下计划应该是完整的，但在开始实施之前，验证文档和代码库模式以及任务合理性非常重要。

特别注意现有工具、类型和模型的命名。从正确的文件导入等。

## 功能描述

AIXue（爱学）MVP 是一个 AI 驱动的个性化学习助手 Web 应用，面向初高中学生。核心功能包括：

1. **智能解题**：拍照上传题目，AI 识别并给出经验证的解题步骤，支持苏格拉底式引导和完整解答两种模式，支持多轮追问
2. **学情诊断**：基于解题记录和试卷上传，进行五维错因分析，生成诊断报告并推荐练习题
3. **用户系统**：多用户注册登录、年级 profile、解题历史、数据隔离

技术架构采用 FastAPI（后端）+ Next.js（前端）+ PostgreSQL（数据库），部署于 Railway。

## 用户故事

见 PRD 文档 `rpiv/requirements/prd-aixue-mvp.md` 第 5 节，共 8 个用户故事覆盖解题、诊断、用户管理三大场景。

## 问题陈述

初高中学生日常学习中遇到难题缺少即时、高质量、零偏差的讲解辅导。现有 AI 解题工具存在幻觉风险，且缺乏真正个性化的学情诊断能力。

## 解决方案陈述

构建一个前后端分离的 Web 应用，后端使用 FastAPI 集成多模态 LLM（Claude Sonnet 4.6）+ SymPy 数学验证引擎，前端使用 Next.js 提供 KaTeX 数学公式渲染和流畅的对话体验。通过三级交叉验证（SymPy + assert + 可选 Lean 4）确保数学解题正确性。基于 pyKT 知识追踪和五维错因分析提供精准学情诊断。

## 功能元数据

**功能类型**：新功能
**估计复杂度**：高
**主要受影响的系统**：后端 API、前端 UI、数据库、LLM 集成、数学验证引擎、知识追踪模型
**依赖项**：FastAPI、Next.js、SQLAlchemy 2.0、asyncpg、PostgreSQL、Anthropic SDK、SymPy、Pix2Text、pyKT、KaTeX、bcrypt、PyJWT、Alembic

---

## 上下文参考

### 相关代码库文件

当前代码库处于初始化阶段，无现有业务代码。以下为已有文件：

- `CLAUDE.md` - 项目配置和开发规范
- `rpiv/requirements/prd-aixue-mvp.md` - 完整的产品需求文档
- `rpiv/research-aixue-mvp.md` - 技术可行性调研报告
- `docs/research-industry-analysis.md` - 行业调研报告

### 要创建的新文件

**后端（Python/FastAPI）：**

```
aixue/
  pyproject.toml                          # uv 项目配置
  alembic.ini                             # 数据库迁移配置
  Dockerfile                              # Docker 构建文件
  .env.example                            # 环境变量模板
  src/
    aixue/
      __init__.py
      main.py                             # FastAPI 应用入口
      config.py                           # 配置管理（Pydantic Settings）
      dependencies.py                     # FastAPI 依赖注入
      db/
        __init__.py
        engine.py                         # async SQLAlchemy 引擎
        session.py                        # 会话管理
        base.py                           # 模型基类
      models/
        __init__.py
        user.py                           # 用户 ORM 模型
        problem.py                        # 题目 ORM 模型
        session.py                        # 解题会话 ORM 模型
        message.py                        # 对话消息 ORM 模型
        diagnosis.py                      # 学情诊断 ORM 模型
      schemas/
        __init__.py
        user.py                           # 用户 Pydantic schema
        problem.py                        # 题目 schema
        session.py                        # 会话 schema
        diagnosis.py                      # 诊断 schema
        auth.py                           # 认证 schema
      api/
        __init__.py
        router.py                         # 总路由
        endpoints/
          __init__.py
          auth.py                         # 登录/注册端点
          users.py                        # 用户管理端点
          solver.py                       # 解题端点
          diagnosis.py                    # 学情诊断端点
          problems.py                     # 题库端点
      services/
        __init__.py
        auth_service.py                   # 认证服务（JWT + bcrypt）
        user_service.py                   # 用户管理服务
        llm_service.py                    # LLM API 调用封装
        solver_service.py                 # 解题服务主控
        math_solver.py                    # 数学深度解题
        general_solver.py                 # 理化生通用解题
        verifier.py                       # SymPy 验证模块
        ocr_service.py                    # OCR 识别服务
        diagnosis_service.py              # 学情诊断服务
        knowledge_tracer.py               # 知识追踪服务
        recommender.py                    # 练习题推荐服务
        problem_service.py                # 题库管理服务
      prompts/
        __init__.py
        socratic.py                       # 苏格拉底引导 Prompt 模板
        direct.py                         # 完整解答 Prompt 模板
        diagnosis.py                      # 学情分析 Prompt 模板
        system.py                         # 系统 Prompt（角色设定）
      migrations/
        versions/                         # Alembic 迁移版本
        env.py                            # Alembic 环境配置
  tests/
    __init__.py
    conftest.py                           # pytest fixtures
    test_services/
      __init__.py
      test_auth_service.py
      test_solver_service.py
      test_verifier.py
      test_diagnosis_service.py
    test_api/
      __init__.py
      test_auth.py
      test_solver.py
      test_diagnosis.py
  data/
    question_bank/
      import_cmm_math.py                 # CMM-Math 数据导入脚本
      import_tal_scq5k.py                # TAL-SCQ5K 导入脚本
```

**前端（Next.js/React/TypeScript）：**

```
frontend/
  package.json
  tsconfig.json
  next.config.ts
  tailwind.config.ts
  .env.local.example
  src/
    app/
      layout.tsx                          # 根布局
      page.tsx                            # 首页/登录
      (auth)/
        login/page.tsx                    # 登录页
        register/page.tsx                 # 注册页
      (main)/
        layout.tsx                        # 主布局（含侧边栏）
        solve/page.tsx                    # 解题页面
        history/page.tsx                  # 解题历史
        diagnosis/page.tsx                # 学情诊断报告
        profile/page.tsx                  # 个人信息
    components/
      ui/                                 # 基础 UI 组件
        button.tsx
        input.tsx
        card.tsx
        dialog.tsx
      chat/
        chat-container.tsx                # 对话容器
        chat-message.tsx                  # 消息气泡（含 LaTeX 渲染）
        chat-input.tsx                    # 输入框（含图片上传）
        image-upload.tsx                  # 图片上传组件
        mode-switch.tsx                   # 苏格拉底/完整解答切换
      diagnosis/
        radar-chart.tsx                   # 知识点雷达图
        report-card.tsx                   # 诊断报告卡片
        weak-point-list.tsx               # 薄弱知识点列表
        exercise-recommend.tsx            # 练习推荐列表
      layout/
        sidebar.tsx                       # 侧边栏导航
        header.tsx                        # 顶部导航栏
    lib/
      api.ts                              # API 客户端
      auth.ts                             # 认证工具
      types.ts                            # TypeScript 类型定义
      utils.ts                            # 工具函数
    hooks/
      use-auth.ts                         # 认证 Hook
      use-chat.ts                         # 对话 Hook
      use-diagnosis.ts                    # 诊断 Hook
    styles/
      globals.css                         # 全局样式 + Tailwind
```

### 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
  - 异步数据库、依赖注入、文件上传
- [Anthropic Python SDK](https://docs.anthropic.com/en/docs/build-with-claude/vision)
  - Vision API 图片输入、Messages API 多轮对话
- [SymPy parse_latex](https://docs.sympy.org/latest/modules/parsing.html#sympy.parsing.latex.parse_latex)
  - LaTeX 到 SymPy 表达式转换
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - 异步引擎和会话管理
- [Next.js App Router](https://nextjs.org/docs/app)
  - App Router 路由和布局
- [KaTeX](https://katex.org/docs/api.html)
  - LaTeX 渲染 API
- [react-katex](https://www.npmjs.com/package/react-katex)
  - React KaTeX 组件
- [pyKT](https://pykt-toolkit.readthedocs.io/)
  - 知识追踪模型使用指南

### 要遵循的模式

**命名约定：**
- Python：snake_case（变量、函数、文件名），PascalCase（类名）
- TypeScript：camelCase（变量、函数），PascalCase（组件、类型）
- 所有注释和文档使用中文
- 变量名和函数名使用英文

**错误处理：**
- FastAPI：使用 HTTPException + 自定义异常处理器
- SymPy 验证失败：自动重试最多 3 次
- LLM API 调用：SDK 内置重试 + 自定义超时

**日志记录：**
- `logging.getLogger(__name__)` 创建模块级 logger
- 异常用 `logger.exception()`
- 日志配置集中在 `main.py` 入口执行一次

**API 设计：**
- RESTful 风格
- 请求/响应使用 Pydantic schema
- 认证使用 JWT Bearer Token

---

## 实施计划

### 阶段 1：基础框架与用户系统

搭建项目骨架，包含 Python 后端（FastAPI + SQLAlchemy + PostgreSQL）、前端（Next.js）、用户注册登录、基础页面框架。

**任务：**
- 初始化 Python 后端项目（pyproject.toml、目录结构、依赖）
- 初始化 Next.js 前端项目
- 配置数据库连接和 ORM 模型
- 实现用户注册/登录 API（JWT 认证）
- 实现前端登录/注册页面
- 实现主布局（侧边栏导航）
- 配置 LLM 服务封装
- 配置管理和日志系统

### 阶段 2：智能解题核心

实现完整的解题流程：图片上传 -> OCR 识别 -> 学科判定 -> 分策略解题 -> 验证 -> 输出。

**任务：**
- 图片上传 API 和前端组件
- 多模态 LLM 题目识别
- 学科自动判定
- 数学深度解题 + SymPy 三级验证管线
- 理化生基础解题
- 苏格拉底引导模式 Prompt 设计
- 完整解答模式 Prompt 设计
- 多轮追问（会话上下文管理）
- 前端对话界面 + KaTeX 渲染
- 解题历史保存和展示

### 阶段 3：学情诊断与题库

实现学情分析闭环：试卷导入、对错判定、五维错因分析、诊断报告、练习推荐。

**任务：**
- 题库数据导入（CMM-Math + TAL-SCQ5K-CN）
- 题目数据模型和管理 API
- 试卷上传和自动识别
- 对错自动判定 + 手动修正
- 五维错因分析引擎
- 学情诊断报告生成
- 练习题推荐引擎
- LLM 变式题生成 + CAS 验证
- 前端诊断报告页面（雷达图 + 薄弱点列表 + 推荐题目）
- pyKT 知识追踪集成（数据充足后启用）

### 阶段 4：集成部署与打磨

全功能集成、Railway 部署、用户体验优化。

**任务：**
- Docker 化后端和前端
- Railway 部署配置（PostgreSQL + Volume + 环境变量）
- 全功能集成测试
- 响应式布局适配（移动端拍照场景）
- 加载状态、错误提示优化
- 性能优化（流式输出、图片压缩）

---

## 逐步任务

### 任务 1：CREATE 后端项目骨架

- **IMPLEMENT**：初始化 `pyproject.toml`，配置 uv 包管理器和所有依赖项
  ```toml
  [project]
  name = "aixue"
  version = "0.1.0"
  requires-python = ">=3.12"
  dependencies = [
      "fastapi>=0.115.0",
      "uvicorn[standard]>=0.30.0",
      "sqlalchemy[asyncio]>=2.0.0",
      "asyncpg>=0.30.0",
      "alembic>=1.14.0",
      "pydantic>=2.0.0",
      "pydantic-settings>=2.0.0",
      "anthropic>=0.40.0",
      "sympy>=1.13.0",
      "pyjwt>=2.9.0",
      "bcrypt>=4.2.0",
      "python-multipart>=0.0.12",
      "pillow>=11.0.0",
      "httpx>=0.27.0",
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=8.0.0",
      "pytest-asyncio>=0.24.0",
      "pytest-cov>=6.0.0",
      "httpx>=0.27.0",
      "mypy>=1.13.0",
      "ruff>=0.8.0",
  ]

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.hatch.build.targets.wheel]
  packages = ["src/aixue"]
  ```
- **IMPLEMENT**：创建完整目录结构（参见上方"要创建的新文件"）
- **IMPORTS**：所有子模块的 `__init__.py`
- **VALIDATE**：`cd D:/CODE/aixue && uv sync && uv run python -c "import aixue; print('OK')"`

### 任务 2：CREATE 配置管理模块

- **IMPLEMENT**：`src/aixue/config.py`，使用 Pydantic Settings 管理环境变量
  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      # 数据库
      database_url: str = "postgresql+asyncpg://localhost/aixue"
      # LLM
      anthropic_api_key: str = ""
      openai_api_key: str = ""
      llm_model: str = "claude-sonnet-4-6-20250514"
      llm_model_light: str = "claude-haiku-4-5-20251001"
      # 认证
      secret_key: str = "change-me-in-production"
      jwt_algorithm: str = "HS256"
      jwt_expire_minutes: int = 1440  # 24 小时
      # 验证
      max_retry_count: int = 3
      sympy_timeout: int = 10
      # 文件上传
      upload_dir: str = "/app/uploads"
      max_image_size: int = 5 * 1024 * 1024  # 5MB

      model_config = {"env_file": ".env"}
  ```
- **IMPLEMENT**：`.env.example` 模板文件
- **VALIDATE**：`uv run python -c "from aixue.config import Settings; s = Settings(); print(s.llm_model)"`

### 任务 3：CREATE 数据库引擎与基础模型

- **IMPLEMENT**：`src/aixue/db/engine.py` — async SQLAlchemy 引擎
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
  from aixue.config import Settings

  settings = Settings()
  engine = create_async_engine(settings.database_url, echo=False)
  AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
  ```
- **IMPLEMENT**：`src/aixue/db/base.py` — 声明式基类
  ```python
  from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
  from datetime import datetime
  import uuid

  class Base(DeclarativeBase):
      pass

  class TimestampMixin:
      created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
      updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
  ```
- **IMPLEMENT**：`src/aixue/db/session.py` — 会话依赖注入
  ```python
  from typing import AsyncGenerator
  from sqlalchemy.ext.asyncio import AsyncSession
  from aixue.db.engine import AsyncSessionLocal

  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with AsyncSessionLocal() as session:
          yield session
  ```
- **VALIDATE**：`uv run python -c "from aixue.db.engine import engine; print(engine.url)"`

### 任务 4：CREATE ORM 数据模型

- **IMPLEMENT**：`src/aixue/models/user.py`
  ```python
  from sqlalchemy import String, ARRAY
  from sqlalchemy.orm import Mapped, mapped_column, relationship
  from aixue.db.base import Base, TimestampMixin
  import uuid

  class User(Base, TimestampMixin):
      __tablename__ = "users"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
      username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
      password_hash: Mapped[str] = mapped_column(String(128))
      name: Mapped[str] = mapped_column(String(100))
      grade: Mapped[str] = mapped_column(String(20))  # 初一~高三
      subjects: Mapped[str] = mapped_column(String(200))  # 逗号分隔的学科列表

      sessions = relationship("SolvingSession", back_populates="user")
      diagnostics = relationship("DiagnosticReport", back_populates="user")
  ```
- **IMPLEMENT**：`src/aixue/models/session.py` — 解题会话模型
  ```python
  class SolvingSession(Base, TimestampMixin):
      __tablename__ = "solving_sessions"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=...)
      user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
      subject: Mapped[str] = mapped_column(String(20))  # 数学/物理/化学/生物
      topic: Mapped[str | None] = mapped_column(String(200))
      mode: Mapped[str] = mapped_column(String(20), default="socratic")  # socratic/direct
      image_path: Mapped[str | None] = mapped_column(String(500))
      question_text: Mapped[str | None] = mapped_column(Text)
      verified_answer: Mapped[str | None] = mapped_column(Text)
      verification_status: Mapped[str] = mapped_column(String(20), default="pending")
      confidence: Mapped[float | None] = mapped_column(Float)

      user = relationship("User", back_populates="sessions")
      messages = relationship("Message", back_populates="session", order_by="Message.created_at")
  ```
- **IMPLEMENT**：`src/aixue/models/message.py` — 对话消息模型
  ```python
  class Message(Base, TimestampMixin):
      __tablename__ = "messages"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=...)
      session_id: Mapped[str] = mapped_column(ForeignKey("solving_sessions.id"))
      role: Mapped[str] = mapped_column(String(20))  # user/assistant/system
      content: Mapped[str] = mapped_column(Text)
      image_path: Mapped[str | None] = mapped_column(String(500))
      token_count: Mapped[int | None] = mapped_column(Integer)

      session = relationship("SolvingSession", back_populates="messages")
  ```
- **IMPLEMENT**：`src/aixue/models/problem.py` — 题库模型
  ```python
  class Problem(Base, TimestampMixin):
      __tablename__ = "problems"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=...)
      subject: Mapped[str] = mapped_column(String(20), index=True)
      grade_level: Mapped[str] = mapped_column(String(20))
      knowledge_points: Mapped[str] = mapped_column(Text)  # JSON 数组
      difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
      content: Mapped[str] = mapped_column(Text)  # LaTeX 格式题目
      solution: Mapped[str | None] = mapped_column(Text)
      source: Mapped[str] = mapped_column(String(50))  # cmm-math / tal-scq5k / user / generated
      image_url: Mapped[str | None] = mapped_column(String(500))
  ```
- **IMPLEMENT**：`src/aixue/models/diagnosis.py` — 学情诊断模型
  ```python
  class DiagnosticReport(Base, TimestampMixin):
      __tablename__ = "diagnostic_reports"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=...)
      user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
      scope: Mapped[str] = mapped_column(String(20))  # full/subject/recent
      subject: Mapped[str | None] = mapped_column(String(20))
      overall_score: Mapped[float | None] = mapped_column(Float)
      knowledge_gaps: Mapped[str | None] = mapped_column(Text)  # JSON
      thinking_patterns: Mapped[str | None] = mapped_column(Text)  # JSON
      habit_analysis: Mapped[str | None] = mapped_column(Text)  # JSON
      cognitive_level: Mapped[str | None] = mapped_column(Text)  # JSON
      recommendations: Mapped[str | None] = mapped_column(Text)  # JSON - 推荐题目ID列表

      user = relationship("User", back_populates="diagnostics")
  ```
- **IMPLEMENT**：`src/aixue/models/__init__.py` — 导出所有模型
- **VALIDATE**：`uv run python -c "from aixue.models import User, SolvingSession, Message, Problem, DiagnosticReport; print('All models imported')"`

### 任务 5：CREATE Alembic 迁移配置

- **IMPLEMENT**：`alembic.ini` — 数据库迁移配置
- **IMPLEMENT**：`src/aixue/migrations/env.py` — Alembic 环境（async 模式）
- **IMPLEMENT**：生成初始迁移文件
- **GOTCHA**：Alembic async 模式需要在 `env.py` 中使用 `run_async_migrations`
- **VALIDATE**：`cd D:/CODE/aixue && uv run alembic revision --autogenerate -m "initial" && uv run alembic upgrade head`

### 任务 6：CREATE 认证服务

- **IMPLEMENT**：`src/aixue/services/auth_service.py`
  - `hash_password(password: str) -> str` — bcrypt 加密
  - `verify_password(password: str, hashed: str) -> bool` — 密码验证
  - `create_access_token(user_id: str) -> str` — JWT 令牌生成
  - `decode_access_token(token: str) -> str` — JWT 解码和验证
- **IMPLEMENT**：`src/aixue/schemas/auth.py` — LoginRequest、RegisterRequest、TokenResponse
- **IMPLEMENT**：`src/aixue/api/endpoints/auth.py`
  - `POST /api/auth/register` — 用户注册
  - `POST /api/auth/login` — 用户登录，返回 JWT
- **IMPLEMENT**：`src/aixue/dependencies.py` — `get_current_user` 依赖注入
- **VALIDATE**：`uv run pytest tests/test_services/test_auth_service.py -v`

### 任务 7：CREATE 用户管理服务

- **IMPLEMENT**：`src/aixue/services/user_service.py`
  - `create_user(db, register_data) -> User`
  - `get_user_by_username(db, username) -> User | None`
  - `get_user_profile(db, user_id) -> User`
  - `update_user_profile(db, user_id, profile_data) -> User`
- **IMPLEMENT**：`src/aixue/schemas/user.py` — UserCreate、UserProfile、UserResponse
- **IMPLEMENT**：`src/aixue/api/endpoints/users.py`
  - `GET /api/users/me` — 获取当前用户信息
  - `PUT /api/users/me` — 更新个人信息
  - `GET /api/users/me/stats` — 获取解题统计
- **VALIDATE**：`uv run pytest tests/test_services/ -v`

### 任务 8：CREATE FastAPI 应用入口

- **IMPLEMENT**：`src/aixue/main.py`
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from aixue.api.router import api_router
  from aixue.config import Settings
  import logging

  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  settings = Settings()
  app = FastAPI(title="AIXue API", version="0.1.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # MVP 阶段允许所有来源
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(api_router, prefix="/api")
  ```
- **IMPLEMENT**：`src/aixue/api/router.py` — 总路由聚合
- **VALIDATE**：`uv run uvicorn aixue.main:app --host 0.0.0.0 --port 8000` 然后访问 `/docs` 查看 Swagger

### 任务 9：CREATE LLM 服务封装

- **IMPLEMENT**：`src/aixue/services/llm_service.py`
  ```python
  import anthropic
  from aixue.config import Settings

  class LLMService:
      def __init__(self):
          self.settings = Settings()
          self.client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)

      async def chat(
          self,
          messages: list[dict],
          system: str | None = None,
          model: str | None = None,
          max_tokens: int = 4096,
      ) -> str:
          """发送消息并获取完整响应"""
          ...

      async def chat_stream(
          self,
          messages: list[dict],
          system: str | None = None,
          model: str | None = None,
          max_tokens: int = 4096,
      ) -> AsyncGenerator[str, None]:
          """流式发送消息"""
          ...

      async def recognize_image(
          self,
          image_data: bytes,
          media_type: str,
          prompt: str,
      ) -> str:
          """多模态 LLM 图片识别"""
          ...
  ```
- **GOTCHA**：使用 `anthropic.AsyncAnthropic` 而非同步客户端，与 FastAPI 的 async 架构一致
- **GOTCHA**：图片 base64 编码后传入 Vision API，注意 5MB 限制
- **VALIDATE**：`uv run python -c "from aixue.services.llm_service import LLMService; print('LLM service created')"`

### 任务 10：CREATE SymPy 验证模块

- **IMPLEMENT**：`src/aixue/services/verifier.py`
  ```python
  import asyncio
  from sympy import symbols, solve, simplify, latex, N
  from sympy.parsing.latex import parse_latex

  class MathVerifier:
      async def pre_solve(self, question_latex: str) -> dict | None:
          """第一级：SymPy 前置求解，获取数学真值"""
          loop = asyncio.get_event_loop()
          return await loop.run_in_executor(None, self._sympy_solve, question_latex)

      async def verify_steps(self, steps: list[dict]) -> list[dict]:
          """第二级：对关键步骤进行 assert 断言验证"""
          ...

      def _sympy_solve(self, latex_expr: str) -> dict | None:
          """同步 SymPy 求解（在 executor 中运行）"""
          try:
              expr = parse_latex(latex_expr)
              # 尝试求解
              result = solve(expr)
              return {"solved": True, "result": result, "latex": latex(result)}
          except Exception:
              return None

      async def verify_answer(self, student_answer: str, correct_answer: str) -> bool:
          """验证学生答案是否正确"""
          loop = asyncio.get_event_loop()
          return await loop.run_in_executor(
              None, self._compare_answers, student_answer, correct_answer
          )
  ```
- **GOTCHA**：SymPy 是同步库，必须在 `run_in_executor` 中运行以避免阻塞事件循环
- **GOTCHA**：`parse_latex` 可能无法处理所有 LaTeX 格式，需要 try/except 并降级到 LLM 输出 SymPy 代码
- **GOTCHA**：设置超时（asyncio.wait_for + Settings.sympy_timeout），防止复杂表达式导致卡死
- **VALIDATE**：`uv run pytest tests/test_services/test_verifier.py -v`

### 任务 11：CREATE Prompt 模板系统

- **IMPLEMENT**：`src/aixue/prompts/system.py` — 系统角色设定
  ```python
  SYSTEM_PROMPT = """你是 AIXue（爱学），一位专业的 AI 学习辅导助手。

  你的学生信息：
  - 姓名：{student_name}
  - 年级：{grade}
  - 重点学科：{subjects}

  核心原则：
  1. 所有回答使用中文
  2. 数学公式使用 LaTeX 格式（用 $ 或 $$ 包裹）
  3. 根据学生年级调整讲解深度，不引用超出其学习范围的知识
  4. 每个步骤标注使用的定理或知识点
  5. 如果不确定答案，明确标注置信度
  """
  ```
- **IMPLEMENT**：`src/aixue/prompts/socratic.py` — 苏格拉底引导模式
  ```python
  SOCRATIC_PROMPT = """你正在使用苏格拉底式引导法帮助学生理解这道题。

  规则：
  1. 不要直接给出答案或完整解题步骤
  2. 通过提问引导学生思考：
     - "你能从题目中找出哪些已知条件？"
     - "这道题涉及哪些知识点？"
     - "如果我们用 XX 方法，下一步应该怎么做？"
  3. 学生每回答一个问题，给予反馈后继续引导下一步
  4. 当学生完全卡住时，给出一个关键提示（而非答案）
  5. 学生到达正确答案时，总结解题思路和关键知识点

  {sympy_hint}
  """
  ```
- **IMPLEMENT**：`src/aixue/prompts/direct.py` — 完整解答模式
  ```python
  DIRECT_PROMPT = """请给出这道题的完整解答过程。

  格式要求：
  1. 分步骤编号（第一步、第二步...）
  2. 每步标注使用的定理/知识点（用【】括起）
  3. 计算过程使用 LaTeX 公式
  4. 最终答案用 \\boxed{} 框起

  {sympy_constraint}
  """
  ```
- **IMPLEMENT**：`src/aixue/prompts/diagnosis.py` — 学情分析 Prompt
- **VALIDATE**：`uv run python -c "from aixue.prompts.system import SYSTEM_PROMPT; print(SYSTEM_PROMPT[:50])"`

### 任务 12：CREATE 解题服务

- **IMPLEMENT**：`src/aixue/services/solver_service.py` — 解题主控
  ```python
  class SolverService:
      def __init__(self, llm: LLMService, verifier: MathVerifier):
          self.llm = llm
          self.verifier = verifier

      async def solve(
          self,
          image: bytes | None,
          text: str | None,
          subject: str | None,
          mode: str,  # "socratic" | "direct"
          session_id: str | None,
          user_profile: dict,
          db: AsyncSession,
      ) -> dict:
          """完整解题流程"""
          # 1. 题目识别
          question = await self._recognize(image, text)
          # 2. 学科判定
          subject = subject or await self._detect_subject(question)
          # 3. 分策略解题
          if subject == "数学":
              result = await self._solve_math(question, mode, user_profile)
          else:
              result = await self._solve_general(question, subject, mode, user_profile)
          # 4. 保存记录
          await self._save_session(db, ...)
          return result
  ```
- **IMPLEMENT**：`src/aixue/services/math_solver.py` — 数学深度解题
  ```python
  class MathSolver:
      async def solve(self, question: str, mode: str, user_profile: dict) -> dict:
          # 第一级：SymPy 前置求解
          sympy_result = await self.verifier.pre_solve(question)
          # 构造 Prompt（注入 SymPy 真值作为硬约束）
          prompt = self._build_prompt(question, mode, user_profile, sympy_result)
          # LLM 解题
          for attempt in range(self.max_retries):
              response = await self.llm.chat(messages, system=system_prompt)
              # 第二级：assert 断言验证
              if await self._verify_response(response, sympy_result):
                  return {"steps": response, "verified": True, "attempts": attempt + 1}
          return {"steps": response, "verified": False, "attempts": self.max_retries}
  ```
- **IMPLEMENT**：`src/aixue/services/general_solver.py` — 理化生通用解题
- **VALIDATE**：`uv run pytest tests/test_services/test_solver_service.py -v`

### 任务 13：CREATE 解题 API 端点

- **IMPLEMENT**：`src/aixue/api/endpoints/solver.py`
  ```python
  @router.post("/solve")
  async def solve_problem(
      image: UploadFile | None = File(None),
      text: str | None = Form(None),
      subject: str | None = Form(None),
      mode: str = Form("socratic"),
      session_id: str | None = Form(None),
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> SolveResponse:
      ...

  @router.post("/solve/{session_id}/follow-up")
  async def follow_up(
      session_id: str,
      message: str = Form(...),
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> SolveResponse:
      """多轮追问"""
      ...

  @router.get("/sessions")
  async def list_sessions(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
      subject: str | None = None,
      limit: int = 20,
      offset: int = 0,
  ) -> list[SessionSummary]:
      """解题历史列表"""
      ...

  @router.get("/sessions/{session_id}")
  async def get_session(
      session_id: str,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> SessionDetail:
      """获取完整对话记录"""
      ...
  ```
- **IMPLEMENT**：`src/aixue/schemas/session.py` — SolveRequest、SolveResponse、SessionSummary、SessionDetail
- **VALIDATE**：启动服务器后用 Swagger UI 测试 `/api/solve` 端点

### 任务 14：CREATE 学情诊断服务

- **IMPLEMENT**：`src/aixue/services/diagnosis_service.py`
  ```python
  class DiagnosisService:
      async def analyze(self, user_id: str, scope: str, subject: str | None, db: AsyncSession) -> dict:
          """五维错因分析"""
          # 1. 获取用户解题记录
          records = await self._get_solve_records(db, user_id, scope, subject)
          # 2. 数据量判断
          if len(records) < 20:
              # 冷启动：LLM 基础分析
              return await self._llm_analyze(records)
          else:
              # 充足数据：pyKT + LLM 混合分析
              return await self._hybrid_analyze(records)

      async def import_exam(self, user_id: str, images: list[bytes], db: AsyncSession) -> dict:
          """试卷导入"""
          # 1. 多模态 LLM 识别试卷
          # 2. 提取题目和学生答案
          # 3. AI 自动判定对错
          # 4. 保存到解题记录
          ...

      async def _five_dimension_analysis(self, records: list) -> dict:
          """五维错因分析"""
          # 维度1: 知识漏洞检测
          # 维度2: 思维路径回溯
          # 维度3: 概念关联分析
          # 维度4: 解题习惯诊断
          # 维度5: 认知水平评估
          ...
  ```
- **IMPLEMENT**：`src/aixue/services/recommender.py` — 练习题推荐
  ```python
  class Recommender:
      async def recommend(self, weak_points: list[dict], user_id: str, db: AsyncSession) -> list[Problem]:
          """基于薄弱知识点推荐练习题"""
          # 1. 从题库匹配相关题目
          # 2. 难度递进排序
          # 3. 去除已做过的题目
          # 4. 如题库不足，LLM 生成变式题
          ...
  ```
- **IMPLEMENT**：`src/aixue/services/knowledge_tracer.py` — pyKT 集成封装
- **VALIDATE**：`uv run pytest tests/test_services/test_diagnosis_service.py -v`

### 任务 15：CREATE 学情诊断 API 端点

- **IMPLEMENT**：`src/aixue/api/endpoints/diagnosis.py`
  ```python
  @router.post("/diagnosis/analyze")
  async def run_diagnosis(
      scope: str = Form("full"),
      subject: str | None = Form(None),
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> DiagnosisResponse:
      ...

  @router.post("/diagnosis/import-exam")
  async def import_exam(
      images: list[UploadFile] = File(...),
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> ExamImportResponse:
      ...

  @router.get("/diagnosis/reports")
  async def list_reports(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> list[DiagnosisReportSummary]:
      ...

  @router.get("/diagnosis/reports/{report_id}")
  async def get_report(
      report_id: str,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> DiagnosisReportDetail:
      ...
  ```
- **VALIDATE**：Swagger UI 测试诊断端点

### 任务 16：CREATE 题库管理

- **IMPLEMENT**：`src/aixue/services/problem_service.py` — 题库 CRUD
- **IMPLEMENT**：`src/aixue/api/endpoints/problems.py`
  - `GET /api/problems` — 题目列表（支持按知识点、难度、学科筛选）
  - `GET /api/problems/{id}` — 题目详情
  - `POST /api/problems/generate` — LLM 生成变式题
- **IMPLEMENT**：`data/question_bank/import_cmm_math.py` — CMM-Math 导入脚本
- **IMPLEMENT**：`data/question_bank/import_tal_scq5k.py` — TAL-SCQ5K-CN 导入脚本
- **GOTCHA**：导入脚本需处理 LaTeX 格式转换和知识点标注
- **VALIDATE**：`uv run python data/question_bank/import_cmm_math.py --dry-run`

### 任务 17：CREATE Next.js 前端项目

- **IMPLEMENT**：初始化 Next.js 项目
  ```bash
  cd D:/CODE/aixue
  npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --eslint
  ```
- **IMPLEMENT**：安装依赖
  ```bash
  cd frontend
  npm install react-katex katex axios recharts lucide-react
  npm install -D @types/katex
  ```
- **IMPLEMENT**：配置 `next.config.ts`（API 代理到后端）
- **IMPLEMENT**：配置 Tailwind CSS
- **VALIDATE**：`cd D:/CODE/aixue/frontend && npm run build`

### 任务 18：CREATE 前端认证系统

- **IMPLEMENT**：`frontend/src/lib/api.ts` — Axios API 客户端（含 JWT 拦截器）
- **IMPLEMENT**：`frontend/src/lib/auth.ts` — Token 存储和管理
- **IMPLEMENT**：`frontend/src/hooks/use-auth.ts` — 认证状态 Hook
- **IMPLEMENT**：`frontend/src/app/(auth)/login/page.tsx` — 登录页面
- **IMPLEMENT**：`frontend/src/app/(auth)/register/page.tsx` — 注册页面（含年级和学科选择）
- **IMPLEMENT**：`frontend/src/app/layout.tsx` — 根布局（认证检查）
- **VALIDATE**：`npm run build && npm run dev` 然后浏览器测试登录流程

### 任务 19：CREATE 前端主布局

- **IMPLEMENT**：`frontend/src/components/layout/sidebar.tsx` — 侧边栏导航
  - 导航项：解题、历史记录、学情诊断、个人信息
  - 当前学科显示
  - 用户信息和退出
- **IMPLEMENT**：`frontend/src/components/layout/header.tsx` — 顶部导航栏（移动端汉堡菜单）
- **IMPLEMENT**：`frontend/src/app/(main)/layout.tsx` — 主区域布局
- **VALIDATE**：浏览器查看布局效果

### 任务 20：CREATE 前端解题对话界面

- **IMPLEMENT**：`frontend/src/components/chat/chat-container.tsx` — 对话容器
- **IMPLEMENT**：`frontend/src/components/chat/chat-message.tsx` — 消息气泡
  - 支持 LaTeX 渲染（react-katex）
  - 支持分步骤展示
  - 区分用户消息和 AI 消息
- **IMPLEMENT**：`frontend/src/components/chat/chat-input.tsx` — 输入框
  - 文本输入
  - 图片上传按钮（支持拍照和文件选择）
  - 发送按钮
- **IMPLEMENT**：`frontend/src/components/chat/image-upload.tsx` — 图片上传组件
  - 支持拖拽上传
  - 图片预览和删除
  - 拍照入口（移动端 camera capture）
- **IMPLEMENT**：`frontend/src/components/chat/mode-switch.tsx` — 模式切换
  - 苏格拉底引导 / 完整解答 切换按钮
- **IMPLEMENT**：`frontend/src/hooks/use-chat.ts` — 对话状态管理 Hook
- **IMPLEMENT**：`frontend/src/app/(main)/solve/page.tsx` — 解题页面
- **GOTCHA**：KaTeX 需要在 `layout.tsx` 中引入 CSS：`import 'katex/dist/katex.min.css'`
- **GOTCHA**：处理 LaTeX 分隔符：行内用 `$...$`，独立行用 `$$...$$`，需要自定义正则解析
- **VALIDATE**：浏览器测试完整解题流程（上传图片 -> 获得解答 -> 追问）

### 任务 21：CREATE 前端解题历史页面

- **IMPLEMENT**：`frontend/src/app/(main)/history/page.tsx`
  - 按时间倒序展示解题记录列表
  - 支持按学科筛选
  - 点击记录查看完整对话
- **VALIDATE**：浏览器查看历史记录

### 任务 22：CREATE 前端学情诊断页面

- **IMPLEMENT**：`frontend/src/components/diagnosis/radar-chart.tsx` — 知识点掌握度雷达图（Recharts）
- **IMPLEMENT**：`frontend/src/components/diagnosis/report-card.tsx` — 诊断报告卡片
  - 总体评分
  - 五维分析结果
- **IMPLEMENT**：`frontend/src/components/diagnosis/weak-point-list.tsx` — 薄弱知识点列表
- **IMPLEMENT**：`frontend/src/components/diagnosis/exercise-recommend.tsx` — 推荐练习题列表
- **IMPLEMENT**：`frontend/src/hooks/use-diagnosis.ts` — 诊断数据 Hook
- **IMPLEMENT**：`frontend/src/app/(main)/diagnosis/page.tsx`
  - 触发诊断分析按钮
  - 试卷上传入口
  - 历史报告列表
  - 诊断报告详情展示
- **VALIDATE**：浏览器测试诊断流程

### 任务 23：CREATE 前端个人信息页面

- **IMPLEMENT**：`frontend/src/app/(main)/profile/page.tsx`
  - 展示和编辑个人信息（姓名、年级、重点学科）
  - 解题统计概览
  - 学情概览
- **VALIDATE**：浏览器测试个人信息编辑

### 任务 24：CREATE Docker 配置

- **IMPLEMENT**：`Dockerfile` — 后端 Docker 构建
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY pyproject.toml .
  RUN pip install uv && uv sync --no-dev
  COPY src/ src/
  COPY alembic.ini .
  EXPOSE 8000
  CMD ["uv", "run", "uvicorn", "aixue.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **IMPLEMENT**：`frontend/Dockerfile` — 前端 Docker 构建
- **IMPLEMENT**：`docker-compose.yml` — 本地开发环境（后端 + 前端 + PostgreSQL）
- **VALIDATE**：`docker compose up --build`

### 任务 25：CREATE Railway 部署配置

- **IMPLEMENT**：`railway.toml` 或 `nixpacks.toml` — Railway 构建配置
- **IMPLEMENT**：配置 Railway 环境变量（参考 `.env.example`）
- **IMPLEMENT**：配置 Railway PostgreSQL 服务
- **IMPLEMENT**：配置 Railway Volume 挂载（用于图片上传存储）
- **GOTCHA**：Railway 的 Python 构建默认使用 Nixpacks，需确认 uv 支持
- **VALIDATE**：`railway up` 部署并访问应用

### 任务 26：CREATE 测试套件

- **IMPLEMENT**：`tests/conftest.py` — pytest fixtures（async 数据库会话、测试客户端）
  ```python
  import pytest
  from httpx import AsyncClient, ASGITransport
  from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
  from aixue.main import app
  from aixue.db.base import Base

  @pytest.fixture
  async def db_session():
      engine = create_async_engine("sqlite+aiosqlite:///:memory:")
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)
      async_session = async_sessionmaker(engine)
      async with async_session() as session:
          yield session

  @pytest.fixture
  async def client():
      transport = ASGITransport(app=app)
      async with AsyncClient(transport=transport, base_url="http://test") as ac:
          yield ac
  ```
- **IMPLEMENT**：`tests/test_services/test_auth_service.py`
- **IMPLEMENT**：`tests/test_services/test_verifier.py`
  - 测试 parse_latex 各种格式
  - 测试 SymPy 求解正确性
  - 测试超时处理
  - 测试答案比对
- **IMPLEMENT**：`tests/test_services/test_solver_service.py`
- **IMPLEMENT**：`tests/test_services/test_diagnosis_service.py`
- **IMPLEMENT**：`tests/test_api/test_auth.py`
- **IMPLEMENT**：`tests/test_api/test_solver.py`
- **IMPLEMENT**：`tests/test_api/test_diagnosis.py`
- **VALIDATE**：`uv run pytest --cov=aixue --cov-report=term-missing -v`

---

## 测试策略

### 单元测试

使用 pytest + pytest-asyncio，每个服务模块对应一个测试文件。

**重点测试：**
- `verifier.py`：LaTeX 解析、SymPy 求解、答案比对、超时处理
- `auth_service.py`：密码加密验证、JWT 生成解码、过期处理
- `math_solver.py`：三级验证流程、重试逻辑
- `diagnosis_service.py`：五维分析、冷启动策略、数据量判断

### 集成测试

使用 httpx AsyncClient + SQLite 内存数据库，测试完整 API 流程。

**重点测试：**
- 注册 -> 登录 -> 获取 Token -> 解题 -> 查看历史
- 上传试卷 -> 诊断分析 -> 查看报告 -> 推荐练习
- 多用户数据隔离验证

### 边缘情况

- 图片模糊/无法识别
- SymPy parse_latex 失败（降级到 LLM 输出 SymPy 代码）
- LLM API 超时/错误
- 验证失败达到最大重试次数
- 空解题记录做学情诊断
- 极大/极小数值的 SymPy 计算
- 并发请求同一用户的会话

---

## 验证命令

### 级别 1：语法和样式

```bash
# Python 代码检查
uv run ruff check src/ tests/
# Python 类型检查
uv run mypy src/aixue/
# 前端代码检查
cd frontend && npm run lint
# 前端类型检查
cd frontend && npx tsc --noEmit
```

### 级别 2：单元测试

```bash
# 后端单元测试
uv run pytest tests/test_services/ -v --cov=aixue --cov-report=term-missing
# 前端测试（如有）
cd frontend && npm test
```

### 级别 3：集成测试

```bash
# 后端 API 集成测试
uv run pytest tests/test_api/ -v
# 完整测试套件
uv run pytest -v --cov=aixue
```

### 级别 4：手动验证

1. 启动后端：`uv run uvicorn aixue.main:app --reload`
2. 启动前端：`cd frontend && npm run dev`
3. 浏览器访问前端，执行以下流程：
   - 注册新用户（填写年级和学科）
   - 登录
   - 上传数学题图片，选择苏格拉底模式，验证引导式回复
   - 切换到完整解答模式，验证完整步骤输出
   - 进行多轮追问
   - 上传理化生题目，验证回复
   - 上传试卷，运行学情诊断
   - 查看诊断报告和推荐练习
   - 查看解题历史
   - 修改个人信息

---

## 验收标准

- [ ] 用户能注册账号并设置年级/学科
- [ ] 用户能登录并维持会话
- [ ] 用户能拍照/截图上传题目
- [ ] 数学题经 SymPy 验证，正确率 > 95%
- [ ] 苏格拉底模式有效引导（不直接给答案）
- [ ] 完整解答模式给出带步骤的完整解答
- [ ] 多轮追问上下文连贯
- [ ] 理化生学科能给出合理解答
- [ ] LaTeX 公式正确渲染
- [ ] 试卷上传后能识别题目和判定对错
- [ ] 学情报告包含五维分析
- [ ] 推荐练习题与薄弱点相关
- [ ] 多用户数据完全隔离
- [ ] 所有 API 端点有认证保护
- [ ] 单次解题响应 < 30 秒
- [ ] Railway 部署成功且可远程访问
- [ ] 测试覆盖率 > 80%
- [ ] 无 ruff / mypy 错误

---

## 完成检查清单

- [ ] 所有 26 个任务按顺序完成
- [ ] 每个任务的验证命令通过
- [ ] 所有验证命令成功执行
- [ ] 完整测试套件通过（单元 + 集成）
- [ ] 无代码检查或类型检查错误
- [ ] 手动测试确认全部功能
- [ ] 所有验收标准满足
- [ ] Railway 部署成功

---

## 备注

### 架构决策记录

1. **FastAPI + Next.js 替代 Streamlit**：调研报告（`rpiv/research-aixue-mvp.md`）分析了 Streamlit 在生产环境的局限性（UI 受限、认证困难、性能问题），推荐 FastAPI + Next.js 前后端分离架构。PRD 中的 Streamlit 方案已被调研结果覆盖更新

2. **PostgreSQL 替代 SQLite**：Railway 容器重启可能丢失 SQLite 数据（除非配合 Volume），Railway 原生支持 PostgreSQL 一键部署，更标准且自动备份

3. **MVP 阶段暂不集成 Lean 4**：三级验证中 L3（Lean 4 形式化证明）复杂度高且只适用于竞赛级题目，MVP 仅实现 L1（SymPy 前置求解）+ L2（assert 断言），Lean 4 作为可选扩展

4. **pyKT 延迟集成**：知识追踪需要充足数据（>= 20 道题），MVP 初期使用 LLM 做基础学情分析，数据积累后再切换到 pyKT 模型。代码结构预留 pyKT 集成接口

5. **前端 KaTeX 而非 MathJax**：K12 数学 LaTeX 子集 KaTeX 完全覆盖，渲染速度更快（毫秒级），包体积更小

### 信心分数：7/10

**降低信心的因素：**
- 前后端分离增加开发量，需要处理 CORS、认证流程、前端状态管理
- SymPy parse_latex 可能无法处理所有中国 K12 数学题格式（如中文数学符号）
- 苏格拉底引导 Prompt 质量需要反复调优
- pyKT 集成可能需要额外的数据预处理工作
- 前端 LaTeX 渲染需要处理各种分隔符格式

**提升信心的因素：**
- 所有核心技术（FastAPI、Anthropic SDK、SymPy、SQLAlchemy）都有成熟的文档和社区支持
- 框架内置能力覆盖了大部分需求，无需大量自研
- 3 人用户量消除了性能和并发的顾虑
- Railway 部署相对简单
