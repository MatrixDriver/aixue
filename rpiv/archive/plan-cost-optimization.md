---
description: "功能实施计划: 图片预处理与OCR/推理拆分成本优化"
status: archived
created_at: 2026-03-06T22:45:00
updated_at: 2026-03-06T22:35:00
archived_at: 2026-03-06T22:50:00
related_files:
  - rpiv/requirements/prd-cost-optimization.md
---

# 功能: 图片预处理与 OCR/推理拆分成本优化

以下计划应该是完整的，但在开始实施之前，验证文档和代码库模式以及任务合理性非常重要。

特别注意现有工具、类型和模型的命名。从正确的文件导入等。

## 功能描述

通过三个维度降低 AIXue 解题流程的 API 成本：
1. **前端图片压缩**：上传前自动缩放至 1536px + WebP/JPEG 转换，减少图片 token
2. **后端 OCR 模型独立配置**：OCR 阶段使用独立配置的模型（`LLM_MODEL_OCR`），与推理模型分离
3. **推理阶段纯文本化**：推理阶段仅接收 OCR 输出的纯文本，不再发送图片给推理模型

整个优化对终端用户完全透明。

## 用户故事

作为 AIXue 运营人员，
我想要前端自动压缩图片、后端 OCR 和推理使用独立模型，
以便在不牺牲解题质量的前提下降低 40%+ 的 API 成本。

## 问题陈述

当前解题流程中，高分辨率图片直接发送给视觉 LLM，OCR 和推理共用同一模型。这导致：
- 高分辨率图片消耗大量图片 token
- OCR 识别完成后，推理阶段仍然携带图片 token
- 无法为 OCR 和推理阶段分别选择性价比最优的模型

## 解决方案陈述

1. 前端在上传前用 Canvas API 压缩图片（最长边 1536px + WebP），减少传输量和图片 token
2. 后端 `recognize_image()` 使用独立的 `LLM_MODEL_OCR` 模型，与推理模型 `LLM_MODEL` 分离
3. 现有架构已经将 OCR 和推理分为两步（`OCRService.recognize()` + `MathSolver/GeneralSolver`），推理阶段已经只接收纯文本，无需改造数据流

## 功能元数据

**功能类型**：增强
**估计复杂度**：低
**主要受影响的系统**：前端图片上传组件、后端 LLM 配置和 OCR 模型选择
**依赖项**：无新增外部依赖

---

## 上下文参考

### 相关代码库文件 重要：在实施之前必须阅读这些文件！

- `src/aixue/config.py` (第 6-33 行) - 原因：Settings 类，需新增 `llm_model_ocr` 字段
- `src/aixue/services/llm_service.py` (第 119-151 行) - 原因：`recognize_image()` 方法，当前硬编码 `self.settings.llm_model`，需改为 OCR 专用模型
- `src/aixue/services/ocr_service.py` (第 53-93 行) - 原因：`OCRService.recognize()` 调用 `self.llm.recognize_image()`，确认不需要修改
- `src/aixue/services/solver_service.py` (第 36-94 行) - 原因：`SolverService.solve()` 解题主控流程，确认 OCR→纯文本→推理的数据流已存在
- `src/aixue/services/math_solver.py` (第 26-106 行) - 原因：确认 MathSolver 已经只接收纯文本 `question`
- `src/aixue/services/general_solver.py` (第 20-73 行) - 原因：确认 GeneralSolver 已经只接收纯文本 `question`
- `frontend/src/components/chat/image-upload.tsx` (第 25-38 行) - 原因：`handleFile()` 函数，压缩逻辑插入点
- `frontend/src/lib/api.ts` (第 102-120 行) - 原因：`solveQuestion()` 通过 FormData 发送图片，确认不需要修改
- `.env.example` - 原因：需新增 `LLM_MODEL_OCR` 示例配置
- `src/aixue/api/endpoints/solver.py` (第 40-106 行) - 原因：solve_problem 端点，确认不需要修改

### 要创建的新文件

- `frontend/src/lib/image-utils.ts` — 图片压缩工具函数 `compressImage()`

### 要遵循的模式

**配置字段模式**（`config.py:17-18`）：
```python
llm_model: str = "google/gemini-3.1-pro-preview"
llm_model_light: str = "google/gemini-2.5-flash"
# 新增字段遵循相同命名规范
llm_model_ocr: str = ""
```

**模型参数传递模式**（`llm_service.py:46`）：
```python
model = model or self.settings.llm_model
```
LLMService.chat() 已支持 `model` 参数覆盖，不需要创建新的 client 实例。

**日志模式**（全局）：
```python
logger = logging.getLogger(__name__)
logger.info("操作描述: key=%s, value=%d", key, value)
```

**前端工具函数模式**（参考 `frontend/src/lib/` 目录）：
独立的纯函数，TypeScript 类型标注，Promise 封装异步操作。

---

## 实施计划

### 阶段 1: 后端配置扩展（约 5 行改动）

在 config.py 新增 OCR 模型配置字段，在 llm_service.py 修改 `recognize_image()` 使用 OCR 专用模型。

### 阶段 2: 前端图片压缩（约 60 行新代码）

创建图片压缩工具函数，集成到图片上传组件。

### 阶段 3: 配置文件更新

更新 .env.example。

---

## 逐步任务

重要：按顺序从上到下执行每个任务。每个任务都是原子的且可独立测试。

### 任务 1: UPDATE `src/aixue/config.py` — 新增 OCR 模型配置

- **IMPLEMENT**：在 Settings 类的 `llm_model_light` 字段后面新增一行：
  ```python
  llm_model_ocr: str = ""  # OCR 模型，为空时回退到 llm_model_light
  ```
- **PATTERN**：遵循 `config.py:17-18` 现有字段命名规范（snake_case，类型标注，默认值）
- **GOTCHA**：使用空字符串 `""` 作为默认值而非 `None`，因为 pydantic-settings 从环境变量读取时空字符串更自然。回退逻辑在 llm_service.py 中用 `or` 实现
- **VALIDATE**：`cd /d/CODE/aixue && uv run python -c "from aixue.config import Settings; s = Settings(); print(f'ocr={s.llm_model_ocr!r}, light={s.llm_model_light!r}')"`

### 任务 2: UPDATE `src/aixue/services/llm_service.py` — OCR 使用独立模型

- **IMPLEMENT**：修改 `recognize_image()` 方法第 151 行，将模型从硬编码的 `self.settings.llm_model` 改为 OCR 模型：
  ```python
  # 原代码 (第 151 行):
  return await self.chat(messages, model=self.settings.llm_model, max_tokens=max_tokens)

  # 改为:
  ocr_model = self.settings.llm_model_ocr or self.settings.llm_model_light
  return await self.chat(messages, model=ocr_model, max_tokens=max_tokens)
  ```
- **PATTERN**：回退逻辑用 `or` 实现，与 `chat()` 方法第 46 行的 `model = model or self.settings.llm_model` 模式一致
- **IMPORTS**：无新增导入
- **GOTCHA**：同时更新第 150 行的日志，加上模型名称以便调试：
  ```python
  logger.info("LLM 图片识别请求: media_type=%s, size=%d bytes, model=%s", media_type, len(image_data), ocr_model)
  ```
- **VALIDATE**：`cd /d/CODE/aixue && uv run python -c "from aixue.services.llm_service import LLMService; s = LLMService(); print('LLMService 初始化成功')"`

### 任务 3: UPDATE `.env.example` — 新增 OCR 模型配置示例

- **IMPLEMENT**：在 `LLM_MODEL_LIGHT` 行之后新增：
  ```env
  # OCR 模型（图片识别），不配置则回退到 LLM_MODEL_LIGHT
  LLM_MODEL_OCR=
  ```
- **PATTERN**：遵循现有注释风格（中文说明 + 等号后为空表示默认）
- **VALIDATE**：目视检查文件格式

### 任务 4: CREATE `frontend/src/lib/image-utils.ts` — 图片压缩工具函数

- **IMPLEMENT**：创建包含 `compressImage()` 函数的工具文件，完整代码如下：
  ```typescript
  /**
   * 图片压缩工具：缩放至最长边 1536px + WebP/JPEG 格式转换。
   */

  const MAX_DIMENSION = 1536;
  const WEBP_QUALITY = 0.85;
  const JPEG_QUALITY = 0.80;

  /**
   * 检测浏览器是否支持 WebP 导出。
   */
  function supportsWebP(): boolean {
    const canvas = document.createElement("canvas");
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL("image/webp").startsWith("data:image/webp");
  }

  /**
   * 压缩图片文件：缩放至最长边 1536px，转换为 WebP（不支持则 JPEG）。
   *
   * - 小于 1536px 的图片不放大，仅做格式转换
   * - 压缩为异步操作
   *
   * @param file 原始图片 File 对象
   * @returns 压缩后的 File 对象
   */
  export async function compressImage(file: File): Promise<File> {
    const bitmap = await createImageBitmap(file);
    const { width, height } = bitmap;

    // 计算缩放比例（不放大）
    const scale = Math.min(1, MAX_DIMENSION / Math.max(width, height));
    const newWidth = Math.round(width * scale);
    const newHeight = Math.round(height * scale);

    // 绘制到 Canvas
    const canvas = document.createElement("canvas");
    canvas.width = newWidth;
    canvas.height = newHeight;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(bitmap, 0, 0, newWidth, newHeight);
    bitmap.close();

    // 选择输出格式
    const useWebP = supportsWebP();
    const mimeType = useWebP ? "image/webp" : "image/jpeg";
    const quality = useWebP ? WEBP_QUALITY : JPEG_QUALITY;
    const ext = useWebP ? ".webp" : ".jpg";

    // 导出 Blob
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error("Canvas toBlob 失败"))),
        mimeType,
        quality
      );
    });

    // 构造新文件名
    const baseName = file.name.replace(/\.[^.]+$/, "");
    return new File([blob], `${baseName}${ext}`, { type: mimeType });
  }
  ```
- **GOTCHA**：
  - 使用 `createImageBitmap` 而非 `new Image()`，前者不需要处理 onload 回调，更简洁
  - `createImageBitmap` 在 Next.js SSR 环境不存在，但此函数只在客户端调用（image-upload.tsx 已标记 `"use client"`）
  - `bitmap.close()` 及时释放内存
- **VALIDATE**：`cd /d/CODE/aixue/frontend && npx tsc --noEmit src/lib/image-utils.ts` 或前端构建检查

### 任务 5: UPDATE `frontend/src/components/chat/image-upload.tsx` — 集成图片压缩

- **IMPLEMENT**：修改 `handleFile` 回调，在验证通过后调用压缩：
  1. 添加导入：
     ```typescript
     import { compressImage } from "@/lib/image-utils";
     ```
  2. 将 `handleFile` 改为 async 函数，在 `onImageSelect(file)` 之前压缩：
     ```typescript
     const handleFile = useCallback(
       async (file: File) => {
         if (!file.type.startsWith("image/")) return;
         // 压缩前不限制大小（压缩后通常远小于 5MB）
         // 压缩后再检查（保留合理上限以防异常）
         const compressed = await compressImage(file);
         if (compressed.size > 10 * 1024 * 1024) {
           alert("图片压缩后仍超过 10MB，请使用更小的图片");
           return;
         }
         onImageSelect(compressed);
         const reader = new FileReader();
         reader.onloadend = () => setPreview(reader.result as string);
         reader.readAsDataURL(compressed);
       },
       [onImageSelect]
     );
     ```
- **PATTERN**：遵循现有 `useCallback` + 依赖数组模式（`image-upload.tsx:25-38`）
- **GOTCHA**：
  - `handleFile` 变为 async 后，调用处（onChange、handleDrop）不需要修改，因为它们不 await 结果
  - 前端大小限制从 5MB 改为 10MB（压缩前允许更大的原图，压缩后通常 <1MB）
  - preview 使用压缩后的图片生成（减少内存占用）
- **VALIDATE**：`cd /d/CODE/aixue/frontend && npm run build`

---

## 测试策略

### 单元测试

**后端**：
- `config.py` 字段测试：验证 `llm_model_ocr` 默认值为空字符串
- `llm_service.py` 模型选择测试：验证 `recognize_image()` 使用 OCR 模型而非默认推理模型

**前端**：
- `compressImage()` 函数测试（需要 jsdom/canvas polyfill，或跳过纯浏览器 API 测试）

### 集成测试

- 上传图片解题端到端流程：确认 OCR 使用正确模型，推理使用正确模型
- 纯文本解题流程：确认跳过 OCR，直接推理

### 边缘情况

- `LLM_MODEL_OCR` 未配置（空字符串）：应回退到 `LLM_MODEL_LIGHT`
- `LLM_MODEL_OCR` 已配置：应使用指定模型
- 小于 1536px 的图片：不放大，仅格式转换
- 浏览器不支持 WebP：降级 JPEG
- 极大图片（如 8000x6000）：正常压缩到 1536px

---

## 验证命令

### 级别 1: 语法和样式

```bash
# 后端 Lint
cd /d/CODE/aixue && uv run ruff check src/aixue/config.py src/aixue/services/llm_service.py

# 前端类型检查
cd /d/CODE/aixue/frontend && npx tsc --noEmit
```

### 级别 2: 单元测试

```bash
cd /d/CODE/aixue && uv run pytest tests/ -x -q
```

### 级别 3: 集成测试

```bash
# 前端构建（包含类型检查和打包）
cd /d/CODE/aixue/frontend && npm run build
```

### 级别 4: 手动验证

1. 启动后端：`cd /d/CODE/aixue && uv run uvicorn aixue.main:app --reload`
2. 启动前端：`cd /d/CODE/aixue/frontend && npm run dev`
3. 上传一张高清图片（>1536px），在浏览器 DevTools Network 面板确认：
   - 发送的图片为 WebP 格式
   - 图片尺寸已压缩
4. 检查后端日志，确认 OCR 请求使用的模型与 `LLM_MODEL_OCR` 或 `LLM_MODEL_LIGHT` 一致
5. 检查后端日志，确认推理请求使用的模型与 `LLM_MODEL` 一致
6. 输入纯文本题目，确认直接进入推理，无 OCR 调用

---

## 验收标准

- [ ] `config.py` 新增 `llm_model_ocr` 字段，默认空字符串
- [ ] `llm_service.py` 的 `recognize_image()` 使用 `llm_model_ocr or llm_model_light` 作为模型
- [ ] `.env.example` 包含 `LLM_MODEL_OCR` 配置示例
- [ ] `frontend/src/lib/image-utils.ts` 实现 `compressImage()` 函数
- [ ] `image-upload.tsx` 的 `handleFile()` 调用 `compressImage()` 压缩后再传递
- [ ] 大图片上传后被压缩至 1536px 以内
- [ ] WebP 不支持时降级为 JPEG
- [ ] 现有解题功能无回归（纯文本输入、图片输入、追问均正常）
- [ ] 后端 Lint 和前端 TypeScript 编译通过
- [ ] 后端 pytest 通过

---

## 完成检查清单

- [ ] 所有任务按顺序完成
- [ ] 每个任务验证立即通过
- [ ] 所有验证命令成功执行
- [ ] 完整测试套件通过（单元 + 集成）
- [ ] 无代码检查或类型检查错误
- [ ] 手动测试确认功能有效
- [ ] 所有验收标准均满足

---

## 备注

### 架构决策

1. **为什么后端改动极小？** 通过代码分析发现，现有架构已经将 OCR 和推理分为两步：`SolverService._recognize()` 调用 `OCRService.recognize()` 完成 OCR，然后将纯文本传给 `MathSolver.solve()` 或 `GeneralSolver.solve()`。推理阶段已经只接收纯文本 `question` 参数，不接触图片数据。因此不需要修改数据流，只需让 OCR 阶段使用独立模型。

2. **为什么用空字符串而非 `None`？** pydantic-settings 从环境变量加载时，空字符串 `""` 是自然的"未配置"状态。使用 `str = ""` 比 `str | None = None` 更简洁，回退逻辑用 `or` 一行搞定。

3. **前端压缩使用 `createImageBitmap`**：比传统的 `new Image()` + onload 模式更现代、代码更简洁，且支持 Worker 环境。浏览器兼容性覆盖率 >97%（Chrome 50+, Firefox 42+, Safari 15+）。

4. **前端大小限制调整**：压缩前允许更大的原图（10MB 上限），因为压缩后通常 <1MB。后端 5MB 限制保持不变，作为最终安全网。

### 风险评估

- **低风险**：后端改动仅 2 处（config + llm_service），且有回退机制
- **低风险**：前端压缩使用浏览器原生 API，无外部依赖
- **信心分数**：9/10 — 改动量小，现有架构天然支持，有完善的回退机制
