---
description: "测试规格: image-preview-ocr"
status: archived
created_at: 2026-03-07T10:20:00
updated_at: 2026-03-07T10:20:00
archived_at: 2026-03-07T10:48:00
---

# 测试规格：图片上传预览 + OCR 结果展示优化

## 1. 类型扩展测试

### TS-001: Message 接口新增 imageUrl 字段
- **优先级**: P0
- **前提**: Message 接口已扩展
- **步骤**: 创建包含 `imageUrl` 字段的 Message 对象
- **预期**: TypeScript 编译通过，`imageUrl` 为可选 `string` 类型
- **验证方式**: `npm run build` 编译检查

### TS-002: Message 接口新增 ocrText 字段
- **优先级**: P0
- **前提**: Message 接口已扩展
- **步骤**: 创建包含 `ocrText` 字段的 Message 对象
- **预期**: TypeScript 编译通过，`ocrText` 为可选 `string` 类型
- **验证方式**: `npm run build` 编译检查

### TS-003: 向后兼容 — 无 imageUrl/ocrText 的消息仍可正常使用
- **优先级**: P0
- **步骤**: 创建不含 `imageUrl` 和 `ocrText` 的 Message 对象
- **预期**: TypeScript 编译通过，不报类型错误

## 2. ImageMessageBubble 组件测试

### IMB-001: 缩略图正常渲染
- **优先级**: P0
- **前提**: 组件接收有效的 `imageUrl`（blob URL）
- **步骤**: 渲染 ImageMessageBubble，传入 imageUrl
- **预期**:
  - 渲染 `<img>` 元素，`src` 为传入的 imageUrl
  - 图片 alt 文本为"上传的题目"或类似描述
  - 图片宽度在 200-240px 范围内
  - 图片最大高度 300px
  - 应用 rounded-lg 圆角

### IMB-002: 缩略图加载失败显示占位图
- **优先级**: P0
- **前提**: imageUrl 对应的图片资源不可用
- **步骤**: 渲染 ImageMessageBubble，触发图片 `onError` 事件
- **预期**:
  - 显示灰色占位图（或占位图标）
  - 显示"图片加载失败"文字

### IMB-003: 无 imageUrl 时显示占位图
- **优先级**: P0
- **前提**: imageUrl 为 undefined 或空字符串
- **步骤**: 渲染 ImageMessageBubble，不传 imageUrl
- **预期**: 显示占位图 + "图片已过期"文字（页面刷新场景）

### IMB-004: 展开按钮初始显示"查看识别结果"
- **优先级**: P0
- **前提**: 组件已渲染
- **步骤**: 查找展开按钮
- **预期**: 按钮文字包含"查看识别结果"和向下箭头（▼）

### IMB-005: 点击展开按钮显示 OCR 文本
- **优先级**: P0
- **前提**: 组件接收有效 `ocrText`
- **步骤**: 点击展开按钮
- **预期**:
  - 展开面板可见
  - OCR 文本正确显示
  - 按钮文字变为"收起"+ 向上箭头（▲）

### IMB-006: 再次点击收起面板
- **优先级**: P0
- **前提**: 面板已展开
- **步骤**: 再次点击展开/收起按钮
- **预期**:
  - 面板收起隐藏
  - 按钮文字恢复为"查看识别结果 ▼"

### IMB-007: OCR 文本为空或 undefined 时显示提示
- **优先级**: P0
- **前提**: ocrText 为空字符串或 undefined
- **步骤**: 展开面板
- **预期**: 面板内显示"未能识别图片中的文字"

### IMB-008: OCR 加载中状态
- **优先级**: P1
- **前提**: ocrText 为 undefined 且 loading 为 true
- **步骤**: 渲染带 loading 状态的组件，展开面板
- **预期**: OCR 文本区域显示脉冲动画/骨架屏

### IMB-009: 展开面板布局 — 上图下文
- **优先级**: P1
- **前提**: 面板已展开，有 imageUrl 和 ocrText
- **步骤**: 检查展开面板内部布局
- **预期**:
  - 上方显示较大尺寸图片（最大宽度 400px）
  - 下方显示 OCR 文本
  - OCR 文本区域有左边框样式

### IMB-010: 缩略图点击触发 Lightbox
- **优先级**: P1
- **前提**: 组件接收有效 imageUrl
- **步骤**: 点击缩略图图片
- **预期**: 触发 onImageClick 回调（或打开 Lightbox）

### IMB-011: 无图片时缩略图不可点击
- **优先级**: P1
- **前提**: imageUrl 为空
- **步骤**: 尝试点击占位图区域
- **预期**: 不触发 Lightbox，cursor 不是 pointer

### IMB-012: OCR 文本以纯文本渲染，不使用 dangerouslySetInnerHTML
- **优先级**: P0（安全相关）
- **前提**: ocrText 包含 HTML 标签（如 `<script>alert(1)</script>`）
- **步骤**: 展开面板查看渲染结果
- **预期**: HTML 标签以纯文本显示，不被解析执行

## 3. ImageLightbox 组件测试

### IL-001: Lightbox 正常显示大图
- **优先级**: P1
- **前提**: Lightbox 以有效 imageUrl 打开
- **步骤**: 触发 Lightbox 打开
- **预期**:
  - 半透明遮罩层（bg-black/60）覆盖全屏
  - 图片以 object-contain 方式展示
  - 最大宽度 90vw，最大高度 90vh
  - 右上角显示关闭按钮

### IL-002: 点击遮罩层关闭 Lightbox
- **优先级**: P1
- **步骤**: 点击遮罩层（图片外部区域）
- **预期**: Lightbox 关闭，遮罩层消失

### IL-003: 点击关闭按钮关闭 Lightbox
- **优先级**: P1
- **步骤**: 点击右上角关闭按钮
- **预期**: Lightbox 关闭

### IL-004: ESC 键关闭 Lightbox
- **优先级**: P1
- **步骤**: 按下 ESC 键
- **预期**: Lightbox 关闭

### IL-005: 点击图片本身不关闭 Lightbox
- **优先级**: P1
- **步骤**: 点击 Lightbox 中的图片
- **预期**: Lightbox 保持打开状态

### IL-006: Lightbox 无障碍属性
- **优先级**: P2
- **步骤**: 检查 Lightbox DOM 属性
- **预期**:
  - 具有 `role="dialog"` 属性
  - 具有 `aria-modal="true"` 属性

## 4. use-chat Hook 改造测试

### UC-001: 发送图片消息时生成 blob URL
- **优先级**: P0
- **前提**: 用户通过 image-upload 选择了图片文件
- **步骤**: 调用 sendMessage(text, imageFile)
- **预期**: 用户消息对象的 `imageUrl` 字段包含以 `blob:` 开头的 URL

### UC-002: 发送纯文本消息时 imageUrl 为 undefined
- **优先级**: P0
- **步骤**: 调用 sendMessage("问题文本", null)
- **预期**: 用户消息对象的 `imageUrl` 为 undefined

### UC-003: 收到 SolveResponse 后回填 ocrText
- **优先级**: P0
- **前提**: Mock API 返回 `SolveResponse` 带 `question: "已知 f(x)=x^2"`
- **步骤**: 发送图片消息并等待响应
- **预期**: 用户消息的 `ocrText` 字段被更新为 "已知 f(x)=x^2"

### UC-004: API 失败时 ocrText 保持 undefined
- **优先级**: P0
- **前提**: Mock API 返回错误
- **步骤**: 发送图片消息，API 抛出异常
- **预期**: 用户消息 `ocrText` 保持 undefined，error 状态被设置

### UC-005: 追问模式不影响 imageUrl
- **优先级**: P1
- **前提**: 已有 sessionId（追问模式）
- **步骤**: 发送纯文本追问消息
- **预期**: 追问消息不包含 imageUrl

## 5. ChatMessage 集成测试

### CM-001: 含图片的用户消息使用 ImageMessageBubble 渲染
- **优先级**: P0
- **步骤**: 渲染 ChatMessage，传入含 imageUrl 的消息
- **预期**: 渲染 ImageMessageBubble 而非纯文本"[图片]"

### CM-002: 纯文本用户消息不受影响
- **优先级**: P0
- **步骤**: 渲染 ChatMessage，传入不含 imageUrl 的消息
- **预期**: 正常渲染文本内容，不出现图片相关 UI

### CM-003: AI 回复消息不显示图片组件
- **优先级**: P0
- **步骤**: 渲染 role="assistant" 的消息
- **预期**: 正常渲染文本+LaTeX，不出现 ImageMessageBubble

### CM-004: 多条图片消息独立管理展开状态
- **优先级**: P1
- **步骤**: 渲染多条含图片的消息，分别展开/收起
- **预期**: 每条消息的展开/收起状态独立，互不影响

## 6. 端到端流程测试（手动）

### E2E-001: 完整上传流程
- **优先级**: P0
- **方式**: 手动测试
- **步骤**:
  1. 打开解题页面
  2. 点击上传图片或拍照
  3. 选择一张题目图片
  4. 确认发送
  5. 观察聊天气泡
- **预期**:
  - 气泡中立即显示缩略图（非"[图片]"文字）
  - OCR 区域显示加载动画
  - AI 回复后展开面板可查看 OCR 文本

### E2E-002: Lightbox 交互
- **优先级**: P1
- **方式**: 手动测试
- **步骤**:
  1. 完成 E2E-001
  2. 点击缩略图
  3. 验证大图显示
  4. 分别用遮罩层点击、关闭按钮、ESC 键关闭
- **预期**: 三种关闭方式均正常工作

### E2E-003: 页面刷新后优雅降级
- **优先级**: P2
- **方式**: 手动测试
- **步骤**:
  1. 完成 E2E-001
  2. 刷新页面
  3. 查看之前的图片消息
- **预期**: 图片区域显示占位图，非空白或错误

### E2E-004: 移动端响应式
- **优先级**: P2
- **方式**: 手动测试（Chrome DevTools 移动设备模拟）
- **步骤**: 在 375px 和 768px 宽度下执行 E2E-001
- **预期**: 缩略图和展开面板自适应屏幕宽度，不溢出

## 7. 后端回归测试

### BE-001: 现有 API 测试不被破坏
- **优先级**: P0
- **方式**: `uv run pytest`
- **预期**: 所有现有后端测试通过

### BE-002: SolveResponse 结构未变更
- **优先级**: P0
- **方式**: 检查后端代码，确认无 API 变更
- **预期**: 后端代码零修改

## 8. 安全测试

### SEC-001: OCR 文本 XSS 防护
- **优先级**: P0
- **步骤**: 模拟 ocrText 包含 `<script>alert('xss')</script>`
- **预期**: 文本以纯文本显示，脚本不执行

### SEC-002: blob URL 不暴露文件系统路径
- **优先级**: P1
- **步骤**: 检查生成的 blob URL 格式
- **预期**: URL 格式为 `blob:http://...` 标准格式，不含本地文件路径

## 9. Object URL 内存管理测试

### MEM-001: 组件卸载时 revoke blob URL
- **优先级**: P1
- **步骤**: 渲染组件后卸载，检查是否调用了 `URL.revokeObjectURL`
- **预期**: blob URL 被正确清理，避免内存泄漏

### MEM-002: 新对话清除旧 blob URL
- **优先级**: P1
- **步骤**: 发送图片消息后调用 newChat()
- **预期**: 旧消息的 blob URL 被 revoke
