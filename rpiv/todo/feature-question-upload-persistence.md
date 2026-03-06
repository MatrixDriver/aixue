---
title: "题目上传内容持久化存储（Cloudflare R2 方案）"
type: feature
status: open
priority: medium
created_at: 2026-03-03T00:00:00
updated_at: 2026-03-03T22:40:00
---

# 题目上传内容持久化存储（Cloudflare R2 方案）

## 动机与背景

当前用户上传的题目（文本、照片）在处理后没有持久化保存，图片存在本地 `/app/uploads`，Railway 容器重建后会丢失。需要将原始上传内容和结构化题目数据都可靠地保存下来，以便后续查看历史题目、学情分析、错题回顾等场景使用。

## 技术决策

**图片存储：Cloudflare R2**（2026-03-03 确认）

选择理由：
- 免费额度完全覆盖个人项目需求（10GB 存储 + 100 万次写入/月 + 1000 万次读取/月）
- 零出口费用（不像 S3 按流量收费）
- 已有 R2 账号和密钥（见密钥文件）
- 比 Railway Volume（$0.25/GB/月、单 region、重建风险）更可靠且更便宜

**元数据存储：现有 PostgreSQL**（Railway 托管，无额外成本）

## 架构设计

```
用户上传图片 → FastAPI 后端
  ├─ 图片 → Cloudflare R2（对象存储，S3 兼容 API）
  │    key 格式: uploads/{user_id}/{session_id}/{timestamp}_{hash}.{ext}
  └─ 元数据 → PostgreSQL（已有）
       - solving_sessions.image_path → 改存 R2 object key
       - messages.image_path → 改存 R2 object key
       - 新增字段：original_filename, file_size, content_type
```

读取流程：
- 后端生成 R2 presigned URL 返回前端（有效期可控）
- 或后端代理读取后返回（适合内网场景）

## 期望行为

1. 用户上传题目（文本输入或拍照上传）后，系统保存原始上传内容：
   - 文本题目：保存原始文本到 PostgreSQL
   - 图片题目：保存原始图片到 Cloudflare R2，元数据存 PostgreSQL
2. 经 OCR/解析处理后，保存结构化的题目数据（题干、选项、科目、知识点等）
3. 用户可查看历史上传的题目记录

## 用户场景

1. 学生拍照上传一道数学题，系统保存照片原图到 R2 和识别后的结构化题目到 DB，后续可在"我的题目"中查看
2. 学生手动输入一道英语题，系统保存原始文本和解析后的结构化数据
3. 学情诊断模块从已保存的结构化题目中提取知识点分布，进行弱项分析

## MVP 定义

1. 集成 Cloudflare R2：使用 boto3（S3 兼容）上传图片，存储 object key 到数据库
2. 改造现有上传流程：`/api/solve` 接收图片后先存 R2，再进行 OCR 处理
3. 结构化题目存储：将解析后的题目信息（题干、选项、答案、科目、知识点标签）保存到 PostgreSQL
4. 提供基础的题目列表和图片访问接口（presigned URL 方式）
5. 环境变量：`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`

## 实施要点

- 依赖：`boto3`（S3 兼容 SDK，同时支持 R2）
- R2 endpoint 格式：`https://{account_id}.r2.cloudflarestorage.com`
- 现有 `solving_sessions` 和 `messages` 表的 `image_path` 字段语义从本地路径改为 R2 object key
- 需要数据迁移：已有的本地图片迁移到 R2（如果有的话）
- 前端图片展示改为通过 presigned URL 或后端代理获取

## 参考

- 对话记录：https://claude.ai/share/c021a8e2-7d5b-4c88-bf03-a77ef728a39f
- 缓存机制关联：题目持久化存储可与缓存机制结合——对识别出的题目文本做 hash，命中缓存直接返回，省掉重复调用
- 批量处理关联：用户一次拍一整页多道题时，先整页 OCR 一次，切割出各题文本，再逐题送解题模型
