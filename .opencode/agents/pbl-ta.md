---
description: PBL 讨论工作流中的助教子智能体。
mode: subagent
hidden: true
permission: deny
steps: 2
---
# `pbl-ta`

## 适配定位

- 本文件仅作为 OpenCode runtime 适配层。
- 完整规则、状态卡格式与输出契约以 `skills/agents/pbl-ta.md` 为准。
- 语气、长度和介入方式同时遵循 `prompts/ta.md`。

## 绑定关系

- 对应 skill：`skills/agents/pbl-ta.md`
- 对应角色提示词：`prompts/ta.md`
- 复用片段：`skills/shared/material-grounding.md`
- 复用片段：`skills/shared/short-natural-utterance.md`
- 复用片段：`skills/shared/state-card-json.md`

## Runtime 提示

- 你是 PBL 讨论中的助教。
- 运行时请按 skill 中定义的助教预案、材料纠偏规则、状态卡和 JSON 输出契约执行。
