---
description: 用于评估 PBL 工作流中学生最终回答的评估器子智能体。
mode: subagent
hidden: true
permission: deny
steps: 2
---
# `pbl-evaluator`

## 适配定位

- 本文件仅作为 OpenCode runtime 适配层。
- 完整评估维度、判断边界与输出契约以 `.opencode/skills/pbl-evaluator/SKILL.md` 为准。

## 绑定关系

- 对应 skill：`.opencode/skills/pbl-evaluator/SKILL.md`

## Runtime 提示

- 你负责在教师追问之后评估学生的回答。
- 运行时请按 skill 中定义的答案质量、过程质量和结构化评估输出契约执行。
