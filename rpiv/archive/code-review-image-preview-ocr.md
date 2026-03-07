---
description: "代码审查报告: image-preview-ocr"
status: archived
created_at: 2026-03-07T10:50:00
updated_at: 2026-03-07T10:55:00
archived_at: 2026-03-07T10:48:00
---

# 代码审查报告

**统计：**

- 修改的文件：4（types.ts, use-chat.ts, chat-message.tsx, chat-container.tsx）
- 添加的文件：2（image-lightbox.tsx, ocr-expand-panel.tsx）
- 删除的文件：0
- 新增行：约 150
- 删除行：约 20

## 发现的问题

```
severity: high
status: fixed
file: frontend/src/components/chat/chat-message.tsx
line: 25-31, 35
issue: OCR 文本使用 dangerouslySetInnerHTML 渲染，存在 XSS 风险
detail: 已修复。Dev-1 在 renderWithLatex 函数入口处新增 escapeHtml() 函数（第 25-31 行），在处理 LaTeX 之前先转义 HTML 特殊字符（&, <, >, "）。修复完整且符合建议方案。
suggestion: 已按建议修复，无需进一步操作。
```

```
severity: medium
status: open
file: frontend/src/components/chat/chat-message.tsx
line: 133-136
issue: 图片 onError 直接修改 DOM 属性而非通过 React state
detail: onError 回调中直接修改 DOM 元素属性（src, alt, className），绕过了 React 的虚拟 DOM 管理。如果组件因其他原因重新渲染，React 会用原始值覆盖手动设置的 DOM 属性，导致错误状态被重置。虽然实施计划中已明确了这是简化方案（后续 R2 持久化会解决），但在当前版本中仍可能产生闪烁。
suggestion: 使用 useState 管理 imgError 状态。示例：const [imgError, setImgError] = useState(false); onError={() => setImgError(true)}; imgError 时渲染占位组件。改动量约 5 行。
```

```
severity: medium
status: open
file: frontend/src/hooks/use-chat.ts
line: 135
issue: newChat 的 useCallback 依赖数组包含 state.messages 导致不必要的函数重建
detail: state.messages 在每次发送/接收消息时都会变化，导致 newChat 函数在每次消息更新后都被重建。如果下游组件依赖 newChat 的引用稳定性（如 useEffect 依赖），可能触发不必要的副作用。
suggestion: 改用 ref 存储 messages 引用，或在 newChat 内部使用 setState(prev => ...) 函数式更新来访问最新 messages，避免将 state.messages 放入依赖数组。例如：setState(prev => { prev.messages.forEach(msg => { if (msg.localImageUrl) URL.revokeObjectURL(msg.localImageUrl); }); return { ... }; });
```

```
severity: low
status: open
file: frontend/src/components/chat/image-lightbox.tsx
line: 37-42
issue: 关闭按钮的 onClick 会同时触发遮罩层的 onClick，导致 onClose 被调用两次
detail: 关闭按钮位于遮罩层 div 内部，点击按钮时事件会冒泡到遮罩层，导致 onClose 被调用两次。虽然对于"关闭"操作来说多次调用不会产生可见 bug（setState(false) 重复调用无副作用），但这不符合预期行为。
suggestion: 在关闭按钮的 onClick 处理中添加 e.stopPropagation()，或者移除关闭按钮的 onClick（让事件冒泡到遮罩层即可）。
```

```
severity: low
status: open
file: frontend/src/components/chat/chat-message.tsx
line: 97
issue: showTextBubble 判断逻辑仅检查严格等于"[图片]"，但用户可能同时输入文字和上传图片
detail: 当 content 不等于"[图片]"时（如用户输入了文字描述同时附加图片），showTextBubble 为 true，图片和文字会同时显示，这是正确行为。但如果用户只上传图片不输入文字，content 被 use-chat 设置为"[图片]"，这是一个约定而非显式标记。如果未来 content 格式变更，此逻辑会失效。
suggestion: 目前逻辑正确且与 use-chat.ts 第 40 行的约定一致，无需立即修改。可考虑在 Message 类型中添加 hasImage 布尔字段替代字符串匹配，但属于后续优化。
```

## 总结

代码实现质量整体良好，符合项目既有模式和编码规范。改动范围精准，6 个文件约 150 行新增代码完成了完整的图片预览+OCR 展示功能。

**需要关注的问题**：
- 1 个 HIGH 级别（OCR XSS 风险）— 已修复（escapeHtml 函数）
- 2 个 MEDIUM 级别 — 建议修复但不阻塞合并
- 2 个 LOW 级别 — 记录备忘，可在后续迭代中处理

**通过的检查**：
- TypeScript 类型检查通过
- 所有后端测试通过（85/85）
- 所有前端测试通过（25/25）
- 代码风格符合项目规范（Tailwind, cn(), lucide-react）
- 无新增依赖（功能代码层面）
- 向后兼容（纯文本消息渲染不受影响）
