---
description: "代码审查报告: multi-question-detection"
status: archived
created_at: 2026-03-07T23:00:00
updated_at: 2026-03-07T23:00:00
archived_at: null
---

# 代码审查报告

## 概述

审查多题图片智能识别与选题功能的全部代码变更。

**统计：**

- 修改的文件：11
- 添加的文件：4（question-selector.tsx, test_ocr_detect.py, test_detect.py, test_multi_question_flow.py）
- 删除的文件：0
- 新增行：469
- 删除行：36

## 测试结果

- 116 个测试全部通过
- ruff check 零错误
- pytest warnings：3 个 deprecation warning（`HTTP_413_REQUEST_ENTITY_TOO_LARGE` -> `HTTP_413_CONTENT_TOO_LARGE`），非阻塞

## 发现的问题

### 问题 1

```
severity: medium
status: archived
file: src/aixue/services/ocr_service.py
line: 146
issue: import 放在方法内部而非文件顶部
detail: _parse_detection_result() 方法内部 import json 和 re。这两个是标准库模块，应该放在文件顶部。每次调用都会执行 import 语句（虽然 Python 会缓存，但不符合 PEP 8 惯例且增加认知负担）
suggestion: 将 `import json` 和 `import re` 移到文件顶部的 import 区域
```

### 问题 2

```
severity: medium
status: archived
file: src/aixue/services/ocr_service.py
line: 139
issue: 贪婪正则匹配可能提取错误的 JSON
detail: `re.search(r'\{[\s\S]*\}', raw)` 使用贪婪匹配，当 LLM 返回包含多个 JSON 对象或花括号的文本时，会匹配从第一个 `{` 到最后一个 `}` 的所有内容，可能包含非 JSON 文本导致解析失败后走 fallback。例如："结果如下 {a:1} 补充说明 {b:2}" 会匹配 "{a:1} 补充说明 {b:2}"
suggestion: 考虑使用非贪婪匹配或尝试匹配 markdown code block 中的 JSON（```json ... ```），实际场景中 fallback 到单题是安全的，因此此问题影响有限
```

### 问题 3

```
severity: medium
status: archived
file: src/aixue/api/endpoints/solver.py
line: 58-59
issue: 每次请求都创建新的 LLMService 和 OCRService 实例
detail: detect_questions 端点每次请求都 `llm = LLMService(); ocr = OCRService(llm)` 创建新实例。虽然现有 solve_problem 端点的 SolverService() 也有同样模式（第 132 行），但 detect_questions 新增了额外的实例化。这不是 bug，但如果 LLMService 构造函数开销增大（如连接池初始化），会影响性能
suggestion: 保持与现有 SolverService() 模式一致即可，后续可统一优化为依赖注入。当前不阻塞
```

### 问题 4

```
severity: low
status: archived
file: src/aixue/api/endpoints/solver.py
line: 53
issue: 使用已弃用的 HTTP 状态码常量
detail: `status.HTTP_413_REQUEST_ENTITY_TOO_LARGE` 已被弃用（pytest 也给出 DeprecationWarning），应使用 `status.HTTP_413_CONTENT_TOO_LARGE`。注意：现有 solve_problem 端点（第 76 行）也使用了旧常量，此问题非新引入但应一并修复
suggestion: 将 `HTTP_413_REQUEST_ENTITY_TOO_LARGE` 替换为 `HTTP_413_CONTENT_TOO_LARGE`（两处：detect_questions 第 53 行和 solve_problem 第 76 行）
```

### 问题 5

```
severity: medium
status: archived
file: frontend/src/hooks/use-chat.ts
line: 80
issue: 单题快速通道判断条件可能遗漏边界情况
detail: `completeQuestions.length === 1 && detectResult.question_count <= 1` 当 question_count=3 但只有 1 道完整题时，不会走快速通道而是显示选题按钮组（包含 1 个可选 + 2 个灰显不完整）。这个行为是合理的——用户能看到其他题不完整的原因。但如果 question_count=0 且 completeQuestions.length===0，会走 else 分支显示一个空的选题消息。实际中 question_count=0 时 completeQuestions 为空数组，此时应该显示"未检测到题目"的提示而非空按钮组
detail: 后端 /detect 端点已经在 question_count==0 时返回了正确的提示消息（第 76 行），前端会显示这个消息文本。所以实际效果是用户看到"未检测到完整题目"提示+一个没有按钮的空选题区域。功能上可用但 UX 略有瑕疵
suggestion: 在前端判断 completeQuestions.length === 0 时，不设置 type: "question_selection"，改为普通文本消息显示提示信息
```

### 问题 6

```
severity: low
status: archived
file: frontend/src/hooks/use-chat.ts
line: 97-111
issue: 多题检测返回后 setState 中 messages 未包含最新的 userMsg
detail: 第 102 行 `messages: [...prev.messages, {...}]` 使用 prev.messages，但 userMsg 已经在第 50-53 行通过 setState 添加了。由于 React 的 setState 批处理和闭包，prev.messages 在这里应该包含 userMsg。但如果两个 setState 在同一个事件循环中合并，可能出现 prev.messages 不包含 userMsg 的情况。实际上 await detectQuestions() 是异步操作，setState 回调中的 prev 会获取最新状态，所以此问题不太可能触发。标注为 low
suggestion: 可保持现状，React 18 的自动批处理在异步操作后的 setState 中 prev 能正确获取最新状态
```

### 问题 7

```
severity: low
status: archived
file: frontend/src/hooks/use-chat.ts
line: 219-236
issue: selectAll 中串行请求无进度反馈
detail: 全部解答时对每道题串行调用 solveQuestion，5 道题可能耗时 30 秒以上。前端仅显示通用的"正在思考..."加载动画，用户无法知道当前在解第几题。PRD 场景 3 提到"每题解答有清晰分隔标记"，但当前实现是等所有题解答完才一次性显示结果
suggestion: 考虑每题解答完成后立即追加到 messages 中（在循环内调用 setState），让用户实时看到逐题结果。当前实现功能正确，UX 改进可后续迭代
```

### 问题 8

```
severity: low
status: archived
file: frontend/src/components/chat/question-selector.tsx
line: 41-71
issue: questions 数组中 index 字段可能不唯一导致 React key 冲突
detail: `key={q.index}` 使用题目的 index 作为 React key。如果 LLM 返回的 JSON 中多道题有相同 index（如都是 1），会导致 React key 重复警告和渲染异常。后端 _parse_detection_result 的 fallback 返回 index=1 的单题，正常情况下不会重复
suggestion: 使用数组索引作为 key 的备选方案：`key={`q-${idx}`}`，或在后端解析时确保 index 唯一
```

## 审查总结

| 严重程度 | 数量 |
|----------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 4 |
| LOW | 4 |

**总体评价**：代码质量良好，架构决策合理（独立 /detect 端点、前端驱动逐题解答、复用现有 user_hint 机制）。没有发现安全漏洞或逻辑错误。4 个 medium 问题主要是代码规范和边界处理，不影响功能正确性。所有 116 个测试通过，测试覆盖了核心场景。

**推荐**：可直接合并。medium 问题建议在下一次迭代中修复。
