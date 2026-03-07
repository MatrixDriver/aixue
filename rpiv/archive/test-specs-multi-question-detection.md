---
description: "测试规格: 多题图片智能识别与选题"
status: archived
created_at: 2026-03-07T22:30:00
updated_at: 2026-03-07T22:30:00
archived_at: null
---

# 测试规格: 多题图片智能识别与选题

基于 PRD `rpiv/requirements/prd-multi-question-detection.md` 和测试策略 `rpiv/validation/test-strategy-multi-question-detection.md`。

## 1. 测试用例总览

| ID | 类型 | 场景 | 优先级 |
|----|------|------|--------|
| UT-01 | 单元 | 多题检测结果解析 - 正常 JSON | P0 |
| UT-02 | 单元 | 多题检测结果解析 - 异常格式降级 | P0 |
| UT-03 | 单元 | 单题快速通道 | P0 |
| UT-04 | 单元 | 多题返回按钮组数据结构 | P0 |
| UT-05 | 单元 | 不完整题目标记 | P0 |
| UT-06 | 单元 | 全部不完整场景 | P0 |
| UT-07 | 单元 | 超过 5 题限制 | P1 |
| UT-08 | 单元 | user_hint 跳过多题检测 | P0 |
| UT-09 | 单元 | 逐题解答 - 正常完成 | P1 |
| UT-10 | 单元 | 逐题解答 - 部分失败跳过 | P1 |
| IT-01 | 集成 | 单题完整流程（OCR → 检测 → 解题） | P0 |
| IT-02 | 集成 | 多题选择流程（检测 → 按钮 → 选题 → 解题） | P0 |
| IT-03 | 集成 | 全部解答流程 | P1 |
| IT-04 | 集成 | 数据库持久化验证 | P1 |
| AT-01 | API | POST /solve - 多题检测响应 | P0 |
| AT-02 | API | POST /solve/select - 选题解答 | P0 |
| AT-03 | API | POST /solve/select - 全部解答 | P1 |
| AT-04 | API | POST /solve - user_hint 快捷路径 | P0 |
| AT-05 | API | POST /solve/select - 无效选择 | P1 |
| AT-06 | API | 回归 - 纯文本输入不受影响 | P0 |

---

## 2. 单元测试用例

### UT-01: 多题检测结果解析 - 正常 JSON

**测试目标**: `OCRService.detect_questions()` 正确解析 LLM 返回的结构化 JSON。

**前置条件**: mock `LLMService.recognize_image()` 返回标准 JSON。

**测试步骤**:
1. 构造 mock LLM 返回值：
   ```json
   {
     "questions": [
       {"number": "1", "summary": "已知函数 f(x) = x^2 + 2x...", "complete": true},
       {"number": "2", "summary": "如图所示，在三角形ABC中...", "complete": true}
     ]
   }
   ```
2. 调用 `detect_questions(image_data, media_type)`
3. 验证返回结果

**预期结果**:
- 返回包含 2 个题目的列表
- 每个题目有 `number`、`summary`、`complete` 字段
- 题目顺序与 LLM 返回一致

---

### UT-02: 多题检测结果解析 - 异常格式降级

**测试目标**: LLM 返回非标准格式时，服务降级为单题流程。

**前置条件**: mock LLM 返回非 JSON 文本。

**测试步骤**:
1. mock LLM 返回纯文本（如 `"这张图片中有两道题"`）
2. 调用 `detect_questions()`
3. 验证降级行为

**预期结果**:
- 不抛出异常
- 返回降级标记（如 `None` 或空列表），触发 fallback 到现有单题流程

---

### UT-03: 单题快速通道

**测试目标**: 检测到仅 1 道完整题时，自动进入解题无需选题。

**前置条件**: mock 多题检测返回单题结果。

**测试步骤**:
1. mock `detect_questions()` 返回 1 道完整题
2. 调用 `SolverService.solve(image=..., text=None)`
3. 验证直接进入解题流程

**预期结果**:
- 返回结果类型为解题结果（非 `question_select`）
- 不包含按钮组数据
- 与现有单题流程行为一致

---

### UT-04: 多题返回按钮组数据结构

**测试目标**: 检测到 2-5 道完整题时，返回正确的按钮组数据。

**前置条件**: mock 多题检测返回 3 道题（2 完整 + 1 不完整）。

**测试步骤**:
1. mock `detect_questions()` 返回 3 道题目
2. 调用 `SolverService.solve()`
3. 验证返回数据结构

**预期结果**:
- 返回类型为 `question_select`
- `questions` 列表包含 3 道题目
- 每道题有 `number`、`summary`、`complete` 字段
- `message` 字段包含 "检测到 3 道题目" 或类似文案
- 包含 `session_id`

---

### UT-05: 不完整题目标记

**测试目标**: 不完整题目被正确标记，不影响完整题目。

**前置条件**: mock 返回混合完整性的题目列表。

**测试步骤**:
1. mock 返回 4 道题目：第 1、3 完整，第 2、4 不完整
2. 调用检测方法
3. 验证每道题的 `complete` 字段

**预期结果**:
- 题目 1、3 的 `complete` 为 `true`
- 题目 2、4 的 `complete` 为 `false`
- 完整题目数量统计正确

---

### UT-06: 全部不完整场景

**测试目标**: 所有题目不完整时返回提示信息。

**前置条件**: mock 返回全部不完整的题目。

**测试步骤**:
1. mock `detect_questions()` 返回 2 道不完整题
2. 调用 `SolverService.solve()`
3. 验证返回结果

**预期结果**:
- 不返回按钮组
- 返回错误/提示信息，包含"未检测到完整题目"或"重新拍照"等关键词
- 不触发解题流程

---

### UT-07: 超过 5 题限制

**测试目标**: 超过 5 道题时只返回前 5 道并附带提示。

**前置条件**: mock 返回 8 道题目。

**测试步骤**:
1. mock `detect_questions()` 返回 8 道完整题
2. 调用相关方法
3. 验证截断和提示

**预期结果**:
- `questions` 列表最多包含 5 道题
- `message` 包含"最多同时处理5道"或"分批拍照"提示
- 第 6-8 题不出现在返回列表中

---

### UT-08: user_hint 跳过多题检测

**测试目标**: 当用户提供 text（user_hint）时，跳过多题检测。

**前置条件**: 提供 image + text 参数。

**测试步骤**:
1. 调用 `SolverService.solve(image=..., text="第14题")`
2. 验证 `detect_questions()` 未被调用
3. 验证走了现有 `RECOGNITION_FOCUSED_PROMPT` 路径

**预期结果**:
- `detect_questions()` 调用次数为 0
- `OCRService.recognize()` 被调用，且 `user_hint="第14题"`
- 返回结果为常规解题结果

---

### UT-09: 逐题解答 - 正常完成

**测试目标**: "全部解答"模式下按顺序逐题完成。

**前置条件**: mock 解题器对每题返回不同结果。

**测试步骤**:
1. 设置 3 道完整题的上下文
2. 请求"全部解答"
3. 验证逐题解答结果

**预期结果**:
- 返回结果包含 3 题的解答
- 每题解答有分隔标记（如 "**第X题**"）
- 解题器被调用 3 次
- 结果按题号顺序排列

---

### UT-10: 逐题解答 - 部分失败跳过

**测试目标**: 某题解答失败时跳过继续，最后汇总。

**前置条件**: mock 第 2 题解答抛出异常。

**测试步骤**:
1. 设置 3 道题，mock 第 2 题解题器抛出 `Exception`
2. 请求"全部解答"
3. 验证结果

**预期结果**:
- 第 1、3 题解答正常包含在结果中
- 第 2 题被标记为失败/跳过
- 最终结果包含失败汇总提示
- 不因单题失败中断整体流程

---

## 3. 集成测试用例

### IT-01: 单题完整流程

**测试目标**: 端到端验证单题图片的完整解题链路。

**前置条件**: mock LLMService 全部方法。

**测试步骤**:
1. mock `recognize_image()` → 多题检测返回单题 JSON
2. mock `recognize_image()` 第二次调用 → OCR 返回题目文本
3. mock `chat()` → 学科判定返回 "数学"
4. mock `chat()` → 解题返回包含 `\boxed{42}` 的解答
5. 调用 `SolverService.solve(image=sample_png, text=None, ...)`

**预期结果**:
- 返回完整解题结果（非 `question_select` 类型）
- 数据库中创建了 SolvingSession 和 Message 记录

---

### IT-02: 多题选择流程

**测试目标**: 多题检测 → 用户选题 → 解答的完整链路。

**测试步骤**:
1. 上传图片 → mock 多题检测返回 3 道题
2. 验证返回 `question_select` 类型
3. 提交选择第 2 题
4. 验证聚焦 OCR 被调用（hint 为第 2 题编号）
5. 验证解题结果

**预期结果**:
- 第一次调用返回题目列表
- 选题后触发聚焦 OCR + 解题
- 最终返回第 2 题的解答

---

### IT-03: 全部解答流程

**测试目标**: "全部解答"模式的完整链路。

**测试步骤**:
1. 上传图片 → mock 多题检测返回 2 道完整题
2. 提交"全部解答"请求
3. 验证每题分别调用 OCR + 解题

**预期结果**:
- 解题器被调用 2 次
- 返回合并结果，有分隔标记
- 数据库记录正确（共用 session）

---

### IT-04: 数据库持久化验证

**测试目标**: 多题场景下数据库记录正确。

**测试步骤**:
1. 走完多题 → 选题 → 解答流程
2. 查询数据库中的 SolvingSession 和 Message

**预期结果**:
- SolvingSession 记录存在
- Message 包含用户问题和 AI 解答
- 多题全部解答时，所有题目的 Message 关联同一个 session

---

## 4. API 测试用例

### AT-01: POST /solve - 多题检测响应

**测试目标**: 上传多题图片时 API 返回正确的 `question_select` 响应。

**测试步骤**:
1. 构造 multipart 请求，上传图片，不带 text 参数
2. mock 多题检测返回 3 道题
3. POST `/api/solve`

**预期结果**:
- HTTP 200
- 响应 JSON 包含 `type: "question_select"`
- `questions` 数组长度为 3
- 每个 question 有 `number`、`summary`、`complete` 字段
- 包含 `session_id` 和 `message`

---

### AT-02: POST /solve/select - 选题解答

**测试目标**: 提交选题后返回解题结果。

**测试步骤**:
1. 先调用 `/solve` 获取 `session_id`
2. POST `/api/solve/select` with `{"session_id": "...", "selected": [1]}`
3. mock 解题流程

**预期结果**:
- HTTP 200
- 返回标准解题结果（content、subject 等字段）
- 解题仅针对所选题目

---

### AT-03: POST /solve/select - 全部解答

**测试目标**: 提交"全部解答"请求。

**测试步骤**:
1. 先调用 `/solve` 获取 `session_id`
2. POST `/api/solve/select` with `{"session_id": "...", "selected": "all"}`

**预期结果**:
- HTTP 200
- 返回合并的解题结果
- content 包含每题分隔标记

---

### AT-04: POST /solve - user_hint 快捷路径

**测试目标**: 带 text 参数时跳过多题检测。

**测试步骤**:
1. POST `/api/solve` with image + text="第14题"
2. mock OCR 聚焦识别

**预期结果**:
- HTTP 200
- 返回标准解题结果（非 `question_select`）
- 多题检测未被调用

---

### AT-05: POST /solve/select - 无效选择

**测试目标**: 提交不存在的题号时返回错误。

**测试步骤**:
1. POST `/api/solve/select` with `{"session_id": "...", "selected": [99]}`

**预期结果**:
- HTTP 400 或 422
- 错误信息指明题号无效

---

### AT-06: 回归 - 纯文本输入不受影响

**测试目标**: 纯文本输入（无图片）走现有流程，不触发多题检测。

**测试步骤**:
1. POST `/api/solve` with text="求解 x^2 = 4"，无图片
2. mock 解题流程

**预期结果**:
- HTTP 200
- 返回标准解题结果
- 多题检测未被调用

---

## 5. Mock 数据 Fixtures

### 5.1 多题检测 LLM 返回值

```python
# 标准多题响应
MOCK_MULTI_QUESTION_RESPONSE = '''{
  "questions": [
    {"number": "1", "summary": "已知函数 f(x) = x^2 + 2x，求 f(3) 的值", "complete": true},
    {"number": "2", "summary": "如图所示，在三角形ABC中，AB=AC", "complete": true},
    {"number": "3", "summary": "求证：当 a > 0 时", "complete": false}
  ]
}'''

# 单题响应
MOCK_SINGLE_QUESTION_RESPONSE = '''{
  "questions": [
    {"number": "1", "summary": "已知函数 f(x) = x^2 + 2x，求 f(3) 的值", "complete": true}
  ]
}'''

# 全部不完整响应
MOCK_ALL_INCOMPLETE_RESPONSE = '''{
  "questions": [
    {"number": "1", "summary": "已知...", "complete": false},
    {"number": "2", "summary": "如图...", "complete": false}
  ]
}'''

# 超过 5 题响应
MOCK_OVER_LIMIT_RESPONSE = '''{
  "questions": [
    {"number": "1", "summary": "题目1...", "complete": true},
    {"number": "2", "summary": "题目2...", "complete": true},
    {"number": "3", "summary": "题目3...", "complete": true},
    {"number": "4", "summary": "题目4...", "complete": true},
    {"number": "5", "summary": "题目5...", "complete": true},
    {"number": "6", "summary": "题目6...", "complete": true},
    {"number": "7", "summary": "题目7...", "complete": true},
    {"number": "8", "summary": "题目8...", "complete": true}
  ]
}'''

# 异常格式响应
MOCK_MALFORMED_RESPONSE = "这张图片中有两道数学题，一道关于函数，一道关于三角形。"
```

### 5.2 解题结果 Mock

```python
MOCK_SOLVE_RESULT = {
    "content": "解：$f(3) = 3^2 + 2 \\times 3 = 15$\n\n答案：$\\boxed{15}$",
    "verified": True,
    "sympy_result": "15",
}
```

## 6. 验收标准汇总

### 必须通过（P0）

- [ ] UT-01: 多题检测正常解析
- [ ] UT-02: 异常格式降级处理
- [ ] UT-03: 单题快速通道
- [ ] UT-04: 多题按钮组数据结构
- [ ] UT-05: 不完整题目标记
- [ ] UT-06: 全部不完整提示
- [ ] UT-08: user_hint 跳过检测
- [ ] IT-01: 单题完整流程
- [ ] IT-02: 多题选择流程
- [ ] AT-01: 多题检测 API 响应
- [ ] AT-02: 选题解答 API
- [ ] AT-04: user_hint 快捷路径 API
- [ ] AT-06: 回归测试

### 应当通过（P1）

- [ ] UT-07: 超过 5 题限制
- [ ] UT-09: 逐题解答正常
- [ ] UT-10: 逐题解答部分失败
- [ ] IT-03: 全部解答流程
- [ ] IT-04: 数据库持久化
- [ ] AT-03: 全部解答 API
- [ ] AT-05: 无效选择错误处理
