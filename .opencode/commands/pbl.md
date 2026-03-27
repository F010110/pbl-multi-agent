---
description: 通过原生 OpenCode 多子智能体工作流启动一次完整的 PBL 讨论。
agent: pbl-orchestrator
---
## 适配定位

- 对应 agent：`pbl-orchestrator`
- 对应 skill：`skills/agents/pbl-orchestrator.md`
- 本文件仅作为命令入口适配层。
- 完整执行要求、阶段顺序和输出要求以 `skills/agents/pbl-orchestrator.md` 中的 command mirror 为准。

## 启动说明

以中文启动一场完整的 PBL 讨论。

用户提供的话题覆盖：`$ARGUMENTS`

## Runtime 提示

- 调用 `pbl-orchestrator` 时，按 skill 中定义的完整命令约束执行。
- 话题细化、材料包要求、自由讨论规则、持久化与终端输出要求均以 `skills/agents/pbl-orchestrator.md` 为准。
