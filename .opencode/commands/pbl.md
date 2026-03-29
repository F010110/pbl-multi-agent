---
description: 通过原生 OpenCode 多子智能体工作流启动一次完整的 PBL 讨论。
agent: pbl-orchestrator
---
## 适配定位

- 本文件仅作为命令入口适配层。
- 完整执行要求、阶段顺序和输出要求以 `.opencode/skills/pbl-orchestrator/SKILL.md` 为准。

## 绑定关系

- 对应 agent：`pbl-orchestrator`
- 对应 skill：`.opencode/skills/pbl-orchestrator/SKILL.md`

## Runtime 提示

- 以中文启动一场完整的 PBL 讨论。
- 用户提供的话题覆盖：`$ARGUMENTS`
- 调用 `pbl-orchestrator` 时，按 skill 中定义的完整命令约束执行。
