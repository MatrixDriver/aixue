---
description: "技术可行性调研: 多题图片智能识别与选题"
status: archived
created_at: 2026-03-07T22:00:00
updated_at: 2026-03-07T22:00:00
archived_at: null
---

# 技术可行性调研: 多题图片智能识别与选题

## 1. LLM 多题检测 Prompt 设计

### 现有模式分析

现有 OCR 服务（`src/aixue/services/ocr_service.py`）有两个 prompt：
- `RECOGNITION_PROMPT`: 无指定题号时，识别图片中全部题目内容
- `RECOGNITION_FOCUSED_PROMPT`: 有 `user_hint` 时，只提取用户指定的那道题

### 多题检测 Prompt 设计方案

**推荐方案**: 新增独立的 `MULTI_QUESTION_DETECTION_PROMPT`，在 OCR 识别之前运行，专门用于检测题目数量和完整性。

```
请分析这张图片中包含的所有题目，输出 JSON 格式结果。

分析要求:
1. 识别每道题的题号（如"第1题"、"14."等）
2. 判断每道题是否完整（题目文字是否被截断、是否缺少关键条件或问题）
3. 用一句话概括每道题的内容（不超过20字）
4. 最多识别 5 道题

输出格式（严格 JSON，不要包含其他文字）:
{
  "question_count": 数字,
  "questions": [
    {
      "index": 1,
      "label": "题号文字，如 '14' 或 '第3题'",
      "summary": "一句话概括",
      "complete": true/false
    }
  ]
}

如果图片中没有可识别的题目，返回: {"question_count": 0, "questions": []}
```

**关键设计决策**:
- 独立于 OCR 识别步骤：检测只做结构分析，不做内容提取，减少 token 消耗
- 限制输出为 JSON：降低解析复杂度
- `max_tokens` 设为 512 即可，因为只输出结构化摘要

### 可行性: 高

Gemini 系列模型对图片中的文本结构识别能力强，JSON 格式输出在 prompt 约束下稳定性高。现有 `RECOGNITION_FOCUSED_PROMPT` 已证明模型能理解"聚焦特定题目"的指令。

---

## 2. 结构化 JSON 输出

### 现有 API 调用方式

`llm_service.py` 使用 OpenAI 兼容 API（通过 `AsyncOpenAI` 客户端），调用 `client.chat.completions.create()`。

### OpenRouter/Gemini JSON 支持情况

- OpenAI 兼容 API 支持 `response_format={"type": "json_object"}` 参数
- OpenRouter 对大部分模型透传此参数
- **但 Gemini 模型通过 OpenRouter 对 `response_format` 的支持不稳定**，某些模型版本可能忽略此参数

### 推荐方案: Prompt 约束 + 后端 JSON 解析 + 容错

1. **Prompt 中强制要求 JSON 输出**（如上述 prompt 设计）
2. **后端解析时做容错处理**:
   ```python
   import json
   import re

   def parse_detection_result(raw: str) -> dict:
       # 尝试直接解析
       try:
           return json.loads(raw)
       except json.JSONDecodeError:
           pass
       # 尝试提取 JSON 块（处理 ```json ... ``` 包裹）
       match = re.search(r'\{[\s\S]*\}', raw)
       if match:
           try:
               return json.loads(match.group())
           except json.JSONDecodeError:
               pass
       # 兜底: 返回单题结构，回退到原有流程
       return {"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "", "complete": True}]}
   ```

3. **可选增强**: 在 `llm_service.chat()` 中支持传入 `response_format` 参数，但不强依赖:
   ```python
   async def chat(self, messages, ..., response_format=None):
       kwargs = {}
       if response_format:
           kwargs["response_format"] = response_format
       response = await self.client.chat.completions.create(..., **kwargs)
   ```

### 可行性: 高

Prompt 约束 + 正则容错是最稳健的方案，不依赖模型对 `response_format` 的支持。即使模型偶尔输出额外文字，正则提取也能获取 JSON。

---

## 3. 前端按钮组交互

### 现有前端架构分析

- **消息渲染**: `chat-message.tsx` 通过 `dangerouslySetInnerHTML` 渲染 `renderWithLatex()` 处理后的 HTML 内容
- **消息类型**: `Message` 接口（`types.ts`）包含 `role`, `content`, `localImageUrl`, `ocrText` 等字段
- **状态管理**: `use-chat.ts` 的 `useChat()` hook 管理消息列表、会话 ID、loading 状态
- **交互流程**: `sendMessage()` 发送请求 → 添加用户消息 → 等待响应 → 添加 AI 消息

### 按钮组实现方案

**方案 A (推荐): 新增消息类型 + 专用组件**

1. 扩展 `Message` 接口，增加 `type` 字段区分普通消息和选题消息:
   ```typescript
   interface Message {
     // ... 现有字段
     type?: "text" | "question_selection";
     questionOptions?: QuestionOption[];
   }

   interface QuestionOption {
     index: number;
     label: string;
     summary: string;
     complete: boolean;
   }
   ```

2. 在 `ChatMessage` 组件中根据 `type` 渲染不同 UI:
   - `"text"`: 现有的文本渲染逻辑
   - `"question_selection"`: 渲染按钮组组件

3. 按钮组组件 `QuestionSelector`:
   - 每道完整题目显示为可点击按钮: `[第14题: 求解方程...]`
   - 不完整题目显示为灰色禁用按钮 + "不完整" 标签
   - 底部增加 "全部解答" 按钮（仅当完整题 >= 2 时显示）
   - 点击后调用回调函数，触发解题请求

4. 点击交互:
   - 单题: 调用现有 `solveQuestion()` API，传入 `text` 为选中题目的 label（如 "第14题"），同时传入原图片
   - 全部解答: 前端逐题串行调用 `solveQuestion()`，每题结果作为独立 AI 消息追加

**方案 B (备选): 纯后端驱动**

后端返回特殊格式的 content（如 Markdown 按钮），前端解析渲染。但这与现有架构不一致，且交互控制不灵活。

### 推荐方案 A 的优势

- 与现有 `ChatMessage` 组件架构一致（扩展而非重构）
- 按钮状态（已选择/禁用）由前端控制，响应更快
- 选题结果可复用现有的 `sendMessage` 流程

### 可行性: 高

现有组件结构清晰，扩展 `Message` 接口和 `ChatMessage` 组件即可。无需引入新的状态管理库或大幅重构。

---

## 4. 逐题处理的会话管理

### 现有解题流程

```
前端 sendMessage() → POST /solve (image + text + mode)
  → SolverService.solve()
    → _recognize() (OCR)
    → detect_subject()
    → MathSolver/GeneralSolver.solve()
    → _save_session() → 返回 session_id
```

每次调用 `/solve` 创建一个新的 `SolvingSession`，包含一个 user message 和一个 assistant message。

### 逐题处理方案

**方案: 前端驱动逐题调用**

1. **多题检测阶段**: 前端发送图片 → 后端新增 `/detect` 端点 → 返回题目列表（不创建 session）
2. **用户选择**: 前端展示按钮组，用户选择题目
3. **逐题解答**: 前端对每道选中的题目调用现有 `/solve` 端点，传入:
   - `image`: 原始图片（同一张）
   - `text`: 用户选择的题号（如 "第14题"），作为 `user_hint` 触发 `RECOGNITION_FOCUSED_PROMPT`
   - 每题独立创建 `SolvingSession`

**关键设计点**:
- **不修改现有 `/solve` 接口**: 逐题调用直接复用 `RECOGNITION_FOCUSED_PROMPT` 的聚焦识别能力
- **前端串行调用**: 避免并发调用给 LLM API 造成速率限制压力
- **每题独立 session**: 保持现有数据模型不变，每题可独立追问
- **"全部解答" 的 UX**: 前端显示进度指示器（"正在解答第 2/3 题..."），每题完成后立即渲染结果

**备选: 后端批量处理**

后端一次性处理所有选中题目，串行调用解题器，一次性返回。但这会导致长时间等待（每题 5-15 秒 × N 题），用户体验差。前端驱动方案允许逐题展示结果。

### 新增 API 端点

```python
@router.post("/detect")
async def detect_questions(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> DetectResponse:
    """检测图片中的题目数量和完整性。"""
```

返回:
```json
{
  "question_count": 3,
  "questions": [
    {"index": 1, "label": "14", "summary": "求解一元二次方程", "complete": true},
    {"index": 2, "label": "15", "summary": "证明三角恒等式", "complete": true},
    {"index": 3, "label": "16", "summary": "（题目不完整）", "complete": false}
  ]
}
```

### 可行性: 高

核心优势是**复用现有的 `RECOGNITION_FOCUSED_PROMPT` 和 `/solve` 端点**，无需修改解题流程。新增工作量仅为:
- 后端: 1 个新端点 + 1 个检测 prompt + JSON 解析逻辑
- 前端: 检测 API 调用 + 按钮组 UI + 逐题调用编排

---

## 5. 成本影响评估

### 多题检测的额外成本

多题检测需要一次额外的 LLM 多模态调用（图片 + prompt → JSON 输出）。

#### 模型选择分析

| 模型 | 用途 | 输入成本 | 输出成本 | 适合检测? |
|------|------|---------|---------|----------|
| `llm_model` (gemini-3.1-pro) | 解题推理 | 高 | 高 | 过度 |
| `llm_model_light` (gemini-2.5-flash) | 学科判定 | 低 | 低 | 合适 |
| `llm_model_ocr` (配置为空，回退 light) | OCR 识别 | 低 | 低 | 合适 |

#### 推荐: 使用 `llm_model_light`（Gemini Flash）

- **理由**: 多题检测是结构分析任务（数几道题、判断完整性），不需要深度推理能力，Flash 模型足够
- **输出 token 少**: JSON 输出约 200-300 tokens，远低于 OCR 的 2048 上限
- **与学科判定同级**: 复杂度类似于 `detect_subject()`，都是简单分类/判断任务

#### 成本估算

- 检测调用的输入: 图片 token（约 1000-2000）+ prompt token（约 200）
- 检测调用的输出: JSON 约 200 tokens
- 使用 Flash 模型，单次检测成本约 $0.001-0.002

#### 对整体流程的影响

| 场景 | 现有流程 LLM 调用次数 | 新流程 LLM 调用次数 | 增量 |
|------|---------------------|-------------------|------|
| 单题（有 hint） | 2（OCR + 解题） | 2（跳过检测） | 0 |
| 单题（无 hint） | 2（OCR + 解题） | 3（检测 + OCR + 解题） | +1 |
| 多题选单题 | 2 | 3（检测 + OCR + 解题） | +1 |
| 多题全部（3题） | 2（质量差） | 7（检测 + 3×OCR + 3×解题） | +5，但质量大幅提升 |

**结论**: 单题场景增加约 $0.001-0.002 成本（可接受），多题场景虽然调用次数增加但解题质量从"混合解答"提升到"逐题精准解答"，ROI 极高。

---

## 6. 总体可行性结论

| 技术点 | 可行性 | 风险 | 复用现有能力 |
|--------|--------|------|-------------|
| 多题检测 Prompt | 高 | JSON 格式偶尔不规范 → 正则容错解决 | OCR prompt 模式 |
| 结构化 JSON 输出 | 高 | 不依赖 response_format，纯 prompt 约束 | llm_service.chat() |
| 前端按钮组交互 | 高 | 无重大风险 | Message 类型扩展 |
| 逐题处理会话管理 | 高 | 前端串行调用需处理错误和进度 | RECOGNITION_FOCUSED_PROMPT + /solve |
| 成本控制 | 高 | Flash 模型成本可忽略 | llm_model_light 配置 |

### 核心架构洞察

**现有 `RECOGNITION_FOCUSED_PROMPT` + `user_hint` 机制是本功能的关键复用点**。多题检测后，每题的解答只需将题号作为 `text` 参数传入现有 `/solve` 端点，触发聚焦识别，无需修改解题核心流程。这意味着:

1. 后端核心改动: 1 个新端点 (`/detect`) + 1 个检测 service 方法 + JSON 解析
2. 前端改动: 检测 API 集成 + `QuestionSelector` 按钮组件 + `useChat` 逐题调用逻辑
3. **不需要修改**: `SolverService.solve()`、`MathSolver`、`GeneralSolver`、数据模型
