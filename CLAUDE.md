# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AIXue（爱学）— AI 辅助学生学习的教育项目，面向初中和高中学生。

核心功能：
- 智能解题：上传题目，获取高质量解题思路
- 学情诊断：分析答题情况，识别弱项，给出针对性强化建议

## 技术栈

- 主语言：Python（基于 .gitignore 配置）
- 包管理器：uv（遵循全局规范）
- 虚拟环境：.venv/

## 仓库信息

- 主分支：master
- 远程源：GitHub (zhuqingxun/aixue) + Gitee (sean515/aixue)
- 推送时需同步两个远程源

## 开发命令

项目尚在初始化阶段，以下为预期命令模式：

```bash
# 依赖安装
uv sync

# 运行应用（待确定框架后更新）
uv run python -m aixue

# 运行测试
uv run pytest

# 类型检查
uv run mypy .
```

## 代码规范

- 所有注释和文档使用中文
- 变量名和函数名使用英文
- Python 代码使用类型提示，遵循 PEP 8
