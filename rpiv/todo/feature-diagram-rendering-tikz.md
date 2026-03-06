---
title: "解题图形渲染能力（TikZ + JSXGraph）"
type: feature
status: open
priority: medium
created_at: 2026-03-03T00:30:00
updated_at: 2026-03-03T00:30:00
---

# 解题图形渲染能力（TikZ + JSXGraph）

## 动机与背景

解题输出中涉及几何、物理（力学/电路）等科目时，需要配图讲解。LLM 本身不能直接"画图"，需要通过结构化输出 + 前端/后端渲染的方式生成图形。

## 期望行为

1. LLM 解题时同时输出：
   - 解题文本（Markdown + LaTeX 公式）
   - 图形描述（TikZ 代码或 JSON schema）
2. 后端编译 TikZ → PDF → SVG，返回图片 URL
3. 前端用 KaTeX 渲染公式，用图片/JSXGraph 渲染图形
4. 学生可以交互式查看图形（JSXGraph 支持拖动辅助理解）

## 用户场景

1. 学生上传一道几何题，解答中包含三角形示意图和辅助线标注
2. 学生上传一道物理力学题，解答中包含力的分解图
3. 学生上传一道电路题，解答中包含电路图

## MVP 定义

1. LLM 解题 prompt 支持输出 TikZ 图形代码（用固定标记块包裹，如 `tikz ... `）
2. 后端 TikZ 编译服务：TikZ → PDF → SVG（使用 Tectonic 或 LuaTeX）
3. 编译结果按题目文本 hash 缓存，避免重复编译
4. 编译失败时降级到 JSXGraph 渲染简化版图形
5. 前端 KaTeX 渲染公式

## 技术方案参考

### 推荐架构

```
拍照 → Gemini Flash OCR → 题目文本
                ↓
        LLM 解题（输出两部分）
        ├── 解题文本（Markdown + LaTeX 公式）
        └── TikZ 图形代码
                ↓
    ┌───────────┬──────────────┬──────────┐
前端 KaTeX    后端 TikZ 编译    缓存层
渲染公式    TikZ→PDF→SVG/PNG   （题目hash）
                    ↓
              返回图片 URL
```

### 关键设计要点

1. **预定义图形类型的 JSON schema**：几何（点线面角）、力学（物体+力箭头）、电路（元件+连线）、函数图像（表达式+定义域），每类一套 schema，LLM 按 schema 填数据
2. **前端用 JSXGraph**：专门为数学教育设计，支持交互式几何、函数图像，体积小（~200KB），学生可拖动图形辅助理解
3. **公式渲染用 KaTeX**：比 MathJax 快很多，适合实时渲染
4. **Prompt 设计是关键**：system prompt 中明确约束 LLM 输出格式，用 few-shot 示例稳定输出质量

### TikZ 编译实现细节

1. **输出格式约束**：system prompt 中要求 LLM 把 TikZ 代码放在固定标记块内，同时限定可用的 TikZ 库白名单
2. **TikZ → SVG 而不是 PNG**：用 pdf2svg 转换，SVG 在前端缩放不失真
3. **模板化 prompt 分学科管理**：几何题、力学题、电路题各一套 few-shot 示例
4. **编译失败的降级策略**：TikZ 重试也失败，降级到 JSXGraph 渲染简化版图形
5. **缓存**：按题目文本 hash 缓存编译好的 SVG

### 编译延迟优化

- 原始 LaTeX 编译一张图 2-5 秒，用 Tectonic 或 LuaTeX 替代传统 pdflatex
- 首次编译后 format 文件缓存，后续编译可压到 500ms 以内
- 部署多个编译 worker，用消息队列异步处理
- 前端先展示文字解答，图形渲染好了再补上

### Docker 环境

```dockerfile
FROM alpine:latest
RUN apk add texlive texmf-dist-latexextra texmf-dist-pictures
# 只装需要的包：tikz, circuitikz, pgfplots, tikz-optics
```

镜像约 2-4GB，只需部署一次。也可用在线编译服务（LaTeX.Online API、Overleaf API）。

### 成本估算

TikZ 编译本身几乎没有额外 API 成本，只是服务器算力。一个 2 核 4G 的容器每秒能编译 2-3 张图。主要成本在 LLM 调用上——要求模型同时输出解题步骤和 TikZ 代码，output token 会多 30-50%。

## 备选方案

- **方案一**：LLM 直接生成 SVG（简单但复杂图形容易出错）
- **方案二**：LLM 生成 JSON → JSXGraph/GeoGebra 渲染（最可控，推荐 MVP 先做此方案）
- **方案三**：LLM 生成 TikZ → 后端编译（最佳效果，作为进阶方案）

## 参考

- 对话记录：https://claude.ai/share/c021a8e2-7d5b-4c88-bf03-a77ef728a39f
- 渲染库：GeoGebra API（几何最强，开源可嵌入）、JSXGraph（轻量级几何，~200KB）、Manim（动画库，适合视频）、Desmos API（函数图像）
- 编译工具：Tectonic、pdf2svg、node-latex
