---
title: "测试规格: 成本优化（图片预处理 + OCR/推理拆分）"
status: completed
created_at: 2026-03-06T23:00:00
updated_at: 2026-03-06T23:00:00
---

# 测试规格: 成本优化

基于 PRD `rpiv/requirements/prd-cost-optimization.md` 和测试策略 `rpiv/validation/test-strategy-cost-optimization.md`。

---

## 1. 模型配置测试 (CO-CFG)

### CO-CFG-001: LLM_MODEL_OCR 配置加载
- **场景**: .env 中设置了 `LLM_MODEL_OCR=google/gemini-2.0-flash-001`
- **预期**: `Settings().llm_model_ocr` 返回 `"google/gemini-2.0-flash-001"`
- **验收**: 值完全匹配

### CO-CFG-002: LLM_MODEL_OCR 未配置时回退
- **场景**: .env 中未设置 `LLM_MODEL_OCR`
- **预期**: `Settings().ocr_model` 返回 `Settings().llm_model_light` 的值
- **验收**: `ocr_model == llm_model_light`

### CO-CFG-003: OCR 和推理模型独立
- **场景**: `LLM_MODEL_OCR=model-a`, `LLM_MODEL=model-b`
- **预期**: `ocr_model != llm_model`
- **验收**: 两个值不同且各自正确

### CO-CFG-004: ocr_model 属性正确
- **场景**: `LLM_MODEL_OCR` 已设置
- **预期**: `ocr_model` 返回 `LLM_MODEL_OCR` 而非 `LLM_MODEL_LIGHT`
- **验收**: `ocr_model == llm_model_ocr`

---

## 2. OCR 服务测试 (CO-OCR)

### CO-OCR-001: OCR 阶段使用独立模型
- **场景**: 调用 `OCRService.recognize()` 识别图片
- **预期**: 底层 `llm.recognize_image()` 调用时使用 `settings.ocr_model` 作为模型参数
- **验收**: Mock `llm.recognize_image` 的 `model` 参数等于配置的 OCR 模型

### CO-OCR-002: OCR 输出结构化文本
- **场景**: 提供包含数学公式的图片
- **预期**: OCR 返回包含 LaTeX 公式标记的文本（如 `$x^2 + 3x$`）
- **验收**: 返回值为非空字符串

### CO-OCR-003: OCR 结果为空时报错
- **场景**: LLM 返回空字符串
- **预期**: 服务返回明确的错误/空结果，上层处理应提示用户
- **验收**: 返回空字符串，`SolverService` 中判断后返回错误提示

### CO-OCR-004: 聚焦指定题目功能保留
- **场景**: 用户提供 `user_hint="第14题"`
- **预期**: OCR Prompt 使用 `RECOGNITION_FOCUSED_PROMPT`，包含用户提示
- **验收**: `llm.recognize_image` 被调用时的 prompt 参数包含 "第14题"

---

## 3. 解题管线拆分测试 (CO-PIPE)

### CO-PIPE-001: 图片输入走两阶段流程
- **场景**: 提供 image + media_type，无 text
- **预期**:
  1. 先调用 OCR（使用 OCR 模型），获得纯文本
  2. 再调用推理（使用推理模型），接收纯文本
- **验收**:
  - `llm.recognize_image` 被调用 1 次
  - `llm.chat` 被调用（推理），且 messages 中不含图片数据

### CO-PIPE-002: 纯文本输入跳过 OCR
- **场景**: 仅提供 text，无 image
- **预期**: 不调用 OCR，直接进入推理阶段
- **验收**: `llm.recognize_image` 未被调用

### CO-PIPE-003: 图片+文本输入（聚焦模式）
- **场景**: 同时提供 image 和 text（如 "第3题"）
- **预期**: OCR 以 text 为 user_hint 聚焦识别，推理阶段接收 OCR 文本
- **验收**: `recognize_image` 调用时 prompt 包含用户文本

### CO-PIPE-004: OCR 失败时返回错误
- **场景**: OCR 返回空文本，且无用户文本输入
- **预期**: `solve()` 返回包含错误提示的结果
- **验收**: 返回字典包含 `"error"` 键

### CO-PIPE-005: 推理阶段不含图片 token
- **场景**: 图片输入走两阶段流程
- **预期**: 推理阶段的 LLM 调用 messages 中无 `image_url` 类型的 content block
- **验收**: 检查 `llm.chat` 调用的 messages 参数，所有 content 均为纯文本

### CO-PIPE-006: 推理模型正确
- **场景**: 图片输入，配置了不同的 OCR 和推理模型
- **预期**: 推理阶段使用 `LLM_MODEL` 而非 `LLM_MODEL_OCR`
- **验收**: `llm.chat` 调用时 model 参数为推理模型

### CO-PIPE-007: 数学题 SymPy 验证流程不受影响
- **场景**: 图片输入的数学题，走两阶段流程
- **预期**: OCR 输出文本后，MathSolver 正常执行 SymPy 前置求解和验证
- **验收**: `verifier.pre_solve` 被调用，且解题结果正常返回

---

## 4. 前端图片压缩测试 (CO-IMG)

### CO-IMG-001: 大图缩放至 1536px
- **场景**: 输入 4000x3000 图片
- **预期**: 输出最长边为 1536px，短边按比例缩放（1536x1152）
- **验收**: 输出图片宽高均不超过 1536px，宽高比与原图一致

### CO-IMG-002: 小图不放大
- **场景**: 输入 800x600 图片
- **预期**: 输出尺寸保持 800x600，不放大
- **验收**: 输出尺寸等于原图尺寸

### CO-IMG-003: 正方形图片处理
- **场景**: 输入 2000x2000 图片
- **预期**: 输出 1536x1536
- **验收**: 宽高均为 1536

### CO-IMG-004: WebP 格式输出
- **场景**: 浏览器支持 WebP
- **预期**: 输出格式为 WebP，quality=85
- **验收**: 输出 Blob 的 type 为 `image/webp`

### CO-IMG-005: WebP 不支持时降级 JPEG
- **场景**: 浏览器不支持 WebP 导出
- **预期**: 输出格式为 JPEG，quality=80
- **验收**: 输出 Blob 的 type 为 `image/jpeg`

### CO-IMG-006: 压缩后体积减小
- **场景**: 输入高分辨率 PNG 图片
- **预期**: 输出文件大小显著小于原文件
- **验收**: 输出大小 < 原始大小

### CO-IMG-007: 压缩函数为异步
- **场景**: 调用压缩函数
- **预期**: 返回 Promise
- **验收**: 函数返回值为 Promise<Blob>

---

## 5. API 集成测试 (CO-API)

### CO-API-001: 图片上传解题响应格式不变
- **场景**: POST `/api/solve` 上传图片
- **预期**: 响应包含 `session_id`, `content`, `subject` 等字段
- **验收**: HTTP 200，JSON 结构与现有一致

### CO-API-002: 纯文本解题响应格式不变
- **场景**: POST `/api/solve` 仅传文本
- **预期**: 响应格式与优化前一致
- **验收**: HTTP 200，JSON 结构与现有一致

### CO-API-003: 无输入返回错误
- **场景**: POST `/api/solve` 无图片无文本
- **预期**: 返回 400/422 错误
- **验收**: HTTP 状态码为 400 或 422

---

## 6. 回归测试 (CO-REG)

### CO-REG-001: 现有解题管线测试全部通过
- **验收**: `tests/test_services/test_solver_service.py` 所有用例通过

### CO-REG-002: 现有 API 测试全部通过
- **验收**: `tests/test_api/test_solver.py` 所有用例通过

### CO-REG-003: 完整测试套件无回归
- **验收**: `uv run pytest` 全部通过，无失败、无错误

---

## 7. 测试文件规划

| 测试文件 | 覆盖规格 | 类型 |
|----------|----------|------|
| `tests/test_services/test_config_cost.py` | CO-CFG-001 ~ CO-CFG-004 | 单元测试 |
| `tests/test_services/test_ocr_cost.py` | CO-OCR-001 ~ CO-OCR-004 | 单元测试 |
| `tests/test_services/test_solver_pipeline_cost.py` | CO-PIPE-001 ~ CO-PIPE-007 | 单元/集成测试 |
| `tests/test_api/test_solver.py` | CO-API-001 ~ CO-API-003 | API 集成测试（扩展现有文件） |
| `frontend/src/__tests__/imageCompress.test.ts` | CO-IMG-001 ~ CO-IMG-007 | 前端单元测试 |
| （现有测试文件） | CO-REG-001 ~ CO-REG-003 | 回归测试 |
