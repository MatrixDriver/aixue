---
description: "功能实施计划: image-preview-ocr"
status: archived
created_at: 2026-03-07T10:20:00
updated_at: 2026-03-07T10:30:00
archived_at: 2026-03-07T10:48:00
related_files:
  - rpiv/requirements/prd-image-preview-ocr.md
---

# 功能：图片上传预览 + OCR 结果展示优化

以下计划应该是完整的，但在开始实施之前，验证文档和代码库模式以及任务合理性非常重要。

特别注意现有工具、类型和模型的命名。从正确的文件导入等。

## 功能描述

用户上传题目图片后，聊天气泡中显示图片缩略图（替代"[图片]"文字），支持点击放大查看完整大图，并提供展开面板展示 OCR 识别文本。纯前端改造，不涉及后端变更。

## 用户故事

作为初高中学生，
我想在聊天气泡中看到上传的题目图片和 OCR 识别结果，
以便确认 AI 正确理解了我的题目，增强对解题结果的信任。

## 问题陈述

当前用户上传图片后，聊天气泡仅显示"[图片]"文字，无法看到上传内容和 OCR 中间结果，导致用户对 AI 解题缺乏信任感。`SolveResponse.question` 中的 OCR 文本虽然已由后端返回，但前端完全忽略了该字段。

## 解决方案陈述

1. 扩展 `Message` 类型，新增 `localImageUrl` 和 `ocrText` 字段
2. 改造 `useChat` hook，发送图片时用 `URL.createObjectURL()` 生成本地预览 URL，收到响应后回填 OCR 文本
3. 改造 `ChatMessage` 组件，含图片消息使用缩略图+展开面板渲染
4. 新建 `ImageLightbox` 组件实现大图查看模态框

## 功能元数据

**功能类型**：增强
**估计复杂度**：中
**主要受影响的系统**：前端 chat 模块
**依赖项**：无新增依赖（复用 lucide-react、Tailwind CSS）

---

## 上下文参考

### 相关代码库文件（实施前必须阅读）

- `frontend/src/lib/types.ts` (第 76-83 行) - `Message` 接口定义，需新增 `localImageUrl` 和 `ocrText` 字段
- `frontend/src/hooks/use-chat.ts` (第 31-99 行) - `sendMessage` 函数，需改造图片消息创建和响应处理逻辑
- `frontend/src/hooks/use-chat.ts` (第 113-122 行) - `newChat` 函数，需添加 Object URL 释放逻辑
- `frontend/src/components/chat/chat-message.tsx` (第 68-141 行) - 消息气泡组件，需集成缩略图+展开面板
- `frontend/src/components/chat/chat-message.tsx` (第 8-13 行) - `ChatMessageProps` 接口，需扩展
- `frontend/src/components/chat/chat-container.tsx` (第 113-120 行) - 消息渲染循环，需传递新字段
- `frontend/src/components/chat/image-upload.tsx` (第 26-39 行) - `handleFile` 函数，了解压缩流程
- `frontend/src/lib/image-utils.ts` - `compressImage` 函数，了解压缩输出

### 要创建的新文件

- `frontend/src/components/chat/image-lightbox.tsx` - 模态框大图查看组件（~50 行）
- `frontend/src/components/chat/ocr-expand-panel.tsx` - 展开/收起面板组件（~70 行）

### 要遵循的模式

**组件模式**（参考 `chat-message.tsx`）：
- "use client" 指令开头
- 使用 `cn()` 工具函数合并 className
- Lucide React 图标（已用 `ImagePlus`, `Camera`, `X`, `Send`, `Loader2`）
- Tailwind CSS 类名，不使用 CSS modules

**LaTeX 渲染**（参考 `chat-message.tsx:20-66`）：
- OCR 文本可能包含 LaTeX 公式，展开面板中应复用 `renderWithLatex()` 函数
- 需要将 `renderWithLatex` 导出或提取为共享函数

**类型定义**（参考 `types.ts`）：
- 可选字段使用 `?` 语法
- 接口名使用 PascalCase

**状态管理**（参考 `use-chat.ts`）：
- 使用 `useState` + `useCallback`
- `setState` 使用函数式更新 `prev => ({ ...prev, ... })`

**错误处理**：
- 图片 `onError` 回调显示占位图
- 加载状态用 `Loader2` 动画（已有模式，见 `chat-container.tsx:130`）

**展开动画**（技术调研结论）：
- 使用 CSS `grid-template-rows: 0fr → 1fr` 过渡
- Tailwind 内联样式 + `transition-all duration-300`

---

## 实施计划

### 阶段 1：基础数据流改造

扩展类型定义和 Hook，为图片预览和 OCR 文本传递建立数据通道。

**任务**：
- 扩展 `Message` 类型
- 改造 `useChat` hook 的 `sendMessage` 和 `newChat`
- ChatMessage 接受新字段

### 阶段 2：缩略图 + 展开面板

创建 OCR 展开面板组件，改造 ChatMessage 渲染含图片的用户消息。

**任务**：
- 创建 `OcrExpandPanel` 组件
- 改造 `ChatMessage` 组件
- 导出 `renderWithLatex` 供展开面板复用

### 阶段 3：Lightbox 模态框

创建独立的图片放大查看组件。

**任务**：
- 创建 `ImageLightbox` 组件
- 在 ChatMessage 中集成 Lightbox

### 阶段 4：集成与容器改造

更新容器组件传递新字段，确保数据贯通。

**任务**：
- 更新 `ChatContainer` 传递新 props
- 处理边缘情况（无图片、纯文本消息兼容性）

---

## 逐步任务

重要：按顺序从上到下执行每个任务。每个任务都是原子的且可独立测试。

### 任务 1: UPDATE `frontend/src/lib/types.ts` — 扩展 Message 接口

- **IMPLEMENT**：在 `Message` 接口（第 76-83 行）新增两个可选字段：
  ```typescript
  localImageUrl?: string;  // 本地 Object URL（blob://）
  ocrText?: string;        // OCR 识别文本（来自 SolveResponse.question）
  ```
- **PATTERN**：与现有 `image_path?: string`（第 81 行）风格一致，使用可选字段
- **VALIDATE**：`cd frontend && npx tsc --noEmit` 确认无类型错误

### 任务 2: UPDATE `frontend/src/hooks/use-chat.ts` — 改造 sendMessage 支持图片预览和 OCR 回填

- **IMPLEMENT**：
  1. 在 `sendMessage` 函数中（第 32-98 行），当 `image` 不为 null 时：
     - 调用 `URL.createObjectURL(image)` 生成预览 URL
     - 写入 `userMsg.localImageUrl`
  2. 收到 `SolveResponse` 后（第 64-78 行 else 分支的新题目流程）：
     - 将 `response.question` 回填到已添加的用户消息的 `ocrText` 字段
     - 使用 `setState` 更新 messages 数组中最后一条用户消息
  3. 在添加 AI 消息的 setState 中，同时更新用户消息的 ocrText：
     ```typescript
     setState((prev) => ({
       ...prev,
       messages: prev.messages.map((msg) =>
         msg.id === userMsg.id
           ? { ...msg, ocrText: response.question }
           : msg
       ).concat([aiMsg]),
       sessionId: newSessionId,
       loading: false,
     }));
     ```
- **IMPORTS**：无新增导入
- **GOTCHA**：`response.question` 可能为空字符串（OCR 失败），这种情况 ocrText 仍然赋值，展开面板会显示"未能识别"提示
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 3: UPDATE `frontend/src/hooks/use-chat.ts` — newChat 释放 Object URL

- **IMPLEMENT**：在 `newChat` 函数（第 113-122 行）中，清空消息前遍历释放所有 Object URL：
  ```typescript
  const newChat = useCallback(() => {
    // 释放所有本地图片 Object URL
    state.messages.forEach((msg) => {
      if (msg.localImageUrl) {
        URL.revokeObjectURL(msg.localImageUrl);
      }
    });
    setState({
      messages: [],
      sessionId: null,
      mode: state.mode,
      subject: "",
      loading: false,
      error: null,
    });
  }, [state.mode, state.messages]);
  ```
- **GOTCHA**：`useCallback` 的依赖数组需要加上 `state.messages`，否则 closure 中的 messages 是旧值
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 4: UPDATE `frontend/src/components/chat/chat-message.tsx` — 导出 renderWithLatex

- **IMPLEMENT**：将 `renderWithLatex` 函数从模块私有改为命名导出：
  ```typescript
  // 改前：function renderWithLatex(text: string): string {
  // 改后：
  export function renderWithLatex(text: string): string {
  ```
- **PATTERN**：保持函数签名和实现不变，仅添加 `export`
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 5: CREATE `frontend/src/components/chat/ocr-expand-panel.tsx` — OCR 展开/收起面板

- **IMPLEMENT**：创建展开面板组件，包含：
  1. 展开/收起按钮（"查看识别结果 ▼" / "收起 ▲"）
  2. 展开区域：上方图片（较大尺寸）+ 下方 OCR 文本
  3. CSS grid 过渡动画
  4. 三种状态：加载中（脉冲动画）、有文本（渲染含 LaTeX）、失败/空（提示文字）

  ```typescript
  "use client";

  import { useState } from "react";
  import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
  import { cn } from "@/lib/utils";
  import { renderWithLatex } from "./chat-message";

  interface OcrExpandPanelProps {
    imageUrl?: string;      // 图片 URL（缩略图下方的大图）
    ocrText?: string;       // OCR 文本
    loading?: boolean;      // 是否加载中
  }

  export default function OcrExpandPanel({ imageUrl, ocrText, loading }: OcrExpandPanelProps) {
    const [expanded, setExpanded] = useState(false);

    // 不需要展开按钮的情况：无 OCR 文本且不在加载中
    if (!loading && ocrText === undefined) return null;

    return (
      <div className="mt-1.5">
        {/* 展开/收起按钮 */}
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-indigo-500 transition-colors"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {expanded ? "收起" : "查看识别结果"}
        </button>

        {/* 展开区域 - grid 动画 */}
        <div
          className={cn(
            "grid transition-all duration-300 ease-in-out",
            expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          )}
        >
          <div className="overflow-hidden">
            <div className="mt-2 space-y-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
              {/* 大图 */}
              {imageUrl && (
                <img
                  src={imageUrl}
                  alt="题目图片"
                  className="max-w-full max-h-80 rounded border border-gray-200"
                />
              )}

              {/* OCR 文本 */}
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Loader2 size={14} className="animate-spin" />
                  正在识别...
                </div>
              ) : ocrText ? (
                <div className="border-l-2 border-indigo-300 pl-3">
                  <p className="mb-1 text-xs font-medium text-gray-500">识别结果</p>
                  <div
                    className="prose prose-sm max-w-none text-sm text-gray-700"
                    dangerouslySetInnerHTML={{ __html: renderWithLatex(ocrText) }}
                  />
                </div>
              ) : (
                <p className="text-sm text-gray-400">未能识别图片中的文字</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
  ```
- **IMPORTS**：`renderWithLatex` 从 `./chat-message` 导入
- **PATTERN**：组件风格与 `ChatMessage` 一致，使用 `cn()` + Tailwind
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 6: CREATE `frontend/src/components/chat/image-lightbox.tsx` — Lightbox 模态框

- **IMPLEMENT**：创建模态框组件，使用 `createPortal` 渲染到 `document.body`：
  ```typescript
  "use client";

  import { useEffect, useCallback } from "react";
  import { createPortal } from "react-dom";
  import { X } from "lucide-react";

  interface ImageLightboxProps {
    src: string;
    alt?: string;
    onClose: () => void;
  }

  export default function ImageLightbox({ src, alt = "图片", onClose }: ImageLightboxProps) {
    const handleKeyDown = useCallback(
      (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      },
      [onClose]
    );

    useEffect(() => {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "";
      };
    }, [handleKeyDown]);

    return createPortal(
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
        onClick={onClose}
        role="dialog"
        aria-modal="true"
      >
        <button
          className="absolute right-4 top-4 rounded-full bg-black/40 p-2 text-white hover:bg-black/60 transition-colors"
          onClick={onClose}
        >
          <X size={20} />
        </button>
        <img
          src={src}
          alt={alt}
          className="max-h-[90vh] max-w-[90vw] object-contain"
          onClick={(e) => e.stopPropagation()}
        />
      </div>,
      document.body
    );
  }
  ```
- **IMPORTS**：`createPortal` from react-dom, `X` from lucide-react
- **PATTERN**：ESC 键关闭（`useEffect` + `keydown`）、遮罩点击关闭（`onClick`）、图片点击阻止冒泡
- **GOTCHA**：`document.body.style.overflow = "hidden"` 防止背景滚动，cleanup 中恢复
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 7: UPDATE `frontend/src/components/chat/chat-message.tsx` — 集成缩略图+展开面板+Lightbox

- **IMPLEMENT**：
  1. 扩展 `ChatMessageProps` 接口，新增字段：
     ```typescript
     interface ChatMessageProps {
       role: MessageRole;
       content: string;
       imagePath?: string;
       localImageUrl?: string;    // 新增
       ocrText?: string;          // 新增
       ocrLoading?: boolean;      // 新增
       timestamp?: string;
     }
     ```
  2. 在组件内新增 Lightbox 状态：
     ```typescript
     const [lightboxOpen, setLightboxOpen] = useState(false);
     ```
  3. 确定实际使用的图片 URL（优先本地 blob，降级到服务端路径）：
     ```typescript
     const displayImageUrl = localImageUrl || imagePath;
     ```
  4. 替换现有图片渲染区域（第 102-109 行），改为缩略图+展开面板：
     ```tsx
     {displayImageUrl && (
       <div className="space-y-1">
         {/* 缩略图 */}
         <img
           src={displayImageUrl}
           alt="上传的题目"
           className="w-48 sm:w-60 max-h-72 rounded-lg border border-gray-200 object-cover cursor-pointer hover:opacity-90 transition-opacity"
           onClick={() => setLightboxOpen(true)}
           onError={(e) => {
             (e.target as HTMLImageElement).src = "";
             (e.target as HTMLImageElement).alt = "图片已过期";
             (e.target as HTMLImageElement).className = "w-48 sm:w-60 h-32 rounded-lg border border-gray-200 bg-gray-100 flex items-center justify-center";
           }}
         />

         {/* OCR 展开面板 */}
         {isUser && (
           <OcrExpandPanel
             imageUrl={displayImageUrl}
             ocrText={ocrText}
             loading={ocrLoading}
           />
         )}

         {/* Lightbox */}
         {lightboxOpen && displayImageUrl && (
           <ImageLightbox
             src={displayImageUrl}
             alt="题目大图"
             onClose={() => setLightboxOpen(false)}
           />
         )}
       </div>
     )}
     ```
  5. 当 content 为 "[图片]" 且有 displayImageUrl 时，不显示文字气泡（避免重复）：
     ```typescript
     const showTextBubble = !(content === "[图片]" && displayImageUrl);
     ```
     然后将文字内容的 div 用 `{showTextBubble && (...)}` 包裹
- **IMPORTS**：
  ```typescript
  import { useState, useMemo } from "react";
  import OcrExpandPanel from "./ocr-expand-panel";
  import ImageLightbox from "./image-lightbox";
  ```
- **PATTERN**：缩略图 `w-48 sm:w-60`（192px/240px），与调研报告建议一致
- **GOTCHA**：
  - `onError` 处理 blob URL 失效（页面刷新后）的情况。注意：直接修改 DOM 属性不是 React 最佳实践，但对于降级场景足够简单。更优方案是用 state 控制，但避免过度工程化
  - 仅用户消息（`isUser`）显示 OCR 展开面板，AI 消息不需要
  - 图片加载失败的优雅降级：考虑使用一个 `imgError` state 来控制占位图渲染，代替直接修改 DOM
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 8: UPDATE `frontend/src/components/chat/chat-container.tsx` — 传递新字段

- **IMPLEMENT**：在消息渲染循环（第 113-120 行）中，将新字段传递给 `ChatMessage`：
  ```tsx
  {messages.map((msg) => (
    <ChatMessage
      key={msg.id}
      role={msg.role}
      content={msg.content}
      imagePath={msg.image_path}
      localImageUrl={msg.localImageUrl}
      ocrText={msg.ocrText}
      ocrLoading={msg.role === "user" && !!msg.localImageUrl && msg.ocrText === undefined && loading}
      timestamp={msg.created_at}
    />
  ))}
  ```
- **PATTERN**：`ocrLoading` 的判定逻辑：是用户消息 + 有本地图片 + 还没收到 OCR 文本 + 全局 loading 状态为 true
- **GOTCHA**：`msg.ocrText === undefined` 区分"还没收到"和"OCR 返回空字符串"两种情况。空字符串表示 OCR 失败，展开面板显示"未能识别"
- **VALIDATE**：`cd frontend && npx tsc --noEmit`

### 任务 9: 手动验证全流程

- **VALIDATE**：
  1. `cd frontend && npm run build` — 确认构建无错误
  2. 启动开发服务器，测试以下场景：
     - 上传图片 → 缩略图立即显示
     - AI 回复后 → 展开按钮出现
     - 点击"查看识别结果" → 面板展开，显示 OCR 文本
     - 点击缩略图 → Lightbox 弹出
     - Lightbox 关闭（遮罩点击 / X 按钮 / ESC 键）
     - 纯文本消息 → 正常渲染，无多余元素
     - "新对话"按钮 → 旧消息清空

---

## 测试策略

### 单元测试

由于本功能为纯 UI 组件，且项目前端当前没有测试框架配置，单元测试暂不纳入本期。重点通过手动验证和类型检查确保正确性。

### 集成测试

不适用（纯前端 UI 改动，不涉及 API 变更）。

### 边缘情况

1. **页面刷新后** — blob URL 失效，缩略图区域应显示占位图或错误状态
2. **纯文本消息** — 无图片字段，ChatMessage 应与改造前行为完全一致
3. **OCR 返回空字符串** — 展开面板显示"未能识别图片中的文字"
4. **连续发送多张图片** — 每条消息独立持有 blob URL，互不影响
5. **追问模式** — `followUp` 为 true 时不涉及图片上传，不受影响
6. **历史会话加载** — `loadSession` 传入的消息没有 `localImageUrl`，应走 `image_path` 降级路径

---

## 验证命令

### 级别 1：语法和样式

```bash
cd frontend && npx tsc --noEmit
```

### 级别 2：构建验证

```bash
cd frontend && npm run build
```

### 级别 3：手动验证

1. 启动前后端开发服务器
2. 登录测试账号（test / test123）
3. 上传一张题目图片：
   - 确认缩略图立即显示（零延迟）
   - 确认"[图片]"文字不再显示
4. 等待 AI 回复后：
   - 确认"查看识别结果"按钮出现
   - 点击展开，确认 OCR 文本正确显示
   - 再次点击收起，确认动画流畅
5. 点击缩略图：
   - 确认 Lightbox 弹出，显示大图
   - 分别测试三种关闭方式（遮罩点击 / X 按钮 / ESC）
6. 发送纯文本消息：
   - 确认渲染正常，无多余 UI 元素
7. 点击"新对话"：
   - 确认消息清空
8. 刷新页面：
   - 确认图片区域优雅降级（占位图或隐藏）

---

## 验收标准

- [ ] 图片消息气泡显示缩略图，不再显示"[图片]"文字
- [ ] 点击缩略图弹出 Lightbox，支持三种关闭方式
- [ ] 展开面板正确显示 OCR 识别文本（含 LaTeX 渲染）
- [ ] 展开/收起动画流畅（grid-template-rows 过渡）
- [ ] 图片上传后缩略图零延迟显示（本地 blob URL）
- [ ] OCR 加载中显示动画，完成后替换为文本
- [ ] OCR 失败时显示"未能识别图片中的文字"
- [ ] 纯文本消息渲染不受影响
- [ ] `npm run build` 通过，无类型错误
- [ ] 新对话时释放 Object URL（无内存泄漏）
- [ ] 页面刷新后图片区域优雅降级

---

## 完成检查清单

- [ ] 所有任务按顺序完成
- [ ] 每个任务验证立即通过
- [ ] `npx tsc --noEmit` 无错误
- [ ] `npm run build` 成功
- [ ] 手动测试确认功能有效
- [ ] 所有验收标准均满足
- [ ] 代码遵循项目约定（Tailwind、lucide-react、cn()）

---

## 备注

- **无新增依赖**：所有功能使用 React 内置 API + Tailwind CSS + lucide-react 实现
- **renderWithLatex 导出**：任务 4 将其改为 export，供 OcrExpandPanel 复用。如果后续有更多地方需要该函数，可考虑迁移到 `lib/utils.ts`，但本期保持最小改动
- **图片降级方案简化决策**：对于 blob URL 失效的情况，选择了简单的 `onError` 处理而非 state 驱动的方案，因为这是已知的临时限制（后续 R2 持久化会彻底解决）
- **改动文件清单**：共改动 4 个现有文件 + 新建 2 个文件，预计约 200 行代码变更
  - UPDATE: `types.ts`, `use-chat.ts`, `chat-message.tsx`, `chat-container.tsx`
  - CREATE: `ocr-expand-panel.tsx`, `image-lightbox.tsx`

**信心分数**：8/10 — 改动范围清晰，技术方案成熟，唯一不确定因素是 CSS grid 过渡动画在不同浏览器的表现可能需要微调。
