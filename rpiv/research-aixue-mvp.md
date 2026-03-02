---
type: research
title: "AIXue MVP 关键技术可行性调研"
status: completed
created_at: 2026-03-02T18:00:00
updated_at: 2026-03-02T18:30:00
archived_at: null
---

# AIXue MVP 关键技术可行性调研

## 1. Web 应用框架选型

### 1.1 方案对比

| 方案 | 前端灵活度 | LaTeX 渲染 | 多轮对话 | 用户认证 | 拍照上传 | 生产就绪度 |
|------|-----------|-----------|---------|---------|---------|-----------|
| **FastAPI + Next.js/React** | 极高 | 原生支持 KaTeX/MathJax | 完全自定义 | JWT / fastapi-users | 完全支持 | 高 |
| Streamlit | 低 | 内置 st.latex() | 受限 | 需第三方 | 基础支持 | 低（原型级） |
| Gradio | 中 | 内置 LaTeX | 内置 ChatInterface | 需第三方 | 支持 | 中 |
| Django + React | 极高 | 原生支持 | 完全自定义 | 内置 auth | 完全支持 | 高 |

### 1.2 推荐方案：FastAPI（后端）+ Next.js（前端）

**理由：**

1. **FastAPI 优势**：
   - 原生 async/await 支持，适合 LLM API 调用和 SymPy 计算等 I/O 密集型任务
   - 自动生成 OpenAPI 文档，前后端协作高效
   - 类型提示 + Pydantic 数据验证，与 Python AI 生态无缝集成
   - 性能优于 Django（3000+ req/s）
   - 官方提供 [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)（FastAPI + React + SQLModel + PostgreSQL）

2. **Next.js 前端优势**：
   - SSR/SSG 混合渲染，首屏加载快
   - React 生态丰富，KaTeX/MathJax 组件成熟
   - 移动端响应式布局原生支持
   - TypeScript 支持，类型安全

3. **淘汰 Streamlit/Gradio 的原因**：
   - Streamlit 的 UI 组件有限，不适合构建复杂的学情诊断报告页面
   - Streamlit 不支持复杂的用户认证和多用户数据隔离
   - Gradio 虽有 ChatInterface，但自定义程度不足以满足苏格拉底式引导的交互设计
   - 两者都不适合生产环境长期维护

4. **不选 Django 的原因**：
   - 对于 3 人初始用户的 MVP，Django 的 ORM 和 admin 等重量级特性属于过度设计
   - FastAPI 的 async 原生支持更适合 LLM API 调用场景

### 1.3 前端 LaTeX 渲染方案

**推荐：KaTeX**

| 维度 | KaTeX | MathJax 3 |
|------|-------|-----------|
| 渲染速度 | 极快（毫秒级） | 较快（MathJax 3 已大幅改进） |
| 包体积 | ~280KB | ~500KB+ |
| React 集成 | react-katex / rehype-katex | better-react-mathjax |
| LaTeX 覆盖率 | 覆盖 K12 所需的绝大部分命令 | 最完整 |
| 服务端渲染 | 支持 SSR | 支持 SSR |

**KaTeX 足以覆盖初高中数学的 LaTeX 需求**（基础代数、方程、分数、根号、矩阵、几何符号等）。如遇到少数不支持的高级命令，可以后期补充 MathJax 作为降级方案。

## 2. 多模态 LLM API 集成

### 2.1 模型选型

| 模型 | 输入价格 ($/1M tokens) | 输出价格 ($/1M tokens) | 图片 token 计算 | 上下文窗口 | K12 数学能力 |
|------|----------------------|----------------------|----------------|-----------|-------------|
| **Claude Sonnet 4.6** | $3.00 | $15.00 | ~(width*height)/750 | 200K | 极强 |
| GPT-4o | $2.50 | $10.00 | 按分辨率计算 | 128K | 极强 |
| GPT-4o-mini | $0.15 | $0.60 | 按分辨率计算 | 128K | 强 |

**推荐主模型：Claude Sonnet 4.6**
- K12 数学推理能力极强（AIME 2025 带工具 100%）
- 200K 上下文窗口，足以支撑多轮对话 + 学情数据注入
- Vision API 成熟，支持 base64 / URL / Files API 三种图片输入方式

**备选/降级：GPT-4o-mini**
- 成本仅为 Claude Sonnet 的 1/20，适合非数学学科（理化生）的简单解题
- K12 常规题目能力足够

### 2.2 图片输入技术细节

**Claude Vision API 规格：**
- 支持格式：JPEG、PNG、GIF、WebP
- 单图大小限制：API 5MB，claude.ai 10MB
- 单次请求最多 100 张图片（API）
- 最大分辨率：8000x8000 px（>20 张图时 2000x2000 px）
- 最佳分辨率：长边不超过 1568 px（超过会自动缩放，增加延迟）
- Token 计算公式：`tokens = (width * height) / 750`
- 示例成本：1000x1000 px 图片约 1334 tokens，约 $0.004/张

**集成方式（Python SDK）：**
```python
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-6-20250514",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image_data,
                },
            },
            {"type": "text", "text": "请识别这道数学题并给出解题步骤"},
        ],
    }],
)
```

### 2.3 多轮对话上下文管理

**Claude Messages API 是无状态的**，每次请求需传入完整对话历史。

**推荐管理方案：**
1. **服务端维护对话历史**：在 PostgreSQL 中存储每个会话的 messages 列表
2. **Token 预算管理**：每次请求前统计已有对话的 token 总量，接近上限时进行摘要压缩
3. **上下文注入**：将用户 profile（年级、学科偏好）和 SymPy 验证结果注入 system prompt
4. **对话结构**：严格交替 user/assistant 消息，图片置于文本之前以获得最佳效果

## 3. SymPy 验证集成

### 3.1 SymPy 在 Web 服务中的使用

**SymPy 是纯 Python 库**，可直接在 FastAPI 应用中使用。但 SymPy 的符号计算是 CPU 密集型操作，需注意以下要点：

1. **同步 vs 异步**：SymPy 本身是同步的，在 async FastAPI 中需使用 `run_in_executor` 避免阻塞事件循环
   ```python
   import asyncio
   from sympy import solve, symbols

   async def verify_solution(expression: str, expected: str):
       loop = asyncio.get_event_loop()
       result = await loop.run_in_executor(
           None, lambda: _sympy_verify(expression, expected)
       )
       return result
   ```

2. **超时保护**：某些复杂表达式的求解可能耗时很长，需设置超时
   ```python
   import signal
   # 或使用 asyncio.wait_for(coro, timeout=5.0)
   ```

### 3.2 LaTeX 到 SymPy 表达式的转换

**SymPy 内置 `parse_latex` 功能：**
```python
from sympy.parsing.latex import parse_latex

expr = parse_latex(r"\frac{1 + \sqrt{x}}{2}")
# 输出: (1 + sqrt(x))/2
```

- 支持两种后端：ANTLR（默认）和 Lark
- 覆盖常见 LaTeX 数学表达式（分数、根号、指数、三角函数、矩阵等）
- **补充方案**：对于 `parse_latex` 无法处理的复杂表达式，让 LLM 直接输出 SymPy 代码

**第三方增强库：**
- [latex2sympy2](https://pypi.org/project/latex2sympy2/)：扩展了 SymPy 原生 LaTeX 解析的覆盖范围
- [Latex-Sympy-Calculator](https://github.com/OrangeX4/Latex-Sympy-Calculator)：VSCode 插件，可参考其解析逻辑

### 3.3 验证管线设计

```
LLM 解题输出 (LaTeX)
    ↓
parse_latex() 转 SymPy 表达式
    ↓
SymPy.solve() / .simplify() / .equals() 求解验证
    ↓
比对结果：通过 → 返回 | 失败 → 重试（最多3次）
```

**延迟预估：**
- LaTeX 解析：< 10ms
- 简单代数求解（一元方程、不等式）：< 50ms
- 中等复杂度（方程组、多项式）：50-500ms
- 复杂符号计算（积分、微分方程）：500ms-5s
- **总验证管线延迟**：通常 < 1s，个别复杂题 < 5s

### 3.4 推荐的三级验证方案

| 级别 | 方法 | 覆盖场景 | 延迟 |
|------|------|---------|------|
| L1 | SymPy 前置求解 | 有明确数值答案的代数/计算题 | <500ms |
| L2 | assert 断言 | 关键步骤校验（如垂直关系验证 dot=0） | <100ms |
| L3 | Lean 4（可选） | 竞赛级/高难度证明题 | 分钟级 |

**MVP 阶段仅需实现 L1 + L2**，L3 作为后续扩展。

## 4. Railway 部署约束

### 4.1 资源规格

| 资源 | Hobby ($5/月) | Pro ($20/月) |
|------|--------------|-------------|
| vCPU | 最高 48 | 最高 1,000 |
| 内存 | 最高 48 GB | 最高 1 TB |
| 临时存储 | 100 GB | 100 GB |
| 卷存储 | 5 GB | 1 TB（可扩展至 250 GB 自助） |
| 副本数 | 6 | 42 |
| 镜像大小 | 100 GB | 无限制 |

**超额计费：**
- RAM：$10/GB/月
- CPU：$20/vCPU/月
- 网络出口：$0.05/GB
- 卷存储：$0.15/GB/月

**对 AIXue MVP 的评估：** Hobby Plan 完全足够。3 个用户的使用量极低，FastAPI 应用 + PostgreSQL 预计月消耗 < $5。

### 4.2 持久化存储方案

Railway 提供 Volume（持久化卷）功能：
- 挂载路径自定义（如 `/app/uploads`）
- 数据跨部署持久化
- Hobby Plan 限制 5 GB，足够存储学生上传的题目图片

**图片存储推荐方案（按复杂度递增）：**

| 方案 | 复杂度 | 成本 | 推荐度 |
|------|-------|------|-------|
| **Railway Volume** | 低 | 包含在 Plan 中 | MVP 首选 |
| Cloudflare R2 | 中 | 免费 10 GB/月 | 扩展期推荐 |
| PostgreSQL BYTEA | 低 | 占用 DB 空间 | 不推荐 |

**MVP 推荐**：直接使用 Railway Volume 存储图片。3 个用户，每天数道题，图片压缩后每张 < 500KB，5 GB 可存储数万张图片。

### 4.3 数据库方案

**Railway 原生支持 PostgreSQL**，一键部署，自动备份，按使用量计费。

推荐直接使用 Railway PostgreSQL 服务，理由：
- 与应用同平台，内网通信延迟极低
- 自动备份，无需额外运维
- Hobby Plan 够用（3 用户数据量极小）
- 不推荐 SQLite（Railway 容器重启可能丢失数据，除非配合 Volume，但 PG 更标准）

## 5. 数据库方案详细设计

### 5.1 存储需求分析

| 数据类型 | 预估规模 | 增长速率 |
|---------|---------|---------|
| 用户 profile | ~3 条记录 | 极慢 |
| 解题会话 | 每天 5-10 条 | 每月 ~200 条 |
| 对话消息 | 每会话 5-20 条 | 每月 ~2000 条 |
| 学情诊断 | 每月 1-2 次 | 极慢 |
| 题库 | 初始 30K+（CMM-Math + TAL-SCQ5K） | 缓慢增长 |

### 5.2 ORM 选型

| ORM | 异步支持 | 学习曲线 | 生态 | FastAPI 集成 |
|-----|---------|---------|------|-------------|
| **SQLAlchemy 2.0** | 原生 async | 中 | 最成熟 | 官方推荐 |
| SQLModel | 原生 async | 低 | 新兴 | FastAPI 官方模板使用 |
| Tortoise ORM | 原生 async | 低 | 较小 | 良好 |
| Prisma (Python) | 异步客户端 | 低 | Node 生态为主 | 非主流 |

**推荐：SQLAlchemy 2.0 + asyncpg**

理由：
1. SQLAlchemy 2.0 提供原生 async 支持，使用 `create_async_engine` + `async_sessionmaker`
2. asyncpg 是性能最优的 PostgreSQL async 驱动
3. 生态最成熟，问题排查资源丰富
4. Alembic 迁移工具支持 async 模式
5. 实测 async 模式下处理能力为同步模式的 3-5 倍

**备选：SQLModel**
- FastAPI 创作者开发，与 FastAPI 深度集成
- 本质是 SQLAlchemy + Pydantic 的封装，降低学习曲线
- FastAPI 官方全栈模板已采用 SQLModel
- 缺点：社区和文档相比 SQLAlchemy 较薄弱

### 5.3 核心数据模型草案

```
User (用户)
├── id, name, grade, subjects, created_at
├── sessions: [SolvingSession]
└── diagnostics: [DiagnosticReport]

SolvingSession (解题会话)
├── id, user_id, subject, topic, mode (socratic/direct)
├── image_path, question_text, verified_answer
├── messages: [Message]
└── created_at, updated_at

Message (对话消息)
├── id, session_id, role (user/assistant/system)
├── content (text + image refs)
└── token_count, created_at

DiagnosticReport (学情诊断报告)
├── id, user_id, exam_image_path
├── knowledge_gaps, thinking_patterns
├── recommended_exercises: [Exercise]
└── created_at

Exercise (题库)
├── id, subject, topic, difficulty, grade_range
├── question_latex, answer_latex, solution_steps
├── source (CMM-Math / TAL / generated)
└── sympy_verification_code
```

## 6. 框架内置方案优先原则检查

### 6.1 FastAPI 内置能力

| 需求 | 框架内置方案 | 是否需要自研 |
|------|------------|------------|
| 请求验证 | Pydantic v2 自动验证 | 否 |
| API 文档 | 自动 OpenAPI/Swagger | 否 |
| 依赖注入 | `Depends()` | 否 |
| 后台任务 | `BackgroundTasks` | 否 |
| 文件上传 | `UploadFile` | 否 |
| CORS | `CORSMiddleware` | 否 |
| WebSocket | 内置支持 | 否（可用于实时对话流） |
| 认证 | OAuth2PasswordBearer 内置 | 需 JWT 库配合 |

### 6.2 Anthropic SDK 内置能力

| 需求 | SDK 内置方案 | 是否需要自研 |
|------|------------|------------|
| 图片输入 | base64 / URL / Files API | 否 |
| 流式输出 | `client.messages.stream()` | 否 |
| Token 计数 | `response.usage` | 否 |
| 重试 | SDK 内置自动重试 | 否 |
| 多模型切换 | 修改 model 参数即可 | 否 |

### 6.3 SymPy 内置能力

| 需求 | 内置方案 | 是否需要自研 |
|------|---------|------------|
| LaTeX 解析 | `parse_latex()` | 否 |
| 方程求解 | `solve()` / `solveset()` | 否 |
| 表达式比较 | `equals()` / `simplify()` | 否 |
| LaTeX 输出 | `latex()` | 否 |
| 数值验证 | `N()` / `evalf()` | 否 |

### 6.4 SQLAlchemy 2.0 内置能力

| 需求 | 内置方案 | 是否需要自研 |
|------|---------|------------|
| 异步引擎 | `create_async_engine` | 否 |
| 会话管理 | `async_sessionmaker` | 否 |
| 迁移 | Alembic | 否 |
| 关系映射 | `relationship()` | 否 |
| JSON 字段 | `JSON` 类型 | 否 |

**结论：AIXue MVP 的核心技术依赖均有成熟的内置方案，无需大量自研代码。**

## 7. 综合推荐方案

### 技术栈总览

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| **前端框架** | Next.js 14+ (React) | SSR + 丰富生态 + 移动端响应式 |
| **LaTeX 渲染** | KaTeX | K12 覆盖足够，性能最优 |
| **后端框架** | FastAPI | async 原生 + Python AI 生态 |
| **LLM 主模型** | Claude Sonnet 4.6 | K12 数学推理能力最强 |
| **LLM 降级** | GPT-4o-mini | 理化生低成本选项 |
| **符号验证** | SymPy | 成熟稳定，内置 LaTeX 解析 |
| **数据库** | PostgreSQL (Railway) | 一键部署 + 自动备份 |
| **ORM** | SQLAlchemy 2.0 + asyncpg | 异步原生 + 生态最强 |
| **认证** | JWT (PyJWT + bcrypt) | FastAPI 内置 OAuth2 支持 |
| **图片存储** | Railway Volume（MVP）→ Cloudflare R2（扩展） | 渐进式扩展 |
| **部署** | Railway | 简单 + 按需计费 |

### 成本预估（月度）

| 项目 | 费用预估 |
|------|---------|
| Railway Hobby Plan | $5/月（含 $5 额度） |
| Railway PostgreSQL | < $1/月（3 用户极低负载） |
| Claude Sonnet API | ~$5-10/月（每天 10 道题 * 30 天） |
| GPT-4o-mini API | ~$0.5/月（理化生辅助） |
| **总计** | **~$12-17/月** |

### 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| SymPy parse_latex 覆盖不全 | 部分 LaTeX 无法自动验证 | LLM 输出 SymPy 代码作为补充路径 |
| LLM API 延迟波动 | 用户体验 | 流式输出 + 前端 loading 动画 |
| 前后端分离增加开发量 | 开发周期 | 使用 FastAPI 官方全栈模板加速 |
| Railway 单区域部署延迟 | 国内访问慢 | Cloudflare CDN 加速前端 |
