---
description: "功能实施计划: multi-question-detection"
status: archived
created_at: 2026-03-07T22:35:00
updated_at: 2026-03-07T22:45:00
archived_at: null
related_files:
  - rpiv/requirements/prd-multi-question-detection.md
---

# 功能：多题图片智能识别与选题

以下计划应该是完整的，但在开始实施之前，验证文档和代码库模式以及任务合理性非常重要。

特别注意现有工具、类型和模型的命名。从正确的文件导入等。

## 功能描述

在现有解题流程中增加"多题检测"环节：用户上传图片后，先用 LLM light 模型分析图中题目数量、编号和完整性，再根据结果分流——单题直接解答（零额外交互）、多题返回选题按钮组、全部不完整提示重拍。用户选择题目后，复用现有聚焦 OCR + 解题流程逐题解答。

## 用户故事

作为初中/高中学生
我想要上传包含多道题目的试卷/作业照片后，能选择要解答的具体题目
以便不用反复裁剪拍照，且每道题都能获得高质量的独立解答

## 问题陈述

当前系统假设每张图片只有一道题目。多题图片导致 OCR 混合识别、解答质量差、不完整题目浪费 LLM 调用。

## 解决方案陈述

在 OCR 之前新增一次轻量 LLM 调用进行结构分析（题目数量+完整性），返回结构化结果让用户选题。选题后复用现有 `RECOGNITION_FOCUSED_PROMPT` 聚焦识别，完全不改变核心解题流程。

## 功能元数据

**功能类型**：新功能
**估计复杂度**：中
**主要受影响的系统**：OCR 服务、解题 API 端点、前端对话 Hook 和消息组件
**依赖项**：无新增外部依赖

---

## 上下文参考

### 相关代码库文件（实施前必须阅读）

**后端**：
- `src/aixue/services/ocr_service.py`（全文）— OCR 服务，包含 `RECOGNITION_PROMPT`、`RECOGNITION_FOCUSED_PROMPT`、`OCRService` 类。新增 `detect_questions()` 方法和 `MULTI_QUESTION_DETECTION_PROMPT` 在此文件
- `src/aixue/services/solver_service.py`（全文）— 解题主控，`solve()` 方法（第 36-94 行）是流程改造入口，`_recognize()` 方法（第 164-189 行）处理 OCR + user_hint 逻辑
- `src/aixue/services/llm_service.py`（第 119-152 行）— `recognize_image()` 方法，多模态 LLM 图片识别入口，多题检测将复用此方法
- `src/aixue/api/endpoints/solver.py`（全文）— API 端点，新增 `/detect` 端点在此文件
- `src/aixue/schemas/session.py`（全文）— Pydantic schema，新增 `DetectResponse`、`QuestionInfo` 在此文件
- `src/aixue/api/router.py`（全文）— 路由聚合，无需修改（solver.router 已注册）
- `src/aixue/config.py`（全文）— 配置，无需修改（`llm_model_light` 已存在）

**前端**：
- `frontend/src/lib/types.ts`（第 76-85 行）— `Message` 接口定义，需扩展 `type` 和 `questionOptions` 字段
- `frontend/src/lib/types.ts`（第 107-118 行）— `SolveResponse` 接口，无需修改
- `frontend/src/lib/api.ts`（第 102-120 行）— `solveQuestion()` 函数，新增 `detectQuestions()` 函数在此文件
- `frontend/src/hooks/use-chat.ts`（全文）— `useChat()` hook，需改造 `sendMessage()` 以支持检测→选题→解答流程
- `frontend/src/components/chat/chat-message.tsx`（第 118-223 行）— `ChatMessage` 组件，需根据 `type` 字段条件渲染选题按钮组
- `frontend/src/components/chat/chat-container.tsx`（第 112-141 行）— 消息列表渲染，需传递 `onSelectQuestion` 回调给 `ChatMessage`
- `frontend/src/components/chat/chat-input.tsx`（全文）— 输入组件，无需修改

**测试**：
- `tests/conftest.py`（全文）— 测试 fixtures（`db_session`、`client`、`auth_token`、`sample_math_image`）
- `tests/test_services/test_solver_service.py`（全文）— 解题服务测试，mock 模式参考

### 要创建的新文件

- `frontend/src/components/chat/question-selector.tsx` — 选题按钮组组件

### 要遵循的模式

**后端命名约定**：
- 服务方法用 snake_case：`detect_questions()`、`recognize()`、`detect_subject()`
- Prompt 常量用 UPPER_SNAKE_CASE：`MULTI_QUESTION_DETECTION_PROMPT`
- Schema 类用 PascalCase：`DetectResponse`、`QuestionInfo`
- Logger 统一用 `logger = logging.getLogger(__name__)`

**后端错误处理模式**（参考 `solver.py` 第 93-104 行）：
```python
try:
    result = await service.method(...)
except ValueError as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
```

**后端 LLM 调用模式**（参考 `ocr_service.py` 第 95-101 行）：
```python
result = await self.llm.recognize_image(
    image_data=image_data,
    media_type=media_type,
    prompt=prompt,
    max_tokens=_OCR_MAX_TOKENS,
)
```

**前端消息处理模式**（参考 `use-chat.ts` 第 36-47 行）：
```typescript
const userMsg: Message = {
    id: `temp-${Date.now()}`,
    session_id: state.sessionId || "",
    role: "user",
    content: text || "[图片]",
    localImageUrl: image ? URL.createObjectURL(image) : undefined,
    created_at: new Date().toISOString(),
};
setState((prev) => ({
    ...prev,
    messages: [...prev.messages, userMsg],
}));
```

**前端 API 调用模式**（参考 `api.ts` 第 102-120 行）：
```typescript
export async function detectQuestions(image: File): Promise<DetectResponse> {
    const formData = new FormData();
    formData.append("image", image);
    const res = await api.post<DetectResponse>("/detect", formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
}
```

**前端组件模式**（参考 `chat-message.tsx`）：
- 使用 `"use client"` 指令
- Props 用 interface 定义
- 使用 `cn()` 工具函数合并 Tailwind 类名
- 使用 lucide-react 图标库

**测试 mock 模式**（参考 `test_solver_service.py`）：
```python
mock_llm = AsyncMock()
mock_llm.recognize_image = AsyncMock(return_value="...")
solver = SolverService(llm=mock_llm, verifier=mock_verifier)
```

---

## 实施计划

### 阶段 1：后端基础（Schema + 检测服务）

新增 Pydantic schema 和 OCR 检测方法，为 API 层提供数据结构和业务逻辑。

### 阶段 2：后端 API（检测端点 + solve 流程适配）

新增 `/detect` 端点，修改 `solve()` 让无 hint 的图片走检测流程。

### 阶段 3：前端（类型 + API + 组件 + Hook）

扩展前端类型、新增 API 函数、创建选题按钮组件、改造 useChat hook。

### 阶段 4：测试

后端单元测试 + API 集成测试。

---

## 逐步任务

重要：按顺序从上到下执行每个任务。每个任务都是原子的且可独立测试。

---

### 任务 1: UPDATE `src/aixue/schemas/session.py` — 新增检测响应 Schema

- **IMPLEMENT**：在文件末尾新增两个 Pydantic 模型：
  ```python
  class QuestionInfo(BaseModel):
      """检测到的单道题目信息。"""
      index: int
      label: str
      summary: str
      complete: bool

  class DetectResponse(BaseModel):
      """多题检测响应。"""
      question_count: int
      questions: list[QuestionInfo]
      message: str
  ```
- **PATTERN**：遵循同文件 `SolveResponse`（第 8-19 行）的风格
- **IMPORTS**：无需新增导入，`BaseModel` 已在文件顶部导入
- **VALIDATE**：`uv run python -c "from aixue.schemas.session import DetectResponse, QuestionInfo; print('OK')"`

---

### 任务 2: UPDATE `src/aixue/services/ocr_service.py` — 新增多题检测 Prompt 和方法

- **IMPLEMENT**：
  1. 在 `SUBJECT_DETECTION_PROMPT` 之后新增 `MULTI_QUESTION_DETECTION_PROMPT` 常量：
     ```python
     MULTI_QUESTION_DETECTION_PROMPT = """请分析这张图片中包含的所有题目，输出 JSON 格式结果。

     分析要求:
     1. 识别每道题的题号（如"第1题"、"14."等）
     2. 判断每道题是否完整（题目文字是否被截断、是否缺少关键条件或问题）
     3. 用一句话概括每道题的内容（不超过20字）
     4. 最多识别5道题

     输出格式（严格 JSON，不要包含其他文字）:
     {"question_count": 数字, "questions": [{"index": 1, "label": "题号文字", "summary": "一句话概括", "complete": true}]}

     如果图片中没有可识别的题目，返回: {"question_count": 0, "questions": []}"""
     ```
  2. 新增常量 `_DETECT_MAX_TOKENS = 512`
  3. 在 `OCRService` 类中新增 `detect_questions()` 方法：
     ```python
     async def detect_questions(
         self,
         image_data: bytes,
         media_type: str,
     ) -> dict:
         """检测图片中的题目数量和完整性。

         Returns:
             包含 question_count 和 questions 列表的字典
         """
         logger.info("开始多题检测: size=%d bytes", len(image_data))
         raw = await self.llm.recognize_image(
             image_data=image_data,
             media_type=media_type,
             prompt=MULTI_QUESTION_DETECTION_PROMPT,
             max_tokens=_DETECT_MAX_TOKENS,
         )
         result = self._parse_detection_result(raw)
         logger.info(
             "多题检测完成: question_count=%d",
             result.get("question_count", 0),
         )
         return result

     @staticmethod
     def _parse_detection_result(raw: str) -> dict:
         """解析 LLM 返回的多题检测 JSON，带容错。"""
         import json
         import re

         # 尝试直接解析
         try:
             return json.loads(raw)
         except json.JSONDecodeError:
             pass
         # 尝试提取 JSON 块
         match = re.search(r'\{[\s\S]*\}', raw)
         if match:
             try:
                 return json.loads(match.group())
             except json.JSONDecodeError:
                 pass
         # 兜底：回退为单题
         logger.warning("多题检测 JSON 解析失败，回退为单题: raw=%s", raw[:200])
         return {
             "question_count": 1,
             "questions": [{"index": 1, "label": "1", "summary": "", "complete": True}],
         }
     ```
- **PATTERN**：方法签名参考同类 `recognize()` 方法（第 68-102 行），logger 使用同文件顶部的 `logger`
- **IMPORTS**：`json` 和 `re` 在方法内部导入（仅此方法使用）
- **GOTCHA**：`_parse_detection_result` 用 `@staticmethod` 但需访问 `logger`，改为普通函数放在类外面或在类内去掉 `@staticmethod`。建议去掉 `@staticmethod` 改为普通方法，或将 logger 调用放在 `detect_questions` 中而非解析方法中
- **VALIDATE**：`uv run python -c "from aixue.services.ocr_service import OCRService; print('OK')"`

---

### 任务 3: UPDATE `src/aixue/api/endpoints/solver.py` — 新增 `/detect` 端点

- **IMPLEMENT**：
  1. 在文件顶部导入新增 schema：
     ```python
     from aixue.schemas.session import (
         ...,  # 保留现有导入
         DetectResponse,
         QuestionInfo,
     )
     from aixue.services.ocr_service import OCRService
     from aixue.services.llm_service import LLMService
     ```
  2. 在 `solve_problem` 端点之前新增 `/detect` 端点：
     ```python
     @router.post("/detect", response_model=DetectResponse)
     async def detect_questions(
         image: UploadFile = File(...),
         current_user: User = Depends(get_current_user),
     ) -> DetectResponse:
         """检测图片中的题目数量和完整性。"""
         image_data = await image.read()
         if len(image_data) > settings.max_image_size:
             raise HTTPException(
                 status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                 detail=f"图片大小超过限制({settings.max_image_size // 1024 // 1024}MB)",
             )
         media_type = image.content_type or "image/png"

         llm = LLMService()
         ocr = OCRService(llm)
         try:
             result = await ocr.detect_questions(image_data, media_type)
         except ValueError as e:
             raise HTTPException(
                 status_code=status.HTTP_502_BAD_GATEWAY,
                 detail=str(e),
             ) from e

         questions = result.get("questions", [])
         question_count = result.get("question_count", len(questions))

         # 限制最多 5 题
         if question_count > 5:
             questions = questions[:5]
             msg = f"检测到 {question_count} 道题目，最多同时处理 5 道，建议分批拍照"
         elif question_count == 0:
             msg = "未检测到完整题目，请重新拍照确保题目完整"
         else:
             complete_count = sum(1 for q in questions if q.get("complete", False))
             if complete_count == 0:
                 msg = "检测到的题目均不完整，请重新拍照确保题目完整"
             else:
                 msg = f"检测到 {question_count} 道题目，请选择要解答的题目"

         return DetectResponse(
             question_count=question_count,
             questions=[QuestionInfo(**q) for q in questions],
             message=msg,
         )
     ```
- **PATTERN**：图片大小校验参考同文件 `solve_problem`（第 74-79 行），异常处理参考第 93-98 行
- **IMPORTS**：需新增 `OCRService` 和 `LLMService` 导入，`DetectResponse` 和 `QuestionInfo` 加入现有 schema 导入
- **GOTCHA**：`DetectResponse` 需要在 schema 中先定义（任务 1），`OCRService` 和 `LLMService` 的直接实例化参考 `solve_problem` 中的 `SolverService()` 模式（第 81 行），`SolverService()` 内部自行创建这两个服务
- **VALIDATE**：`uv run python -c "from aixue.api.endpoints.solver import router; print('OK')"`

---

### 任务 4: UPDATE `frontend/src/lib/types.ts` — 扩展前端类型

- **IMPLEMENT**：
  1. 在 `Message` 接口（第 76-85 行）中新增可选字段：
     ```typescript
     export interface Message {
       // ... 现有字段保持不变
       id: string;
       session_id: string;
       role: MessageRole;
       content: string;
       image_path?: string;
       localImageUrl?: string;
       ocrText?: string;
       created_at: string;
       /** 消息类型：普通文本或选题 */
       type?: "text" | "question_selection";
       /** 多题检测结果（type 为 question_selection 时使用） */
       questionOptions?: QuestionOption[];
     }
     ```
  2. 在 `Message` 接口之后新增类型定义：
     ```typescript
     /** 检测到的单道题目选项 */
     export interface QuestionOption {
       index: number;
       label: string;
       summary: string;
       complete: boolean;
     }

     /** 多题检测 API 响应 */
     export interface DetectResponse {
       question_count: number;
       questions: QuestionOption[];
       message: string;
     }
     ```
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 5: UPDATE `frontend/src/lib/api.ts` — 新增 detectQuestions API 函数

- **IMPLEMENT**：
  1. 在文件顶部 import 中新增 `DetectResponse` 类型：
     ```typescript
     import type {
       ...,  // 保留现有导入
       DetectResponse,
     } from "./types";
     ```
  2. 在 `solveQuestion` 函数之前新增：
     ```typescript
     export async function detectQuestions(image: File): Promise<DetectResponse> {
       const formData = new FormData();
       formData.append("image", image);
       const res = await api.post<DetectResponse>("/detect", formData, {
         headers: { "Content-Type": "multipart/form-data" },
       });
       return res.data;
     }
     ```
- **PATTERN**：完全参考 `solveQuestion`（第 102-120 行）的 FormData + multipart 模式
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 6: CREATE `frontend/src/components/chat/question-selector.tsx` — 选题按钮组组件

- **IMPLEMENT**：
  ```tsx
  "use client";

  import { useState } from "react";
  import { cn } from "@/lib/utils";
  import type { QuestionOption } from "@/lib/types";

  interface QuestionSelectorProps {
    questions: QuestionOption[];
    message: string;
    onSelect: (selected: QuestionOption) => void;
    onSelectAll: () => void;
    disabled?: boolean;
  }

  export default function QuestionSelector({
    questions,
    message,
    onSelect,
    onSelectAll,
    disabled = false,
  }: QuestionSelectorProps) {
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const completeQuestions = questions.filter((q) => q.complete);

    const handleSelect = (q: QuestionOption) => {
      if (!q.complete || disabled) return;
      setSelectedIndex(q.index);
      onSelect(q);
    };

    const handleSelectAll = () => {
      if (disabled) return;
      setSelectedIndex(-1); // -1 表示全部
      onSelectAll();
    };

    return (
      <div className="space-y-2">
        <p className="text-sm text-gray-600">{message}</p>
        <div className="flex flex-col gap-2">
          {questions.map((q) => (
            <button
              key={q.index}
              onClick={() => handleSelect(q)}
              disabled={!q.complete || disabled || selectedIndex !== null}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                q.complete && selectedIndex === null && !disabled
                  ? "border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 cursor-pointer"
                  : "",
                !q.complete
                  ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                  : "",
                selectedIndex === q.index
                  ? "border-indigo-500 bg-indigo-100 ring-2 ring-indigo-200"
                  : "",
                selectedIndex !== null && selectedIndex !== q.index
                  ? "opacity-50"
                  : ""
              )}
            >
              <span className="font-medium shrink-0">
                {q.label ? `第${q.label}题` : `题目 ${q.index}`}
              </span>
              <span className="truncate">{q.summary}</span>
              {!q.complete && (
                <span className="ml-auto shrink-0 rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-500">
                  不完整
                </span>
              )}
            </button>
          ))}

          {completeQuestions.length >= 2 && (
            <button
              onClick={handleSelectAll}
              disabled={disabled || selectedIndex !== null}
              className={cn(
                "rounded-lg border-2 border-dashed px-3 py-2 text-sm font-medium transition-colors",
                selectedIndex === null && !disabled
                  ? "border-emerald-300 text-emerald-600 hover:bg-emerald-50 cursor-pointer"
                  : "",
                selectedIndex === -1
                  ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-200"
                  : "",
                selectedIndex !== null && selectedIndex !== -1
                  ? "opacity-50"
                  : ""
              )}
            >
              全部解答（{completeQuestions.length} 道题）
            </button>
          )}
        </div>
      </div>
    );
  }
  ```
- **PATTERN**：组件结构参考 `chat-message.tsx`（`"use client"` + interface Props + default export），样式使用 `cn()` + Tailwind
- **IMPORTS**：`cn` 从 `@/lib/utils`，`QuestionOption` 从 `@/lib/types`
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 7: UPDATE `frontend/src/components/chat/chat-message.tsx` — 条件渲染选题按钮组

- **IMPLEMENT**：
  1. 新增导入：
     ```typescript
     import QuestionSelector from "./question-selector";
     import type { QuestionOption } from "@/lib/types";
     ```
  2. 扩展 `ChatMessageProps` 接口，新增可选字段：
     ```typescript
     interface ChatMessageProps {
       // ... 现有字段
       type?: "text" | "question_selection";
       questionOptions?: QuestionOption[];
       onSelectQuestion?: (selected: QuestionOption) => void;
       onSelectAll?: () => void;
       selectionDisabled?: boolean;
     }
     ```
  3. 在函数参数中解构新字段：
     ```typescript
     export default function ChatMessage({
       role,
       content,
       imagePath,
       localImageUrl,
       ocrText,
       ocrLoading,
       timestamp,
       type,
       questionOptions,
       onSelectQuestion,
       onSelectAll,
       selectionDisabled,
     }: ChatMessageProps) {
     ```
  4. 在"文字内容"部分（`showTextBubble` 条件渲染，约第 192-209 行）之后，`timestamp` 之前，新增选题按钮组渲染：
     ```tsx
     {/* 选题按钮组 */}
     {type === "question_selection" && questionOptions && onSelectQuestion && onSelectAll && (
       <div className="inline-block rounded-2xl px-4 py-3 bg-white shadow-sm border border-gray-100">
         <QuestionSelector
           questions={questionOptions}
           message={content}
           onSelect={onSelectQuestion}
           onSelectAll={onSelectAll}
           disabled={selectionDisabled}
         />
       </div>
     )}
     ```
  5. 当 `type === "question_selection"` 时，隐藏普通文字气泡（将 `showTextBubble` 逻辑调整）：
     ```typescript
     const showTextBubble = !(content === "[图片]" && displayImageUrl) && type !== "question_selection";
     ```
- **PATTERN**：条件渲染参考同文件 `displayImageUrl &&` 块（第 160-189 行）
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 8: UPDATE `frontend/src/components/chat/chat-container.tsx` — 传递选题回调

- **IMPLEMENT**：
  1. 新增导入：
     ```typescript
     import type { QuestionOption } from "@/lib/types";
     ```
  2. 扩展 `ChatContainerProps` 接口：
     ```typescript
     interface ChatContainerProps {
       // ... 现有字段
       onSelectQuestion?: (selected: QuestionOption) => void;
       onSelectAll?: () => void;
       selectionDisabled?: boolean;
     }
     ```
  3. 在函数参数中解构新字段
  4. 修改 `ChatMessage` 渲染（第 113-124 行），传递新 props：
     ```tsx
     <ChatMessage
       key={msg.id}
       role={msg.role}
       content={msg.content}
       imagePath={msg.image_path}
       localImageUrl={msg.localImageUrl}
       ocrText={msg.ocrText}
       ocrLoading={msg.role === "user" && !!msg.localImageUrl && msg.ocrText === undefined && loading}
       timestamp={msg.created_at}
       type={msg.type}
       questionOptions={msg.questionOptions}
       onSelectQuestion={onSelectQuestion}
       onSelectAll={onSelectAll}
       selectionDisabled={selectionDisabled}
     />
     ```
- **PATTERN**：Props 传递参考现有 `ChatMessage` 渲染（第 113-124 行）
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 9: UPDATE `frontend/src/hooks/use-chat.ts` — 改造消息发送流程

- **IMPLEMENT**：
  1. 新增导入：
     ```typescript
     import { detectQuestions, solveQuestion, followUp } from "@/lib/api";
     import type { Message, SolveMode, SolveResponse, FollowUpResponse, QuestionOption, DetectResponse } from "@/lib/types";
     ```
  2. 在 `ChatState` 接口中新增：
     ```typescript
     interface ChatState {
       // ... 现有字段
       pendingImage: File | null;       // 多题检测后暂存的原始图片
       detecting: boolean;               // 多题检测中
       selectionDisabled: boolean;       // 选题按钮是否禁用
     }
     ```
     初始状态新增：`pendingImage: null, detecting: false, selectionDisabled: false`
  3. 改造 `sendMessage` 函数核心逻辑（当前代码第 49-94 行）：
     ```typescript
     // 在 try 块内，替换 "新题目" 分支（else 分支，第 65-82 行）：
     if (state.sessionId) {
       // 追问模式 — 保持不变
       ...
     } else {
       // 新题目
       if (image && !text) {
         // 仅图片，无 user_hint → 触发多题检测
         setState((prev) => ({ ...prev, detecting: true }));
         try {
           const detectResult: DetectResponse = await detectQuestions(image);
           const completeQuestions = detectResult.questions.filter((q) => q.complete);

           if (completeQuestions.length === 1 && detectResult.question_count <= 1) {
             // 单题快速通道：直接解题
             const response: SolveResponse = await solveQuestion({
               image,
               mode: state.mode,
             });
             newSessionId = response.session_id;
             ocrQuestion = response.question;
             aiMsg = {
               id: `ai-${Date.now()}`,
               session_id: response.session_id,
               role: "assistant",
               content: response.content,
               created_at: new Date().toISOString(),
             };
           } else {
             // 多题或全不完整 → 返回选题消息
             setState((prev) => ({
               ...prev,
               detecting: false,
               loading: false,
               pendingImage: image,
               messages: [...prev.messages, {
                 id: `detect-${Date.now()}`,
                 session_id: "",
                 role: "assistant" as const,
                 content: detectResult.message,
                 created_at: new Date().toISOString(),
                 type: "question_selection" as const,
                 questionOptions: detectResult.questions,
               }],
             }));
             return; // 等待用户选择
           }
         } finally {
           setState((prev) => ({ ...prev, detecting: false }));
         }
       } else {
         // 有文字（可能含图片）→ 现有流程（user_hint 跳过检测）
         const response: SolveResponse = await solveQuestion({
           text: text || undefined,
           image: image || undefined,
           subject: state.subject || undefined,
           mode: state.mode,
         });
         newSessionId = response.session_id;
         ocrQuestion = response.question;
         aiMsg = {
           id: `ai-${Date.now()}`,
           session_id: response.session_id,
           role: "assistant",
           content: response.content,
           created_at: new Date().toISOString(),
         };
       }
     }
     ```
  4. 新增 `selectQuestion` 回调：
     ```typescript
     const selectQuestion = useCallback(
       async (selected: QuestionOption) => {
         if (!state.pendingImage) return;
         setState((prev) => ({ ...prev, loading: true, selectionDisabled: true }));

         try {
           const response: SolveResponse = await solveQuestion({
             image: state.pendingImage,
             text: selected.label ? `第${selected.label}题` : `题目${selected.index}`,
             mode: state.mode,
           });

           const aiMsg: Message = {
             id: `ai-${Date.now()}`,
             session_id: response.session_id,
             role: "assistant",
             content: response.content,
             created_at: new Date().toISOString(),
           };

           setState((prev) => ({
             ...prev,
             messages: [...prev.messages, aiMsg],
             sessionId: response.session_id,
             loading: false,
             pendingImage: null,
           }));
         } catch (err: unknown) {
           const message =
             (err as { response?: { data?: { detail?: string } } })?.response
               ?.data?.detail || "解题失败，请稍后重试";
           setState((prev) => ({
             ...prev,
             loading: false,
             selectionDisabled: false,
             error: message,
           }));
         }
       },
       [state.pendingImage, state.mode]
     );
     ```
  5. 新增 `selectAll` 回调：
     ```typescript
     const selectAll = useCallback(
       async () => {
         if (!state.pendingImage) return;
         // 找到选题消息中的完整题目
         const selectionMsg = state.messages.find((m) => m.type === "question_selection");
         const completeQuestions = selectionMsg?.questionOptions?.filter((q) => q.complete) || [];
         if (completeQuestions.length === 0) return;

         setState((prev) => ({ ...prev, loading: true, selectionDisabled: true }));

         const results: Message[] = [];
         const failures: string[] = [];

         for (const q of completeQuestions) {
           try {
             const response: SolveResponse = await solveQuestion({
               image: state.pendingImage!,
               text: q.label ? `第${q.label}题` : `题目${q.index}`,
               mode: state.mode,
             });
             results.push({
               id: `ai-${Date.now()}-${q.index}`,
               session_id: response.session_id,
               role: "assistant",
               content: `**第${q.label || q.index}题**\n\n${response.content}`,
               created_at: new Date().toISOString(),
             });
           } catch {
             failures.push(q.label || String(q.index));
           }
         }

         if (failures.length > 0) {
           results.push({
             id: `ai-fail-${Date.now()}`,
             session_id: "",
             role: "assistant",
             content: `以下题目解答失败：${failures.join("、")}，请稍后重试。`,
             created_at: new Date().toISOString(),
           });
         }

         setState((prev) => ({
           ...prev,
           messages: [...prev.messages, ...results],
           sessionId: results.length > 0 ? results[results.length - 1].session_id : prev.sessionId,
           loading: false,
           pendingImage: null,
         }));
       },
       [state.pendingImage, state.mode, state.messages]
     );
     ```
  6. 更新 `newChat` 中的初始状态重置，新增 `pendingImage: null, detecting: false, selectionDisabled: false`
  7. 更新 return 对象，新增导出：
     ```typescript
     return {
       // ... 现有字段
       detecting: state.detecting,
       selectionDisabled: state.selectionDisabled,
       selectQuestion,
       selectAll,
     };
     ```
- **GOTCHA**：
  - `sendMessage` 中检测流程有提前 return，需确保 loading 状态正确管理
  - `selectAll` 中串行调用 `solveQuestion`，每次都传同一张 `pendingImage`
  - `newChat` 需清理 `pendingImage`
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 10: UPDATE 前端页面调用 — 传递新 props 给 ChatContainer

- **IMPLEMENT**：找到使用 `ChatContainer` 的页面组件（通过 `grep ChatContainer` 定位），将 `useChat()` 返回的新字段传递给 `ChatContainer`：
  ```tsx
  const { ..., selectQuestion, selectAll, selectionDisabled } = useChat();

  <ChatContainer
    // ... 现有 props
    onSelectQuestion={selectQuestion}
    onSelectAll={selectAll}
    selectionDisabled={selectionDisabled}
  />
  ```
- **PATTERN**：查找 `import ChatContainer` 和 `<ChatContainer` 来定位需要修改的文件
- **VALIDATE**：`cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### 任务 11: CREATE `tests/test_services/test_ocr_detect.py` — 多题检测单元测试

- **IMPLEMENT**：
  ```python
  """多题检测服务单元测试。"""

  from unittest.mock import AsyncMock

  import pytest

  from aixue.services.llm_service import LLMService
  from aixue.services.ocr_service import OCRService


  @pytest.fixture
  def mock_llm():
      llm = AsyncMock(spec=LLMService)
      return llm


  @pytest.fixture
  def ocr_service(mock_llm):
      return OCRService(mock_llm)


  class TestDetectQuestions:
      """多题检测测试。"""

      @pytest.mark.asyncio
      async def test_single_complete_question(self, ocr_service, mock_llm):
          """单题完整：返回 1 道题。"""
          mock_llm.recognize_image = AsyncMock(
              return_value='{"question_count": 1, "questions": [{"index": 1, "label": "14", "summary": "求解方程", "complete": true}]}'
          )
          result = await ocr_service.detect_questions(b"fake-image", "image/png")
          assert result["question_count"] == 1
          assert len(result["questions"]) == 1
          assert result["questions"][0]["complete"] is True

      @pytest.mark.asyncio
      async def test_multiple_questions(self, ocr_service, mock_llm):
          """多题：返回多道题。"""
          mock_llm.recognize_image = AsyncMock(
              return_value='{"question_count": 3, "questions": [{"index": 1, "label": "1", "summary": "方程", "complete": true}, {"index": 2, "label": "2", "summary": "几何", "complete": true}, {"index": 3, "label": "3", "summary": "不完整", "complete": false}]}'
          )
          result = await ocr_service.detect_questions(b"fake-image", "image/png")
          assert result["question_count"] == 3
          assert len(result["questions"]) == 3
          complete = [q for q in result["questions"] if q["complete"]]
          assert len(complete) == 2

      @pytest.mark.asyncio
      async def test_no_questions(self, ocr_service, mock_llm):
          """无题目：返回空列表。"""
          mock_llm.recognize_image = AsyncMock(
              return_value='{"question_count": 0, "questions": []}'
          )
          result = await ocr_service.detect_questions(b"fake-image", "image/png")
          assert result["question_count"] == 0
          assert len(result["questions"]) == 0

      @pytest.mark.asyncio
      async def test_json_with_markdown_wrapper(self, ocr_service, mock_llm):
          """LLM 返回 markdown 包裹的 JSON 也能解析。"""
          mock_llm.recognize_image = AsyncMock(
              return_value='```json\n{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "test", "complete": true}]}\n```'
          )
          result = await ocr_service.detect_questions(b"fake-image", "image/png")
          assert result["question_count"] == 1

      @pytest.mark.asyncio
      async def test_invalid_json_fallback(self, ocr_service, mock_llm):
          """JSON 解析失败时回退为单题。"""
          mock_llm.recognize_image = AsyncMock(
              return_value="这不是 JSON 格式的内容"
          )
          result = await ocr_service.detect_questions(b"fake-image", "image/png")
          assert result["question_count"] == 1
          assert result["questions"][0]["complete"] is True


  class TestParseDetectionResult:
      """JSON 解析容错测试。"""

      def test_valid_json(self, ocr_service):
          result = ocr_service._parse_detection_result(
              '{"question_count": 2, "questions": []}'
          )
          assert result["question_count"] == 2

      def test_json_with_extra_text(self, ocr_service):
          result = ocr_service._parse_detection_result(
              '分析结果如下：\n{"question_count": 1, "questions": [{"index": 1, "label": "1", "summary": "x", "complete": true}]}\n以上'
          )
          assert result["question_count"] == 1

      def test_completely_invalid(self, ocr_service):
          result = ocr_service._parse_detection_result("无法解析")
          assert result["question_count"] == 1  # 回退为单题
  ```
- **PATTERN**：测试结构参考 `test_solver_service.py`（AsyncMock + pytest.mark.asyncio + class 分组）
- **VALIDATE**：`cd "D:/CODE/aixue" && uv run pytest tests/test_services/test_ocr_detect.py -v`

---

### 任务 12: UPDATE `tests/test_api/test_solver.py` — 新增 /detect 端点集成测试

- **IMPLEMENT**：在现有测试文件末尾新增测试类：
  ```python
  class TestDetectEndpoint:
      """多题检测 API 端点测试。"""

      @pytest.mark.asyncio
      async def test_detect_requires_auth(self, client):
          """未认证请求返回 401。"""
          resp = await client.post("/api/detect")
          assert resp.status_code == 401

      @pytest.mark.asyncio
      async def test_detect_requires_image(self, client, auth_headers):
          """缺少图片返回 422。"""
          resp = await client.post("/api/detect", headers=auth_headers)
          assert resp.status_code == 422

      @pytest.mark.asyncio
      async def test_detect_oversized_image(self, client, auth_headers, oversized_image):
          """超大图片返回 413。"""
          resp = await client.post(
              "/api/detect",
              headers=auth_headers,
              files={"image": ("big.png", oversized_image, "image/png")},
          )
          assert resp.status_code == 413
  ```
- **PATTERN**：参考同文件现有测试的 fixture 使用方式
- **GOTCHA**：需先读取 `tests/test_api/test_solver.py` 现有内容确认结构
- **VALIDATE**：`cd "D:/CODE/aixue" && uv run pytest tests/test_api/test_solver.py -v -k "detect"`

---

## 测试策略

### 单元测试

- `test_ocr_detect.py`：覆盖多题检测服务的核心逻辑
  - 单题/多题/无题目/不完整题目场景
  - JSON 解析容错（正常 JSON、markdown 包裹、无效内容）
  - 验证 LLM 调用参数（model、prompt、max_tokens）

### 集成测试

- `test_solver.py` 中新增 `/detect` 端点测试
  - 认证检查（401）
  - 参数校验（422）
  - 图片大小限制（413）

### 边缘情况

- LLM 返回空 choices（已有重试机制覆盖）
- JSON 中 `question_count` 与 `questions` 数组长度不一致
- `questions` 数组中 `complete` 字段缺失
- 前端 `pendingImage` 在用户切换页面后被清理

---

## 验证命令

### 级别 1：语法和样式

```bash
cd "D:/CODE/aixue" && uv run ruff check src/
cd "D:/CODE/aixue/frontend" && npx tsc --noEmit --pretty
```

### 级别 2：单元测试

```bash
cd "D:/CODE/aixue" && uv run pytest tests/test_services/test_ocr_detect.py -v
```

### 级别 3：集成测试

```bash
cd "D:/CODE/aixue" && uv run pytest tests/test_api/test_solver.py -v -k "detect"
```

### 级别 4：全量回归

```bash
cd "D:/CODE/aixue" && uv run pytest -v
cd "D:/CODE/aixue/frontend" && npm run build
```

### 级别 5：手动验证

1. 启动后端：`cd "D:/CODE/aixue" && uv run uvicorn aixue.main:app --reload`
2. 启动前端：`cd "D:/CODE/aixue/frontend" && npm run dev`
3. 登录后上传一张包含多道题目的试卷照片
4. 验证：
   - 多题图片显示选题按钮组
   - 单题图片直接进入解题（无额外交互）
   - 附带文字说明时跳过检测
   - 选择单题后正确解答
   - 选择"全部解答"后逐题展示结果

---

## 验收标准

- [ ] `/detect` 端点正确返回 `DetectResponse`（question_count + questions 列表）
- [ ] 单题图片走快速通道，用户体验与现有流程一致
- [ ] 多题图片返回选题按钮组，完整题可点击，不完整题灰显
- [ ] user_hint（text 非空）时跳过多题检测
- [ ] "全部解答"逐题串行调用，每题结果独立展示
- [ ] 超过 5 题时给出分批拍照建议
- [ ] 所有完整题目均不完整时提示重新拍照
- [ ] JSON 解析失败时优雅回退到单题流程
- [ ] 现有单题解题功能无回归
- [ ] 所有验证命令通过零错误

---

## 完成检查清单

- [ ] 所有 12 个任务按顺序完成
- [ ] 每个任务验证立即通过
- [ ] ruff + tsc 零错误
- [ ] 全量 pytest 通过
- [ ] 前端 build 成功
- [ ] 手动测试确认功能有效

---

## 备注

### 架构决策

1. **独立 `/detect` 端点 vs 扩展 `/solve`**：选择独立端点。理由：职责单一、前端可控调用时机、不改变现有 `/solve` 的语义
2. **前端驱动 vs 后端驱动逐题解答**：选择前端驱动。理由：逐题展示结果体验更好、避免长时间等待、每题独立 session 便于追问
3. **检测结果不持久化**：检测结果仅在前端内存中（`pendingImage` + `questionOptions`），不存数据库。理由：检测是临时中间状态，无业务价值需要持久化

### 信心分数：8/10

主要信心来源：
- 核心解题流程完全不改动，通过 `user_hint` 机制自然复用
- 后端新增代码量小（1 个端点 + 1 个服务方法 + 2 个 schema）
- 前端改动集中在 `use-chat.ts`，逻辑清晰

风险点（降分原因）：
- `use-chat.ts` 改动较大，状态管理复杂度增加
- "全部解答"的串行调用在网络不稳定时可能部分失败
