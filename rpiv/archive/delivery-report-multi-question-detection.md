---
description: "交付报告: multi-question-detection"
status: archived
created_at: 2026-03-07T22:55:00
updated_at: 2026-03-07T22:55:00
archived_at: null
related_files:
  - rpiv/requirements/prd-multi-question-detection.md
  - rpiv/plans/plan-multi-question-detection.md
  - rpiv/validation/code-review-multi-question-detection.md
  - rpiv/validation/test-strategy-multi-question-detection.md
  - rpiv/validation/test-specs-multi-question-detection.md
---

# 交付报告: 多题图片智能识别与选题

## 完成摘要

- **PRD 文件**: rpiv/requirements/prd-multi-question-detection.md
- **实施计划**: rpiv/plans/plan-multi-question-detection.md
- **测试覆盖**: 116 个测试全部通过（含 8 个新增单元测试 + 3 个新增集成测试）
- **代码审查**: 0 critical / 0 high / 4 medium / 4 low

### 代码变更

**后端（3 文件修改）：**
- `src/aixue/schemas/session.py` — 新增 `QuestionInfo` + `DetectResponse` Pydantic 模型
- `src/aixue/services/ocr_service.py` — 新增 `MULTI_QUESTION_DETECTION_PROMPT` + `detect_questions()` + `_parse_detection_result()`
- `src/aixue/api/endpoints/solver.py` — 新增 `/detect` 端点

**前端（7 文件，含 1 个新建）：**
- `frontend/src/lib/types.ts` — Message 扩展 type/questionOptions + 新增 QuestionOption/DetectResponse
- `frontend/src/lib/api.ts` — 新增 `detectQuestions()` API 函数
- `frontend/src/components/chat/question-selector.tsx` — **新建**选题按钮组组件
- `frontend/src/components/chat/chat-message.tsx` — 条件渲染选题按钮组
- `frontend/src/components/chat/chat-container.tsx` — 传递选题回调 props
- `frontend/src/hooks/use-chat.ts` — sendMessage 改造 + selectQuestion/selectAll 回调
- `frontend/src/app/(main)/solve/page.tsx` — 传递新 props

**测试（2 文件，含 1 个新建）：**
- `tests/test_services/test_ocr_detect.py` — **新建** 8 个单元测试
- `tests/test_api/test_solver.py` — 新增 3 个集成测试

**QA 补充测试（2 文件新建）：**
- `tests/test_services/test_multi_question_flow.py` — 服务层补充测试
- `tests/test_api/test_detect.py` — API 端点补充测试

## 关键架构决策

1. **独立 `/detect` 端点**（不修改 `/solve`）：职责单一，不改变现有语义
2. **前端驱动逐题调用**：每题复用 `/solve` + user_hint，逐题展示结果体验更好
3. **检测结果不持久化**：仅前端内存暂存（pendingImage + questionOptions），无业务价值需持久化
4. **JSON 三级容错**：直接解析 → 正则提取 → 回退单题流程

## 代码审查遗留问题（均为 medium/low，建议后续迭代修复）

- M1: `_parse_detection_result` 中 `import json/re` 应移到文件顶部
- M2: 贪婪正则 `\{[\s\S]*\}` 在多 JSON 对象时可能匹配过多
- M3: `/detect` 端点每次请求创建 LLMService + OCRService 实例
- M4: 单题快速通道条件 `completeQuestions.length === 1 && question_count <= 1` 边界情况
- L1: `HTTP_413_REQUEST_ENTITY_TOO_LARGE` 已弃用，应使用 `HTTP_413_CONTENT_TOO_LARGE`
- L2: setState 闭包可能引用过时状态
- L3: 全部解答串行无进度反馈
- L4: React key 使用 Date.now() 存在理论冲突

## 建议后续步骤

1. 部署到线上环境验证端到端功能
2. 修复 medium 问题（特别是 M2 正则和 M3 实例化）
3. 实现图片裁剪/校正功能（已在 todo 中）
4. 全部解答模式增加逐题进度反馈
