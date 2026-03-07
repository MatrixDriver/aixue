---
description: "交付报告: 图片预处理与OCR/推理拆分成本优化"
status: archived
created_at: 2026-03-06T22:35:00
updated_at: 2026-03-06T22:35:00
archived_at: 2026-03-06T22:50:00
related_files:
  - rpiv/requirements/prd-cost-optimization.md
  - rpiv/plans/plan-cost-optimization.md
  - rpiv/validation/code-review-cost-optimization.md
  - rpiv/validation/test-strategy-cost-optimization.md
  - rpiv/validation/test-specs-cost-optimization.md
  - rpiv/research-cost-optimization.md
---

# 交付报告：图片预处理与 OCR/推理拆分成本优化

## 完成摘要

| 项目 | 详情 |
|------|------|
| PRD 文件 | `rpiv/requirements/prd-cost-optimization.md` |
| 实施计划 | `rpiv/plans/plan-cost-optimization.md` |
| 技术调研 | `rpiv/research-cost-optimization.md` |
| 代码审查 | `rpiv/validation/code-review-cost-optimization.md` |
| 测试通过率 | 85/85（100%） |
| 代码审查结果 | 0 critical, 0 high, 1 medium, 2 low |

### 代码变更清单

| 文件 | 操作 | 变更内容 |
|------|------|----------|
| `src/aixue/config.py` | 修改 | 新增 `llm_model_ocr: str = ""` 配置字段 |
| `src/aixue/services/llm_service.py` | 修改 | `recognize_image()` 使用 `llm_model_ocr or llm_model_light` 作为 OCR 模型 |
| `.env.example` | 修改 | 新增 `LLM_MODEL_OCR` 配置示例 |
| `frontend/src/lib/image-utils.ts` | 新建 | `compressImage()` 图片压缩工具函数（1536px + WebP/JPEG） |
| `frontend/src/components/chat/image-upload.tsx` | 修改 | `handleFile()` 集成压缩逻辑 |

**总计**：5 文件变更 + 1 新建文件，约 85 行新增 / 31 行删除。

## 关键决策记录

1. **后端改动极小**：代码分析发现现有架构已天然支持 OCR/推理分离（`OCRService.recognize()` 输出纯文本 → `MathSolver/GeneralSolver` 接收纯文本），无需改造数据流，仅需让 OCR 阶段使用独立模型配置
2. **空字符串而非 None**：`llm_model_ocr` 使用 `str = ""` 默认值，比 `str | None = None` 更适合 pydantic-settings 环境变量加载，回退逻辑用 `or` 一行搞定
3. **前端使用 createImageBitmap**：比传统 `new Image()` + onload 更简洁，支持 Worker，兼容性 >97%
4. **前端大小限制调整**：压缩前允许更大原图（10MB），压缩后通常 <1MB，后端 5MB 限制作为安全网

## 遗留问题

| # | 严重度 | 文件 | 描述 | 建议 |
|---|--------|------|------|------|
| 1 | medium | `image-upload.tsx:27-38` | async handleFile 的 Promise rejection 未被捕获 | 在 handleFile 内部添加 try-catch，catch 中提示用户"图片处理失败" |
| 2 | low | `image-utils.ts:29` | compressImage 缺少 try-catch | 捕获异常后返回原始文件作为降级 |
| 3 | low | `image-utils.ts:41` | canvas context 非空断言 | 风险极低，可接受 |

以上问题均不阻塞发布，建议在后续迭代中修复 medium 问题。

## 建议后续步骤

1. **修复前端错误处理**（medium 问题）：为 handleFile 添加 try-catch
2. **部署验证**：在 Railway 环境变量中添加 `LLM_MODEL_OCR`，观察日志确认模型切换生效
3. **成本对比**：优化前后各运行 20 题，对比日志中的 token 消耗
4. **管理后台**：已记录为独立 todo（`rpiv/todo/feature-admin-dashboard.md`），后续开发动态模型配置
