---
description: "技术调研: 图片预览+OCR结果展示"
status: archived
created_at: 2026-03-07T10:10:00
updated_at: 2026-03-07T10:15:00
archived_at: 2026-03-07T10:48:00
---

# 技术调研：图片上传预览 + OCR 结果展示优化

## 1. 现有代码结构分析

### 1.1 关键文件清单

| 文件 | 作用 | 改动关联度 |
|------|------|-----------|
| `frontend/src/components/chat/chat-message.tsx` | 消息气泡渲染，当前用 `<img src={imagePath}>` 展示图片 | **核心改动** |
| `frontend/src/components/chat/image-upload.tsx` | 上传前预览 + 压缩，使用 FileReader base64 | 需提供预览 URL |
| `frontend/src/components/chat/chat-container.tsx` | 消息列表容器，传递 `msg.image_path` 给 ChatMessage | 需传递新字段 |
| `frontend/src/components/chat/chat-input.tsx` | 输入框 + 图片上传入口 | 小改动 |
| `frontend/src/hooks/use-chat.ts` | 解题状态管理，构造用户消息和 AI 消息 | **核心改动** |
| `frontend/src/lib/types.ts` | Message/SolveResponse 类型定义 | 需扩展字段 |
| `frontend/src/lib/image-utils.ts` | 图片压缩（canvas + WebP/JPEG） | 可复用，无需改动 |
| `frontend/src/lib/api.ts` | solveQuestion API 调用 | 无需改动 |

### 1.2 当前数据流

```
用户选图 → ImageUpload.handleFile() → compressImage() → File 对象
         → FileReader.readAsDataURL() → base64 预览（仅上传前）

发送 → useChat.sendMessage(text, image) → 创建 userMsg（content="[图片]", 无图片数据）
     → solveQuestion(FormData) → SolveResponse { question, content, ... }
     → 创建 aiMsg（content=response.content）
```

**核心问题**：
1. `userMsg` 中 `content` 写死为 `"[图片]"`，没有保留图片预览数据
2. `SolveResponse.question`（OCR 结果）被完全忽略，未传递给前端展示
3. `image_path` 字段目前只有历史记录加载时后端返回的服务端路径，实时对话中为 undefined

### 1.3 后端 API 已有能力

`SolveResponse` 已包含 `question: string` 字段（OCR 识别文本），前端只需在收到响应后将其关联到用户消息即可展示，**无需新增后端接口**。

## 2. 技术方案调研

### 2.1 图片预览方案对比

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **Object URL**（`URL.createObjectURL(file)`） | 零拷贝、内存高效、同步创建 | 需手动 `revokeObjectURL` 释放；页面刷新后失效 | **推荐** |
| **Base64 Data URL**（`FileReader.readAsDataURL`） | 可序列化、持久化方便 | 内存占用大（比原文件大 33%）；大图性能差 | 不推荐 |
| **Canvas 缩略图** | 可精确控制尺寸 | 额外计算开销；已有 compressImage 做过缩放 | 过度 |

**结论**：使用 `URL.createObjectURL(compressedFile)` 创建预览 URL。在 `useChat` 中将其附加到 userMsg，组件卸载或新对话时调用 `URL.revokeObjectURL()` 释放。

**生命周期管理**：
- 创建时机：`sendMessage` 中发送图片时立即创建
- 存储位置：扩展 `Message` 类型新增 `localImageUrl?: string` 字段
- 释放时机：`newChat()` 清空消息时遍历释放；组件 unmount 时释放
- 刷新降级：Object URL 失效后，`<img>` 的 `onError` 回调显示占位图

### 2.2 Lightbox/图片放大方案

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **自实现 Modal** | 零依赖、完全可控、代码量小（~60行） | 需自行处理 ESC/遮罩关闭 | **推荐** |
| **yet-another-react-lightbox** | 功能丰富（缩放、滑动） | 新增依赖；功能远超需求 | 过度 |
| **react-medium-image-zoom** | 轻量、Medium 式放大 | 交互模式不匹配（非 modal） | 不匹配 |
| **HTML `<dialog>` 元素** | 浏览器原生、自动处理 ESC 和焦点陷阱 | React 19 兼容性好 | **备选** |

**结论**：自实现简单 Modal 组件（~60 行），使用 `<dialog>` 元素或 div + portal。需求很简单（显示大图 + 关闭），不值得引入第三方库。

**实现要点**：
- 使用 React `createPortal` 渲染到 `document.body`
- 遮罩层 `onClick` 关闭 + `onKeyDown` ESC 关闭
- 图片 `max-width: 90vw; max-height: 90vh; object-fit: contain`
- 右上角关闭按钮（X icon，复用 lucide-react 的 X）
- 无图片数据时不渲染点击区域

### 2.3 展开/收起动画方案

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **CSS `grid-template-rows` 过渡** | 纯 CSS、不需要 JS 计算高度、支持动态内容 | 需要 grid 包装 | **推荐** |
| **CSS `max-height` 过渡** | 简单 | 需要猜测 max-height 值；过渡不自然 | 不推荐 |
| **framer-motion** | 功能强大 | 新增 ~30KB 依赖；杀鸡用牛刀 | 过度 |
| **CSS `height: auto` + `calc-size()`** | 最简洁 | 浏览器支持不足（Chrome 129+） | 未来方案 |

**结论**：使用 CSS `grid-template-rows: 0fr → 1fr` 过渡，这是目前纯 CSS 实现 `height: auto` 动画的最佳方案。

```css
/* 收起 */
.expand-container { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 0.3s ease; }
.expand-container.open { grid-template-rows: 1fr; }
.expand-container > div { overflow: hidden; }
```

### 2.4 Next.js Image 组件适用性

项目当前**未使用** `next/image`，且图片来源为用户上传的 Object URL（blob:// 协议），`next/image` 需要配置 `remotePatterns` 或 `unoptimized`，反而增加复杂度。**建议继续使用原生 `<img>` 标签**，因为：
1. 图片已经通过 `compressImage()` 做过尺寸和格式优化
2. Object URL 是本地 blob，不走 Next.js 图片优化管线
3. 未来接入 R2 持久化后再考虑 `next/image`

### 2.5 状态管理方案

当前 `useChat` hook 使用 `useState` 管理所有状态，结构清晰，无需引入外部状态库。扩展方案：

1. **扩展 Message 类型**：新增 `localImageUrl?: string`（Object URL）和 `ocrText?: string`（OCR 结果）
2. **sendMessage 改造**：
   - 发送时：`URL.createObjectURL(image)` → 写入 `userMsg.localImageUrl`
   - 收到响应时：将 `response.question` 回填到对应用户消息的 `ocrText` 字段
3. **newChat 清理**：遍历 messages，释放所有 `localImageUrl`

## 3. 组件设计建议

### 3.1 新增组件

| 组件 | 职责 | 预估代码量 |
|------|------|-----------|
| `ImageLightbox` | 模态框大图查看 | ~50 行 |
| `OcrExpandPanel` | 展开/收起面板（图片 + OCR 文本） | ~70 行 |

### 3.2 改造组件

| 组件 | 改动内容 |
|------|----------|
| `ChatMessage` | 缩略图替代文字 + 点击放大 + 展开按钮 + OCR 面板 |
| `useChat` | sendMessage 中创建 Object URL + 回填 ocrText + newChat 释放资源 |
| `types.ts` | Message 增加 `localImageUrl?` 和 `ocrText?` |
| `chat-container.tsx` | 传递新字段给 ChatMessage |

### 3.3 ChatMessage 改造后结构

```
<div> 消息气泡
  {有图片 ?
    <div> 缩略图区域
      <img 缩略图 onClick={打开lightbox} />    ← 200-240px 宽
      <button "查看识别结果 ▼/▲" />
      <OcrExpandPanel open={expanded}>          ← grid 动画展开
        <img 大图 />                            ← 展开区域内的图片
        <div OCR文本 / 加载中 / 识别失败 />
      </OcrExpandPanel>
    </div>
  : null}
  <div 文字内容 />                              ← 原有逻辑不变
</div>
<ImageLightbox />                               ← portal 到 body
```

## 4. 风险与注意事项

1. **Object URL 内存泄漏**：必须在 newChat / unmount 时调用 `URL.revokeObjectURL()`。建议在 useChat 中用 `useEffect` cleanup
2. **刷新后图片丢失**：Object URL 在刷新后失效，需要 `onError` 降级显示占位图。这是已知约束，R2 持久化是后续功能
3. **历史记录页面**：`history/page.tsx` 也使用 `ChatMessage`，需确保 `localImageUrl` 为空时走 `image_path`（服务端路径）的逻辑，保持向后兼容
4. **移动端适配**：缩略图宽度建议用 `w-48 sm:w-60`（192px/240px），展开面板最大宽度跟随气泡
5. **OCR 文本可能含 LaTeX**：展开面板中的 OCR 文本应复用 `renderWithLatex()` 渲染

## 5. 技术结论

| 决策点 | 结论 |
|--------|------|
| 图片预览方案 | Object URL（`createObjectURL`） |
| Lightbox 方案 | 自实现 Modal（~50 行，lucide-react X icon） |
| 展开动画 | CSS `grid-template-rows` 过渡 |
| 第三方依赖 | **不需要新增任何依赖** |
| Next.js Image | 不使用，继续用原生 `<img>` |
| 状态管理 | 扩展现有 useChat hook |
| 后端改动 | **无需后端改动**，`SolveResponse.question` 已有 OCR 文本 |

**总改动量预估**：约 5 个文件，~200 行新增/修改代码，纯前端改动。
