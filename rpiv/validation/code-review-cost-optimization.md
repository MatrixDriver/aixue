---
description: "代码审查报告: 成本优化（图片预处理 + OCR/推理拆分）"
status: completed
created_at: 2026-03-06T23:30:00
updated_at: 2026-03-06T23:30:00
archived_at: null
---

# 代码审查报告

## 变更概览

**统计：**

- 修改的文件：5
- 添加的文件：1 (`frontend/src/lib/image-utils.ts`)
- 删除的文件：0
- 新增行：85
- 删除行：31

**变更文件：**
| 文件 | 类型 | 描述 |
|------|------|------|
| `src/aixue/config.py` | 修改 | 新增 `llm_model_ocr` 配置字段 |
| `src/aixue/services/llm_service.py` | 修改 | `recognize_image()` 使用 OCR 专用模型 |
| `.env.example` | 修改 | 新增 `LLM_MODEL_OCR` 配置示例 |
| `frontend/src/lib/image-utils.ts` | 新建 | 图片压缩工具函数 |
| `frontend/src/components/chat/image-upload.tsx` | 修改 | 集成压缩逻辑 |
| `CLAUDE.md` | 修改 | 更新项目文档（与功能无关） |

## 审查结果

### 后端 — config.py (第 19 行)

实现简洁正确。`llm_model_ocr: str = ""` 遵循现有字段命名规范，空字符串默认值与 pydantic-settings 环境变量加载机制兼容。

**结论**: 无问题。

### 后端 — llm_service.py (第 150-152 行)

```python
ocr_model = self.settings.llm_model_ocr or self.settings.llm_model_light
logger.info("LLM 图片识别请求: media_type=%s, size=%d bytes, model=%s", media_type, len(image_data), ocr_model)
return await self.chat(messages, model=ocr_model, max_tokens=max_tokens)
```

回退逻辑 `or` 模式与 `chat()` 方法第 46 行的 `model = model or self.settings.llm_model` 一致。日志新增模型名称便于调试。

**结论**: 无问题。

### 后端 — .env.example

```
# OCR 模型（图片识别），不配置则回退到 LLM_MODEL_LIGHT
LLM_MODEL_OCR=
```

注释清晰，格式正确。

**结论**: 无问题。

### 前端 — image-utils.ts

```
severity: low
status: open
file: frontend/src/lib/image-utils.ts
line: 29
issue: compressImage 缺少 try-catch 错误处理
detail: 如果 createImageBitmap 因图片损坏而失败，或 canvas.getContext("2d") 返回 null（尽管用了 !），异常会向上传播到 handleFile，但 handleFile 中也没有 try-catch。用户会看到未处理的 Promise rejection 而非友好提示。
suggestion: 在 compressImage 或 handleFile 中添加 try-catch，捕获异常后返回原始文件或提示用户。
```

```
severity: low
status: open
file: frontend/src/lib/image-utils.ts
line: 41
issue: canvas.getContext("2d") 使用非空断言 (!)
detail: 虽然在现代浏览器中 2d context 几乎不可能返回 null，但使用 ! 非空断言绕过了 TypeScript 类型检查。这是一个极低概率的边缘情况。
suggestion: 可接受，风险极低。如果要严格处理，可改为 if (!ctx) throw new Error("...")。
```

### 前端 — image-upload.tsx

```
severity: medium
status: open
file: frontend/src/components/chat/image-upload.tsx
line: 27-38
issue: async handleFile 的 Promise rejection 未被捕获
detail: handleFile 变为 async 后，在 onChange 和 handleDrop 的调用处（第 48 行、第 123 行、第 137 行）未 await 也未 .catch()。如果 compressImage 抛出异常（如图片损坏），会产生 unhandled Promise rejection。
suggestion: 在 handleFile 内部包裹 try-catch，catch 中向用户提示"图片处理失败"并 console.error 记录。
```

### CLAUDE.md 变更

大幅更新项目文档，内容准确反映当前架构。与功能实现无关，属于文档改善。

**结论**: 无问题。

## 问题汇总

| # | 严重度 | 文件 | 行号 | 问题 |
|---|--------|------|------|------|
| 1 | medium | `image-upload.tsx` | 27-38 | async handleFile 未处理 Promise rejection |
| 2 | low | `image-utils.ts` | 29 | compressImage 缺少 try-catch |
| 3 | low | `image-utils.ts` | 41 | canvas context 非空断言 |

## 总结

后端改动非常小（共 4 行变更）且正确，回退逻辑清晰，遵循现有模式。前端新增的图片压缩功能实现完整，但缺少错误处理——异步函数的异常未被捕获，可能导致 unhandled Promise rejection。

**无 CRITICAL 或 HIGH 级别问题。** 1 个 medium 问题（前端 Promise rejection）建议在后续迭代修复，不阻塞当前发布。所有 85 个测试通过，无回归。
