# AIXue 行业调研报告

> 调研时间：2026-03-02
> 调研范围：竞品分析、技术方案、开源项目

---

## 一、竞品分析

### 产品矩阵

| 产品 | 公司 | 市场 | 核心定位 |
|------|------|------|----------|
| Photomath | Google | 全球 | 数学拍照解题，动画教程（付费） |
| Gauth | 字节跳动 | 海外 | 全科 AI 助手，AI Live Tutor + 白板 + 视频 |
| Question.ai | 作业帮 | 海外 | 全科解题，19 亿题库 |
| Wolfram Alpha | Wolfram | 全球 | 精确计算引擎，零幻觉 |
| Khanmigo | Khan Academy | 全球 | 苏格拉底式 AI 辅导，$4/月 |
| 学而思 | 好未来 | 中国 | 九章大模型 + DeepSeek，免费 |
| 小猿 AI | 猿辅导 | 中国 | 五重错因分析，DeepSeek + 自研模型 |
| 作业帮 | 作业帮 | 中国 | 拍照搜题 + AI 辅导，19 亿题库 |
| 豆包爱学 | 字节跳动 | 中国 | 1v1 AI 讲题 + 动态板书 + 虚拟实验 |

### 关键能力对比

**拍照识别**：学而思九章识题（手写体最优）> 小猿/作业帮 > Gauth/Photomath。几何图形识别仍是全行业薄弱环节。

**解题输出**：
- 纯文字分步骤：所有产品标配
- 动画/白板：Gauth（实时白板）、豆包（动态板书）、Photomath（动画教程）
- 视频讲解：学而思（2.5 亿分钟）、小猿（3 亿覆盖）
- 语音讲解：Gauth、豆包（实时语音互动）

**对话式辅导**：Khanmigo（苏格拉底式引导，核心设计）> 学而思（无限追问）> 小猿/豆包 > Photomath（无追问）

**学情管理**：小猿（五重错因分析）> 豆包（遗忘曲线 + 知识图谱）> 学而思 > Gauth > Photomath（无）

### 行业演进路径

```
拍照搜题 (1.0) → 分步解析 (2.0) → 对话式辅导 (3.0) → AI 1v1 个性化教师 (4.0)
```

当前行业从 3.0 向 4.0 过渡，学而思、小猿、Gauth 走在前列。

### 全行业共性痛点

1. **AI 幻觉**：解题过程中出错，对学生误导成本极高
2. **几何图形识别**：全行业薄弱环节
3. **浅层交互**：多数仍停留在"给答案"而非"教思考"
4. **过度依赖风险**：学生可能沦为抄答案

### 中外产品差异

- **中国产品**：学情管理闭环强（错题本 + 诊断 + 推荐 + 复习），题库规模大，与 K12 课程体系绑定
- **海外产品**：单点极致（Photomath 动画、Khanmigo 教育理念、Wolfram 计算精度），更偏"教会思考"

---

## 二、技术方案

### 2.1 数学 OCR

| 方案 | 类型 | 公式准确率 | 几何图形 | 中文 | 成本 |
|------|------|-----------|---------|------|------|
| Mathpix | 商业 | 最高 | 不支持 | 支持 | 付费 |
| Mistral OCR 3 | 商业 | 极高 | 有限 | 支持 | 付费 |
| Pix2Text | 开源 | 高（SOTA） | 不支持 | 优秀 | 免费 |
| LaTeX-OCR | 开源 | 高 | 不支持 | 有限 | 免费 |
| 多模态 LLM | API | 高 | 支持 | 支持 | 按 token |

**几何图形识别**前沿：Geo-LLaVA（平面 + 立体几何）、DFE-GPS（SigLIP 视觉编码器）、MATHVERSE/Tangram 基准测试。

### 2.2 大模型数学推理（AIME 2025 基准）

| 模型 | AIME 2025（无工具） | 有工具 |
|------|---------------------|--------|
| GPT-5.2 | ~95%+ | 100% |
| Gemini 3 Pro | 95% | 100% |
| GPT-5 | 94.6% | - |
| Claude Sonnet 4.5 | 87% | 100% |
| Claude Sonnet 4 (Thinking) | 76.3% | - |
| DeepSeek-R1 | 79.8% (AIME 2024) | - |

- K12 数学：当前主流模型已能处理绝大多数高中及以下难度
- 竞赛级别：需带推理能力的模型（Thinking 模式、o1、DeepSeek-R1）
- MATH 基准已接近天花板（97%+），AIME 成为新的区分基准

### 2.3 数学推理验证

| 验证层级 | 技术方案 | 适用场景 | 实时性 |
|----------|----------|----------|--------|
| 第一层 | SymPy 数值验证 | 代数/计算题答案校验 | 毫秒级 |
| 第二层 | 多模型交叉验证 | 不同 LLM 分别解题并比对 | 秒级 |
| 第三层 | LLM + CAS 混合 | AI 生成步骤 + SymPy 验证每步 | 秒级 |
| 第四层 | Lean 4 形式化 | 竞赛级/研究级证明 | 分钟级 |

- **SymPy**：非常成熟，陶哲轩基于 SymPy 构建证明验证助手
- **Lean 4**：mathlib 已形式化 210,000+ 条定理；DeepSeek-Prover-V2 专为 Lean 4 设计
- **Safe 框架**：将 LLM 的 CoT 每步翻译为 Lean 4 验证，失败即标记为幻觉

### 2.4 学情诊断 / 知识追踪

**经典模型**：BKT（可解释性强）→ DKT（RNN）→ AKT（Transformer）→ 图神经网络（2025 年占比 26.2%，最多）

**最新方向**：
- 图神经网络 + 混合/元学习是主流（占比 50%）
- L-HAKT：LLM + 双曲空间的知识追踪
- LLM 直接做知识追踪仍不成熟（FoundationalASSIST 评测显示仅达基线水平）
- 可解释性是合规硬性要求（欧盟 AI 法案 2026 年 8 月执行）

**认知诊断**：NeuralCD（准确性 + 可解释性平衡）、EduCDM（开源实现库）

### 2.5 中文数学题库资源

| 数据集 | 规模 | 覆盖 | 特点 |
|--------|------|------|------|
| CMM-Math | 28K+ | 小学至高中 | 多模态，含选择/填空/分析题 |
| CMMaTH | 23,856 | K12 多模态 | 最大中文多模态数学评测基准 |
| TAL-SCQ5K-CN | 5K | 小/初/高竞赛 | 好未来出品，LaTeX 格式 |
| Math23K | 23,162 | 应用题 | 中文数学应用题 |

---

## 三、开源项目

### 核心推荐（按 AIXue 模块）

#### 端到端系统架构

| 项目 | Stars | 参考价值 | 要点 |
|------|-------|---------|------|
| [DeepTutor](https://github.com/HKUDS/DeepTutor) | 10.5K | 极高 | RAG + 知识图谱 + 多 Agent + 会话级知识追踪 + 自适应练习 |
| [OATutor](https://github.com/CAHLR/OATutor) | 170 | 高 | BKT 学情评估 + 自适应题目选择，CHI 2023 论文 |
| [Mr. Ranedeer AI Tutor](https://github.com/JushBJJ/Mr.-Ranedeer-AI-Tutor) | 29.7K | 极高 | 纯 Prompt 方案，分级教学 + 苏格拉底式引导的 Prompt 标杆 |

#### 数学 OCR

| 项目 | Stars | 参考价值 | 要点 |
|------|-------|---------|------|
| [Pix2Text](https://github.com/breezedeus/Pix2Text) | 3K | 极高 | 中文优秀、轻量、版面分析一体化，Mathpix 开源替代 |
| [LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) | 16.2K | 高 | ViT 架构，公式识别专精 |
| [Surya](https://github.com/datalab-to/surya) | 19.4K | 高 | 全页面 OCR，90+ 语言，整页试卷处理 |

#### Manim 动画生成

| 项目 | Stars | 参考价值 | 要点 |
|------|-------|---------|------|
| [ManimCommunity](https://github.com/ManimCommunity/manim) | 37K | 极高 | 首选渲染引擎，文档完善 |
| [Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim) | 1.7K | 极高 | 反向知识树算法，LLM→Manim 完整 Pipeline |
| [Generative Manim](https://github.com/marcelo-earth/generative-manim) | 801 | 高 | 多引擎评估框架，code-writer + reviewer 反馈循环 |
| [topic2manim](https://github.com/mateolafalce/topic2manim) | 16 | 中高 | 端到端：脚本→Manim→TTS→FFmpeg，多 Agent 架构 |

#### 知识追踪

| 项目 | Stars | 参考价值 | 要点 |
|------|-------|---------|------|
| [pyKT](https://github.com/pykt-team/pykt-toolkit) | 354 | 极高 | 10+ 模型统一实现，7+ 数据集，NeurIPS 2022 |
| [EduCDM](https://github.com/bigdata-ustc/EduCDM) | - | 高 | 认知诊断模型库（IRT/DINA/NeuralCDM） |

---

## 四、对 AIXue 的启示

### 产品层面

1. **苏格拉底式引导是行业共识方向**：Khanmigo 和学而思都以此为核心设计
2. **学情闭环是国内用户强需求**：错题本 + 遗忘曲线 + 个性化推荐
3. **多模态输出是趋势**：文字 + 语音 + 白板/动画，Gauth 和豆包走在前列
4. **AI 幻觉是教育场景的信任基础**：必须有验证机制

### 技术层面

1. **数学 OCR**：多模态 LLM 端到端处理为主，Pix2Text 作为补充
2. **解题引擎**：Claude Sonnet 4.6 / GPT-5 级别模型 + SymPy 验证
3. **学情追踪**：pyKT (simpleKT/AKT) 快速起步 + NeuralCD 认知诊断
4. **题库**：CMM-Math + TAL-SCQ5K-CN 打底 + LLM 生成变式题（CAS 验证）
5. **Manim 动画**（后续版本）：ManimCommunity + Math-To-Manim 的 Pipeline 参考

### 关键开源项目清单

| 优先级 | 项目 | 用途 |
|--------|------|------|
| P0 | DeepTutor | 系统架构参考 |
| P0 | Mr. Ranedeer | Prompt 设计参考 |
| P0 | Pix2Text | 数学 OCR |
| P0 | pyKT | 学情追踪模型 |
| P1 | ManimCommunity | 动画引擎 |
| P1 | Math-To-Manim | LLM→Manim Pipeline |
| P1 | OATutor | 自适应辅导逻辑 |
| P2 | EduCDM | 认知诊断模型 |
