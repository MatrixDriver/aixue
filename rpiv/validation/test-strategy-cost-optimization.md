---
title: "测试策略: 成本优化（图片预处理 + OCR/推理拆分）"
status: completed
created_at: 2026-03-06T11:00:00
updated_at: 2026-03-06T11:00:00
---

# 测试策略: 成本优化

## 1. 测试范围

本策略覆盖三个核心场景：

| 场景 | 层级 | 测试类型 |
|------|------|----------|
| 前端图片压缩 | 前端 (Next.js) | 单元测试 + 集成测试 |
| 后端 OCR/推理拆分 | 后端 (FastAPI) | 单元测试 + 集成测试 + API 测试 |
| 模型独立配置 | 后端 (配置层) | 单元测试 |

## 2. 测试框架与工具

### 后端
- **框架**: pytest + pytest-asyncio（沿用现有模式）
- **Mock**: unittest.mock.AsyncMock（沿用现有模式）
- **HTTP 客户端**: httpx.AsyncClient + ASGITransport（沿用 conftest.py 模式）
- **数据库**: SQLite 内存数据库，通过依赖覆盖注入

### 前端
- **框架**: Jest / Vitest（视 frontend 配置而定）
- **图片处理测试**: Canvas API mock 或 jsdom 环境

## 3. 场景一：前端图片压缩

### 测试目标
验证上传图片在发送前被正确压缩（最长边 1536px，WebP quality=85）。

### 测试用例分类

**单元测试**（图片压缩函数）：
- 大图（如 4000x3000）压缩后最长边不超过 1536px，宽高比保持
- 小图（如 800x600）不放大，仅做格式转换
- 正方形图片（如 2000x2000）正确处理
- 输出格式为 WebP（浏览器支持时）
- WebP 不支持时降级为 JPEG (quality=80)
- 压缩后文件大小显著小于原图

**集成测试**（上传流程）：
- 上传组件调用压缩函数后再发送请求
- 压缩失败时的降级行为（发送原图或提示错误）

### Mock 策略
- Mock Canvas API (`HTMLCanvasElement.prototype.toBlob`)
- Mock `createImageBitmap` 或 `Image` 对象

## 4. 场景二：后端 OCR/推理两阶段拆分

### 测试目标
验证解题管线正确拆分为 OCR 阶段和推理阶段，各阶段使用独立模型调用。

### 测试用例分类

**单元测试**（OCR Service 改造）：
- OCR 阶段使用 `LLM_MODEL_OCR` 配置的模型
- OCR 输出为结构化文本（含 LaTeX 公式）
- OCR 识别失败返回明确错误
- OCR 结果为空时返回错误提示

**单元测试**（Solver Service 改造）：
- 图片输入：先走 OCR 再走推理，两次 LLM 调用使用不同模型
- 纯文本输入：跳过 OCR，直接进入推理阶段
- OCR 结果正确传递给推理阶段（结构化文本，非图片）
- 推理阶段接收纯文本（不含图片 token）

**API 集成测试**（solve 端点）：
- 图片上传触发两阶段流程，响应格式不变
- 纯文本输入仅触发推理阶段
- OCR 失败时返回合适的 HTTP 错误码和提示

### Mock 策略
- 沿用现有 `mock_llm` 模式，扩展为区分 OCR 调用和推理调用
- 通过检查 `mock_llm` 的调用参数（model 参数）验证模型选择正确
- 数据库仍使用 `_make_mock_db()` 模式

## 5. 场景三：模型独立配置

### 测试目标
验证 `LLM_MODEL_OCR` 配置项正确加载、回退逻辑正确。

### 测试用例分类

**单元测试**（Settings / config.py）：
- `LLM_MODEL_OCR` 设置时，OCR 阶段使用该值
- `LLM_MODEL_OCR` 未设置时，回退到 `LLM_MODEL_LIGHT`
- `LLM_MODEL` 和 `LLM_MODEL_OCR` 可以配置为不同模型
- 配置值通过 `Settings` 类正确暴露

### Mock 策略
- 使用 `monkeypatch` 或环境变量覆盖测试不同配置组合

## 6. 回归测试

成本优化不应破坏现有功能。以下现有测试必须全部通过：

- `tests/test_services/test_solver_service.py` — 解题管线（IT-SOL-001 ~ IT-SOL-007）
- `tests/test_api/test_solver.py` — 解题 API 端点（E2E-001 ~ E2E-005）
- 所有其他现有测试

## 7. 测试命名规范

沿用现有命名模式：
- 测试文件: `test_<module>.py`
- 测试类: `Test<Feature>`
- 测试方法: `test_<scenario>`
- 测试规格编号: `CO-<类别>-<序号>`（CO = Cost Optimization）
  - `CO-IMG-xxx`: 图片压缩
  - `CO-OCR-xxx`: OCR 拆分
  - `CO-CFG-xxx`: 模型配置
  - `CO-REG-xxx`: 回归

## 8. 质量门槛

- 所有新增测试通过
- 所有现有测试通过（零回归）
- 新增代码覆盖关键分支（OCR/纯文本路径、配置回退路径）
- 无 CRITICAL 或 HIGH 级别的代码审查问题
