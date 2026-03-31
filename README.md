# pbl-multi-agent

这是一个项目内使用的 OpenCode 试验场，用于演示原生 PBL 风格的多智能体研讨流程。

## 架构

- 主流程由 OpenCode 原生编排完成，核心讨论逻辑维护在标准 skill 目录 `.opencode/skills/` 中。
- `pbl-orchestrator` 负责串联选题、材料包、自由讨论、教师追问与教师终评。
- 题目确定后会先调用 `pbl-material-researcher` 生成可比较、最好带冲突的材料包，再进入讨论。
- 教师、学生、助教、两位同伴、主持人和总结器都以独立子 agent 形式运行。
- 自由讨论按短轮次推进，是否结束由讨论状态而不是固定轮数决定。

## 目录结构

- `.opencode/skills/`：标准 skill 单一事实源；每个 agent 的职责、规则、状态契约与输出契约都定义在这里
- `.opencode/agents/`：OpenCode runtime agent 适配层
- `.opencode/commands/`：项目内斜杠命令适配层，例如 `/pbl`
- `prompts/`：部分角色的语气与表达辅助文档
- `archived/skills-legacy/`：旧 `skills/` 目录的归档镜像，仅用于历史比对，不再作为当前主源
- `plan.txt`：当前工作流阶段与 local-context policy 的简要规划文本

## 提示词组织

- 当前采用标准 skill-first 架构：`.opencode/skills/` 是优先维护的主源。
- skill 文档先定义角色职责、可见信息、行为规则、状态卡与输出契约。
- `.opencode/agents/`、`.opencode/commands/` 和 `prompts/` 主要承担运行时适配或辅助说明，不应先于 skill 修改。
- 讨论参与者的共性要求直接并入各自的 agent skill，避免规则分散在多个共享片段中。
- 原 `skills/` 目录已归档到 `archived/skills-legacy/`，避免丢失任何既有指令，同时不再参与当前架构。
- 修改核心规则后，应同步核对对应的 `.opencode/` 与 `prompts/` 是否仍一致。

## 运行方式

- 在项目根目录启动 OpenCode：

```bash
opencode
```

- 在 OpenCode 界面中直接开始讨论：

```text
/pbl
```

- 或者显式提供一个话题：

```text
/pbl 平台算法是否在重塑公共讨论
```

- 默认以中文运行整场讨论。

## Agent 列表

- `pbl-orchestrator`
- `pbl-material-researcher`
- `pbl-teacher`
- `pbl-student`
- `pbl-ta`
- `pbl-peer-high`
- `pbl-peer-low`
- `pbl-moderator`
- `pbl-summarizer`

## 讨论流程

当前工作流遵循 `plan.txt` 与 `.opencode/skills/pbl-orchestrator/SKILL.md` 中的阶段约束：

1. 教师选择或细化讨论主题。
2. 材料搜索 agent 在网上或可用知识源中整理至少 5 条材料，形成材料包。
3. 教师结合近期教学内容给出引导，并把讨论锚定到材料。
4. 学生先基于材料给出初始看法。
5. 学生、同伴和助教围绕材料展开自适应讨论，主持人根据最新内容、分歧、发言意愿、材料覆盖与问题状态逐轮决定下一位发言者。
6. 自由讨论结束后，教师提出 1 到 3 个追问；其中至少一问推动学生综合本轮研讨中的关键分歧、机制、材料关系或观点变化，但不必直接要求“总结研讨”。
7. 学生集中作答。
8. 教师给出最终点评，并同时评价学生回答质量与整段讨论中的参与表现。

## 说明

- 默认运行方式尽量在一次 assistant 响应中完成整场讨论，以减少步骤消耗。
- 材料包默认要求 5 到 7 条短材料，每条控制在 200 到 400 字，并尽量保留差异、张力与冲突。
- 后续讨论要求围绕材料中的具体内容展开比较、误读、纠偏或综合，而不是只交换抽象观点。
- 主题优先选人文社科方向，包括公共议题、制度问题、历史解释、媒体文化与带争议的时事。
- 学生和同伴具有动态观点状态，可能被说服、部分修正，或继续保留分歧。
- `peer_high` 更倾向于追问机制与边界，`peer_low` 更容易停留在表层或出现误读。
- 教师最终点评同时评估学生最终回答与整段讨论过程。
