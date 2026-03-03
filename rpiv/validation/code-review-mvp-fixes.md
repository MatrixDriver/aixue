---
description: "代码审查报告: MVP 全栈实现及后续修复 (最近 5 次提交)"
status: completed
created_at: 2026-03-03T10:00:00
updated_at: 2026-03-03T10:30:00
archived_at: null
---

# 代码审查报告

**审查范围**: 最近 5 次提交 (be741d9..b6d3eeb)
- fix: OCR 聚焦指定题目 + 降低 max_tokens + 前端超时 300s
- fix: LLM 空 choices 自动重试 3 次（间隔 1/3/5 秒）
- fix: 处理 OpenRouter 返回空 choices 导致的 500 错误
- fix: 修复 Railway 部署 $PORT 变量展开和 Dockerfile uv.lock 缺失
- feat: 切换 LLM 到 Gemini + 修复部署配置

**统计：**

- 修改的文件：12
- 添加的文件：3 (frontend/railway.toml, frontend/next.config.ts 新增内容, uv.lock)
- 删除的文件：0
- 新增行：607
- 删除行：90

---

## 发现的问题

### 问题 1: 数学验证逻辑反转

```
severity: high
status: fixed
file: src/aixue/services/math_solver.py
line: 97
issue: verified 在 SymPy 无法求解时被设为 True，逻辑反转
detail: |
  当 SymPy 前置求解失败（返回 None）或处于苏格拉底模式时，
  `verified = sympy_result is None` 将 verified 设为 True（当 sympy_result 为 None 时）。
  这意味着"无法验证"反而被标记为"已验证"，与语义相悖。
  当 sympy_result 有值但 mode 为 socratic 时，verified 为 False，也不合理。
suggestion: |
  应改为 `verified = False`（无法验证时默认未验证），
  或引入第三种状态如 "unverifiable" 来区分"验证失败"和"跳过验证"。
```

### 问题 2: CORS 配置 allow_origins=* 与 allow_credentials=True 冲突

```
severity: high
status: fixed
file: src/aixue/main.py
line: 46-51
issue: CORS 通配符 + credentials=True 是无效组合
detail: |
  浏览器规范明确禁止 Access-Control-Allow-Origin: * 与
  Access-Control-Allow-Credentials: true 同时使用。
  浏览器会拒绝响应，导致跨域请求失败。
  当前之所以能工作，是因为前端通过 Next.js rewrites 代理请求绕过了 CORS，
  但如果将来直接调用后端 API 会出问题。
suggestion: |
  MVP 阶段如果只通过 Next.js 代理访问，可以去掉 allow_credentials=True；
  或者将 allow_origins 设为具体的前端域名列表。
```

### 问题 3: 全局异常处理器泄露内部错误信息

```
severity: high
status: fixed
file: src/aixue/main.py
line: 57-61
issue: 全局异常处理器将原始异常消息暴露给客户端
detail: |
  `detail = str(exc) if str(exc) else "服务器内部错误，请稍后重试"`
  会将内部错误细节（如数据库连接字符串、文件路径、堆栈信息片段）
  直接返回给前端，存在信息泄露风险。
suggestion: |
  生产环境应只返回通用错误消息 "服务器内部错误，请稍后重试"，
  内部细节仅记录到日志中（logger.exception 已在做这件事）。
```

### 问题 4: 前端代理超时与 axios 超时不一致

```
severity: medium
status: fixed
file: frontend/next.config.ts
line: 17
issue: proxyTimeout (180s) < axios timeout (300s)，会导致代理先断开
detail: |
  Next.js proxyTimeout 设为 180 秒，但 frontend/src/lib/api.ts 的
  axios timeout 设为 300 秒。当请求耗时在 180-300 秒之间时，
  代理层会先超时断开连接，而 axios 还在等待，
  前端会收到一个模糊的网络错误而非超时提示。
suggestion: |
  两者保持一致，建议都设为 300 秒（或都设为 180 秒），
  proxyTimeout 应 >= axios timeout。
```

### 问题 5: verifier.py 使用已弃用的 asyncio.get_event_loop()

```
severity: medium
status: fixed
file: src/aixue/services/verifier.py
line: 34-35, 61-62, 85-87
issue: get_event_loop().run_in_executor() 在 Python 3.12+ 已弃用
detail: |
  Python 3.10 起 asyncio.get_event_loop() 在没有运行中的事件循环时
  会发出 DeprecationWarning，Python 3.12 中行为更严格。
  正确做法是使用 asyncio.get_running_loop() 或 asyncio.to_thread()。
suggestion: |
  将所有 `asyncio.get_event_loop().run_in_executor(None, func, ...)`
  替换为 `asyncio.to_thread(func, ...)`，更简洁且无弃用警告。
```

### 问题 6: verifier._sympy_solve 的 fallback 逻辑无效

```
severity: medium
status: fixed
file: src/aixue/services/verifier.py
line: 102-126
issue: 异常回退分支重复执行相同的 parse_latex()，必然再次失败
detail: |
  第一个 try 块中 `parse_latex(latex_expr)` 抛出异常后，
  fallback 分支（line 117）再次调用 `parse_latex(latex_expr)`
  解析完全相同的输入，必然产生相同的异常，导致 fallback 永远不会成功。
  `symbols("x")` 创建了变量但对 parse_latex 的解析能力没有任何影响。
suggestion: |
  如果目标是用符号变量求解，应在 fallback 中使用不同的解析策略
  （如 sympify 或手动构造表达式），而非重复调用 parse_latex。
  或者直接移除无效的 fallback 分支。
```

### 问题 7: config.py 字段命名误导

```
severity: medium
status: fixed
file: src/aixue/config.py
line: 13
issue: anthropic_api_key 实际存储的是 OpenRouter API Key
detail: |
  代码已切换到 OpenRouter/Gemini，但配置字段仍叫 `anthropic_api_key`，
  对应的环境变量为 ANTHROPIC_API_KEY。新接手的开发者会误以为这是
  Anthropic 的密钥。pyproject.toml 中也仍保留着 anthropic 依赖。
suggestion: |
  将字段重命名为 `openrouter_api_key`（环境变量 OPENROUTER_API_KEY），
  并清理 pyproject.toml 中未使用的 anthropic 依赖。
```

### 问题 8: pyproject.toml dev 依赖重复定义

```
severity: low
status: fixed
file: pyproject.toml
line: 26-35, 57-66
issue: dev 依赖在 [project.optional-dependencies] 和 [dependency-groups] 中重复定义
detail: |
  完全相同的依赖列表出现了两次：
  - [project.optional-dependencies].dev (line 26-35)
  - [dependency-groups].dev (line 57-66)
  这会导致维护时容易遗漏其中一处的更新。
suggestion: |
  uv 默认使用 [dependency-groups]，可以移除 [project.optional-dependencies].dev，
  只保留一处定义。
```

### 问题 9: solver_service.py 函数内部 import

```
severity: low
status: fixed
file: src/aixue/services/solver_service.py
line: 111-112, 129, 206
issue: 多处在函数体内部 import 模块，不符合 PEP 8 规范
detail: |
  follow_up() 和 _save_session() 方法中有多个运行时 import：
  - `from sqlalchemy import select`（line 111, 206）
  - `from sqlalchemy.orm import selectinload`（line 112）
  - `from aixue.prompts.system import build_system_prompt`（line 129）
  这些模块在文件顶部已有同类 import（selectinload 在 solver.py 中用到），
  且不存在循环依赖问题。
suggestion: |
  将这些 import 移到文件顶部，与其他 import 统一管理。
```

### 问题 10: dependencies.py 异常链断裂

```
severity: low
status: fixed
file: src/aixue/dependencies.py
line: 29-36
issue: HTTPException 在 except 块中抛出但缺少 from e
detail: |
  `raise HTTPException(...)` 在 `except jwt.ExpiredSignatureError:` 和
  `except jwt.InvalidTokenError:` 块中抛出，没有使用 `from e`。
  这会导致原始异常的 traceback 被抑制，不利于调试。
suggestion: |
  改为 `raise HTTPException(...) from e`，保留异常链。
  （注意：solver.py 中的类似模式已正确使用了 `from e`。）
```

---

## 总结

| 严重程度 | 数量 | 已修复 |
|----------|------|--------|
| critical | 0    | 0      |
| high     | 3    | 3      |
| medium   | 4    | 4      |
| low      | 3    | 3      |

**全部 10 个问题已修复**，72 项测试全部通过，ruff 检查无告警。
