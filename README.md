# pbl-multi-agent

这是一个项目内使用的 OpenCode 试验场，用于演示原生 PBL 风格的多智能体研讨流程。

## 架构

- 主流程完全由 OpenCode 原生编排，不依赖 Python 运行时。
- 由一个主编排 agent 负责协调整体工作流。
- 题目确定后会先由专门的材料搜索 agent 生成一组可互相比较、甚至互相冲突的材料包，再进入讨论。
- 多个角色子 agent 负责生成实际发言，对话轮次灵活，通常目标为 10 轮以上，而不是只有几次很长的发言。
- 主持人与评估器也分别由独立子 agent 承担，而不是写死在逻辑中。
- 编排器会维护隐藏的讨论状态，例如观点变化、分歧程度和发言意愿。

## 目录结构

- `skills/agents/`：规范化单一事实源；每个 agent 的职责、规则、状态契约与运行时镜像参考都定义在这里
- `skills/shared/`：学生、同伴等角色共用的提示词复用片段
- `.opencode/agents/`：OpenCode runtime agent 适配层，包括编排器、材料搜索、教师、学生、助教、同伴、主持人、总结器和评估器
- `.opencode/commands/`：项目内斜杠命令适配层，例如 `/pbl`
- `prompts/`：角色提示词与语气说明的辅助文档层
- `archive/legacy-root/`：已归档的 Python 原型运行时（`src/`、`skills/`）
- `archive/legacy-opencode/`：已归档的 OpenCode skill 原型文件与生成依赖
- `archive/legacy-root/data/sessions/`：已归档的示例 session 数据

## 提示词组织

- 现在采用 skill-first 架构：`skills/agents/` 是唯一应优先维护的主源。
- skill 文档首先描述角色职责、可见信息、行为规则、状态卡与输出契约，而不是把 `.opencode/` 当作主要生成目标。
- `.opencode/agents/`、`.opencode/commands/` 和 `prompts/` 是运行时适配或辅助文档层，服务于当前 OpenCode 目录组织。
- 学生、`peer_high`、`peer_low`、助教这类讨论参与者的共性要求继续抽到 `skills/shared/` 中，便于复用与比对。
- 若修改了 `skills/agents/` 中的核心规则，应同时核对对应的 `.opencode/` 与 `prompts/` 文件是否仍保持一致。
- 这样既能保证运行时功能不受影响，也能把“单一事实源”稳定收敛到 skill 层。

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

- 讨论转录可见性：
  - 编排器会直接在终端输出完整对话记录。
  - 当前运行过程会同步镜像到 `data/transcripts/latest.md`。
  - 每次运行还会在 `data/transcripts/` 下创建一个新的时间戳转录文件，因此旧记录会被保留。

## Agent 拓扑

- 主编排器：
  - `pbl-orchestrator`
- 材料搜索子 agent：
  - `pbl-material-researcher`
- 角色子 agent：
  - `pbl-teacher`
  - `pbl-student`
  - `pbl-ta`
  - `pbl-peer-high`
  - `pbl-peer-low`
- 控制类子 agent：
  - `pbl-moderator`
  - `pbl-summarizer`
  - `pbl-evaluator`

## 讨论流程

当前原生 OpenCode 工作流遵循 `plan.txt` 中定义的业务流程：

1. 教师选择或细化讨论主题。
2. 材料搜索 agent 在网上或可用知识源中整理 5 到 7 条材料，形成材料包。
3. 教师结合近期教学内容给出引导，并把讨论锚定到材料。
4. 学生先基于材料给出初始看法。
5. 学生、同伴和助教围绕材料展开自适应讨论，主持人根据最新内容、分歧、发言意愿、材料覆盖深度与公平性逐轮决定下一位发言者。
6. 学生主动结束讨论。
7. 教师提出 1 到 3 个追问。
8. 学生作答。
9. 评估器审查学生回答。
10. 教师给出最终点评。

## 说明

- 主流程现在由原生 OpenCode 与多个子 agent 协同完成。
- 默认运行方式经过优化，尽量在一次 assistant 响应中完成整场讨论，以减少步骤消耗。
- 材料包默认要求 5 条以上短材料，每条控制在 200 到 400 字，并尽量保留差异、张力与冲突。
- 后续讨论默认要求引用、比较、误读、纠偏或综合这些材料，而不是只做抽象观点交换。
- 主题选择现在优先人文社科方向，包括有争议的事件、公共议题和带有解释空间的时事新闻。
- 学生和同伴现在具有动态观点状态，因此他们可能被说服、部分修正，或继续坚持正确/错误观点。
- `peer_high` 更倾向于质疑不充分的解释，`peer_low` 更倾向于给出较简单甚至有误的看法，从而触发澄清。
- 评估器现在同时评估最终回答质量与整个讨论过程质量。
- 旧版 Python 与 OpenCode skill 原型已经归档到 `archive/` 下，不再属于当前活跃运行路径。
