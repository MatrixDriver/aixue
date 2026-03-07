---
description: "技术可行性调研: 图片预处理 + OCR/推理拆分成本优化"
status: archived
created_at: 2026-03-06T11:00:00
updated_at: 2026-03-06T11:00:00
---

## 1. 前端 Canvas API WebP 导出

### 浏览器兼容性

- **Canvas.toBlob / toDataURL 的 WebP 支持**：
  - Chrome 17+、Edge 18+、Firefox 96+、Opera 15+：完全支持 `image/webp` 导出
  - **Safari 16+**（2022年9月发布）：支持 WebP 导出。Safari 15 及更早版本不支持
  - iOS Safari 16+：支持（对应 iOS 16+）
  - 市场覆盖率：截至 2026 年，WebP 导出的全球浏览器支持率已超过 95%

- **降级方案**：不支持 WebP 时使用 JPEG（quality=0.80）完全可行
  - 检测方法：`canvas.toDataURL('image/webp')` 返回结果若以 `data:image/png` 开头则说明不支持 WebP
  - JPEG 在相同质量下体积约为 WebP 的 1.3-1.5 倍，但仍远优于 PNG

### 在 Next.js 中的实现位置

当前图片上传流程：
1. `image-upload.tsx` 的 `handleFile()` 接收 File 对象
2. 调用 `onImageSelect(file)` 传递给 `chat-input.tsx` 的 `setImage`
3. `use-chat.ts` 的 `sendMessage()` 将 File 传给 `api.ts` 的 `solveQuestion()`
4. `solveQuestion()` 通过 FormData 发送原始 File

**最佳插入点**：在 `image-upload.tsx` 的 `handleFile()` 函数中，调用 `onImageSelect(file)` 之前插入压缩逻辑。具体实现：

- 创建独立的 `compressImage(file: File): Promise<File>` 工具函数（放在 `lib/image-utils.ts`）
- 在 `handleFile()` 中 `await compressImage(file)` 后再传递
- `handleFile` 需要改为 async 函数
- 压缩后生成新的 File 对象（保留原文件名但改扩展名），preview 仍用压缩后的结果
- 无需修改 `chat-input.tsx`、`use-chat.ts` 或 `api.ts`，改动完全封装在上传组件中

### 压缩流程伪代码

```
1. 创建 Image 对象加载 File
2. 计算缩放比例（最长边不超过 1536px，不放大）
3. 创建 Canvas，drawImage 缩放绘制
4. canvas.toBlob('image/webp', 0.85) 尝试 WebP
5. 若失败（toBlob 返回 null 或检测不支持），改用 canvas.toBlob('image/jpeg', 0.80)
6. 将 Blob 包装为 File 对象返回
```

---

## 2. 后端 OCR/推理拆分

### 当前 LLMService 架构分析

**client 实例化方式**（`llm_service.py:21-26`）：
- 单个 `AsyncOpenAI` client，绑定 OpenRouter 的 base_url 和 api_key
- **关键发现**：`chat()` 方法已支持 `model` 参数覆盖，默认使用 `self.settings.llm_model`
- `recognize_image()` 方法（第 119-151 行）也通过 `chat()` 调用，且硬编码使用 `self.settings.llm_model`

**OpenRouter 模型切换**：
- OpenRouter 的 OpenAI 兼容 API 天然支持在同一 API key 下调用不同模型——只需在每次请求中传入不同的 `model` 参数
- 当前 `chat()` 方法的签名 `model: str | None = None` 已经支持这一点
- **无需创建多个 LLMService 实例**，也无需多个 client

### OCR 阶段模型切换方案

**改动极小**：只需修改 `recognize_image()` 方法，将 model 从硬编码的 `self.settings.llm_model` 改为 `self.settings.llm_model_ocr`：

```python
# 当前代码 (llm_service.py:151)
return await self.chat(messages, model=self.settings.llm_model, max_tokens=max_tokens)

# 改为
return await self.chat(messages, model=self.settings.llm_model_ocr, max_tokens=max_tokens)
```

**OCRService 无需修改**：`ocr_service.py` 调用的是 `self.llm.recognize_image()`，模型选择逻辑封装在 LLMService 内部。

### 两阶段拆分的调用链

当前解题流程（推测）：上传图片 -> OCR 识别 -> 解题推理，OCR 和推理已经是分开的步骤（`OCRService.recognize()` + 后续 `LLMService.chat()` 推理调用）。拆分模型只需确保两个阶段使用不同的 model 参数，现有架构已天然支持。

---

## 3. 配置扩展

### 当前 Settings 结构（`config.py`）

```python
llm_model: str = "google/gemini-3.1-pro-preview"      # 推理模型
llm_model_light: str = "google/gemini-2.5-flash"       # 轻量模型（学科判定等）
```

### 新增 `llm_model_ocr` 的方案

在 Settings 类中添加一个字段，使用 `@property` 或 Pydantic `model_validator` 实现回退逻辑：

**推荐方案（最简洁）**：直接在字段中设为空字符串，在 LLMService 中处理回退

```python
# config.py 新增
llm_model_ocr: str = ""  # OCR 模型，为空时回退到 llm_model_light
```

```python
# llm_service.py 中使用
ocr_model = self.settings.llm_model_ocr or self.settings.llm_model_light
```

**回退逻辑**：`LLM_MODEL_OCR` 未配置（空字符串） -> 使用 `LLM_MODEL_LIGHT`（当前为 `google/gemini-2.5-flash`）

这符合需求摘要中的"未配置时默认回退到 LLM_MODEL_LIGHT"要求，且不需要 Pydantic validator，实现最简洁。

### .env 配置示例

```env
# 推理模型（解题）
LLM_MODEL=google/gemini-3.1-pro-preview
# OCR 模型（图片识别），不配置则回退到 LLM_MODEL_LIGHT
LLM_MODEL_OCR=google/gemini-2.5-flash
# 轻量模型（学科判定等辅助任务）
LLM_MODEL_LIGHT=google/gemini-2.5-flash
```

---

## 4. 前端图片上传现有实现

### 文件位置与数据流

| 文件 | 职责 |
|------|------|
| `frontend/src/components/chat/image-upload.tsx` | 图片选择/拍照/拖拽 UI + 文件验证 |
| `frontend/src/components/chat/chat-input.tsx` | 组合输入框 + ImageUpload，管理 text/image 状态 |
| `frontend/src/hooks/use-chat.ts` | 对话状态管理，调用 API |
| `frontend/src/lib/api.ts` | Axios 封装，`solveQuestion()` 通过 FormData 发送 |

### 当前图片处理逻辑

- `image-upload.tsx:handleFile()`：仅做类型检查（`image/*`）和大小限制（5MB），**无任何压缩/格式转换**
- 图片以原始 File 对象传递，最终通过 `FormData.append("image", file)` 发送
- 5MB 限制在前端和后端（`config.py:max_image_size`）均有

### 压缩逻辑插入方案

**改动范围最小的方案**：

1. 新建 `frontend/src/lib/image-utils.ts`，实现 `compressImage()` 函数
2. 修改 `image-upload.tsx` 的 `handleFile()`，在验证通过后调用压缩
3. 压缩后的 File 对象替代原始 File 传递给 `onImageSelect`
4. 其他文件（chat-input、use-chat、api）完全不需要修改

**注意事项**：
- 压缩是异步操作（Canvas + toBlob），`handleFile` 需要变为 async
- 压缩后文件可能远小于 5MB，可以考虑在压缩前放宽或移除前端大小限制（让用户能上传大图，压缩后再检查）
- preview 应使用压缩后的图片生成（减少内存占用）

---

## 5. 风险与注意事项

| 风险点 | 等级 | 缓解措施 |
|--------|------|----------|
| Safari 15 及以下不支持 WebP 导出 | 低 | 运行时检测 + JPEG 降级，2026年 Safari 15 用户极少 |
| Canvas 压缩可能损失关键细节（小字/公式） | 中 | 1536px 分辨率对手机拍照足够；quality=85 保留高细节 |
| OCR 模型切换后识别质量变化 | 低 | 默认回退到 llm_model_light（已验证的 Gemini Flash），运营可随时调整 |
| 前端压缩对低端手机性能影响 | 低 | Canvas 操作由浏览器原生实现，1536px 图片处理耗时通常 <200ms |

## 6. 结论

**所有技术方案均可行，改动量小**：

- **前端**：新增 1 个工具函数文件 + 修改 `image-upload.tsx` 的 `handleFile()`，约 50 行新代码
- **后端**：`config.py` 新增 1 个字段 + `llm_service.py` 修改 1 行模型引用，约 5 行改动
- **无需新增依赖**：前端 Canvas API 为浏览器原生能力，后端 OpenRouter client 已支持多模型切换
- **向后兼容**：所有新配置项均有合理默认值，不配置时行为与当前完全一致
