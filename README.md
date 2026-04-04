# pbl-multi-agent

这是一个项目内使用的 OpenCode 试验场，用于演示原生 PBL 风格的多智能体研讨流程。

当前目录是实验副本，当前 git 分支为 `realtime-state-experiment`。
这一分支正在试验两条彻底分离的讨论工作流：全自动模式继续采用“每轮后刷新角色状态卡”的编排方式；用户参与模式则把 `student` 的举手、待发言与等待状态下沉到 `pbl_runtime`，由 runtime 作为官方状态源。

## 架构

- 当前主流程仍由 OpenCode 原生编排完成，核心讨论逻辑维护在标准 skill 目录 `.opencode/skills/` 中。
- `pbl-orchestrator` 负责串联选题、材料包、自由讨论、教师追问与教师终评；当前已明确区分两种运行方式，并要求两种模式走各自独立工作流，而不是混在同一条流程里补充例外规则。
- 题目确定后会先调用 `pbl-material-researcher` 生成可比较、最好带冲突的材料包，再进入讨论。
- 在当前已落地的全自动模式中，教师、学生、助教、两位同伴、主持人和总结器都以独立子 agent 形式运行。
- 在规划中的用户参与模式中，`student` 将从“固定子 agent”扩展为“讨论角色 + 运行时控制源”，允许由 agent 或真实用户驱动；moderator 读取的是聚合后的学生发言意愿，而不是只看 `pbl-student` 自身状态。
- 对应地，moderator 也不再只有一套统一输入假设：全自动模式下读取四张角色状态卡，用户参与模式下读取三张 agent 状态卡加一份学生聚合状态，并按各自独立工作流做结束判断与选人。
- 自由讨论按短轮次推进，是否结束由讨论状态而不是固定轮数决定。
- 在本实验分支中，全自动模式下每轮正文发言落盘后，student、ta、`peer_high`、`peer_low` 都会各自再执行一次“只刷新状态卡”的流程；用户参与模式下则只刷新 ta、`peer_high`、`peer_low`，student 是否举手和是否待发言只读取 runtime 聚合状态。
- 为支持后续用户参与模式，项目架构会逐步从“单次命令内跑完整场讨论”扩展为“保留全自动模式，同时增加可接入 GUI 实时输入的会话式运行时”。

## 目录结构

- `.opencode/skills/`：标准 skill 单一事实源；每个 agent 的职责、规则、状态契约与输出契约都定义在这里
- `.opencode/agents/`：OpenCode runtime agent 适配层
- `.opencode/commands/`：项目内斜杠命令适配层，例如 `/pbl-auto`、`/pbl-user`
- `pbl_runtime/`：用户参与式运行时与 Python GUI；负责 session、事件流、状态聚合与本地图形界面
- `prompts/`：部分角色的语气与表达辅助文档
- `data/`：讨论转录，以及后续用户参与式运行时可能使用的会话状态、事件流等持久化数据
- `archived/skills-legacy/`：旧 `skills/` 目录的归档镜像，仅用于历史比对，不再作为当前主源
- `plan.txt`：当前工作流阶段与 local-context policy 的简要规划文本

## 提示词组织

- 当前采用标准 skill-first 架构：`.opencode/skills/` 是优先维护的主源。
- skill 文档先定义角色职责、可见信息、行为规则、状态卡与输出契约。
- `.opencode/agents/`、`.opencode/commands/` 和 `prompts/` 主要承担运行时适配或辅助说明，不应先于 skill 修改。
- 讨论参与者的共性要求直接并入各自的 agent skill，避免规则分散在多个共享片段中。
- 原 `skills/` 目录已归档到 `archived/skills-legacy/`，避免丢失任何既有指令，同时不再参与当前架构。
- 修改核心规则后，应同步核对对应的 `.opencode/` 与 `prompts/` 是否仍一致。
- 角色行为规范仍优先维护在 skill 中；但与“用户是否举手、谁来代表 student 发言、是否等待 GUI 输入”相关的运行时决策，将逐步下沉到更显式的 session/runtime 层，而不继续全部塞进 prompt 契约里。

## 运行方式

当前明确区分两种运行方式：

- 全自动模式：当前已实现，对应命令 `/pbl-auto`；由 OpenCode 调用全部 `pbl-*` 子 agent，完成整场讨论并实时写入转录。
- 用户参与模式：当前作为架构扩展方向预留，对应命令 `/pbl-user`；后续会引入常驻会话运行时和独立 GUI；用户可在讨论进行中随时举手、发言，`student` 角色将支持由 agent 或用户驱动。

- 在项目根目录启动 OpenCode：

```bash
opencode
```

- 在 OpenCode 界面中直接启动一场全自动讨论：

```text
/pbl-auto
```

- 或者显式提供一个话题：

```text
/pbl-auto 平台算法是否在重塑公共讨论
```

- 默认以中文运行整场讨论。
- 当前仓库已把两种模式拆成两个不同命令：`/pbl-auto` 与 `/pbl-user`。
- 当前仓库已提供 `/pbl-user` 所需的本地 runtime/session 与 GUI 原型；但该命令入口本身是否已被当前 assistant 运行链路直接接管，仍取决于运行环境。

### 用户参与式运行时原型

仓库现已提供一个最小可运行的本地 runtime/session 与 Python GUI 原型，作为 `/pbl-user` 的配套基础设施：

```bash
python3 -m pbl_runtime.cli bootstrap --topic "平台算法是否在重塑公共讨论"
python -m pbl_runtime.cli init --topic "平台算法是否在重塑公共讨论"
python -m pbl_runtime.cli run
python -m pbl_runtime.cli gui
python3 -m pbl_runtime.cli ensure-services --session-id <id>
python3 -m pbl_runtime.cli select-student --session-id <id> --prompt "请回应刚才关于平台激励机制的说法"
python3 -m pbl_runtime.cli submit-student --session-id <id> --text "我觉得平台并不只是放大情绪，它也在筛选能快速传播的表达。"
python3 -m pbl_runtime.cli wait-student --session-id <id>
python3 -m pbl_runtime.cli consume-student --session-id <id>
python3 -m pbl_runtime.cli resume-info --session-id <id>
python3 -m pbl_runtime.cli phase --session-id <id> --phase free_discussion
python3 -m pbl_runtime.cli checkpoint --session-id <id> --checkpoint waiting_for_student_turn --waiting-reason awaiting_student_utterance
python3 -m pbl_runtime.cli init-transcripts --session-id <id>
python3 -m pbl_runtime.cli append-public --session-id <id> --markdown "## 教师\n\n今天我们讨论..."
python3 -m pbl_runtime.cli complete-session --session-id <id>
```

- `bootstrap`：创建 session，并在后台启动 runtime 与 GUI
- `init`：创建一个新的用户参与式 session，并写入 `data/runtime/`
- `run`：持续轮询并消费 GUI 或其他适配器投递到 inbox 的事件
- `gui`：启动本地 `tkinter` GUI，支持学生举手、放下手，并在被选中发言后显示提示
- `ensure-services`：确认 runtime 与 GUI 后台进程仍在运行；若已退出则自动重启
- `select-student`：把“已选中发言”状态同步给 GUI
- `submit-student`：把学生在对话界面中的 `/pbl-say ...` 正文写入当前 session
- `wait-student`：阻塞等待学生输入正文
- `consume-student`：在编排器读取正文后安全清空待消费状态
- `resume-info`：读取可恢复推进所需的 session / runtime / checkpoint 概览
- `phase`：写回当前讨论阶段，便于 `/pbl-user` 恢复时继续推进
- `checkpoint`：写回编排器恢复点、等待原因和转录路径
- `init-transcripts`：初始化本次运行的单次转录与 `data/transcripts/latest.md`
- `append-public`：把新的公开内容实时追加到两份转录文件
- `complete-session`：在本轮讨论结束后把 session 标记为完成，并清空 `current_session.txt`，避免下一轮误续上一次会话

当前嵌入方式按用户参与模式约定如下：

- 在学生首次发言开始前，先启动本地 runtime 与 GUI
- 每次恢复 `/pbl-user` 会话前，先确认 runtime 与 GUI 后台 Python 进程仍在运行；若已退出则自动重启
- moderator 持续读取 runtime 聚合状态中的学生举手信息，而不是等待聊天命令
- 当 moderator 选中 `student` 为下一位发言者时，运行时把“已选中发言”的提示同步给 GUI，并进入等待学生输入状态
- GUI 当前只承担举手与状态提示职责；学生正文直接通过对话界面的 `/pbl-say ...` 提交；GUI 暂不展示完整研讨记录

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
5. 学生、同伴和助教围绕材料展开自适应讨论；全自动模式下，每轮先生成一位角色的正文发言，再刷新 student、ta、`peer_high`、`peer_low` 的最新状态卡，主持人随后根据这四张最新状态卡、材料覆盖与问题状态决定下一位发言者；用户参与模式下，每轮先落盘正文，再刷新 ta、`peer_high`、`peer_low` 的最新状态卡，并由 moderator 结合 runtime 中学生角色的聚合状态决定下一位发言者。
6. 自由讨论结束后，教师提出 1 到 3 个追问；其中至少一问推动学生综合本轮研讨中的关键分歧、机制、材料关系或观点变化，但不必直接要求“总结研讨”。
7. 学生集中作答。
8. 教师给出最终点评，并同时评价学生回答质量与整段讨论中的参与表现。

用户参与模式落地后，整体阶段顺序仍保持一致，但会由独立的用户参与式工作流负责推进；不会在当前全自动工作流的步骤里夹杂“若有用户则改走另一条路”的例外分支。

## 说明

- 全自动模式下，默认尽量在一次 assistant 响应中完成整场讨论，以减少步骤消耗。
- 由于本分支在全自动模式中额外加入了“每轮后全员状态刷新”，该模式下自由讨论阶段的调用量和等待时间都会高于主分支；用户参与模式的额外成本则主要来自 runtime 等待与恢复。
- 材料包默认要求 5 到 7 条短材料，每条控制在 200 到 400 字，并尽量保留差异、张力与冲突。
- 后续讨论要求围绕材料中的具体内容展开比较、误读、纠偏或综合，而不是只交换抽象观点。
- 主题优先选人文社科方向，包括公共议题、制度问题、历史解释、媒体文化与带争议的时事。
- 学生和同伴具有动态观点状态，可能被说服、部分修正，或继续保留分歧。
- `peer_high` 更倾向于追问机制与边界，`peer_low` 更容易停留在表层或出现误读。
- 教师最终点评同时评估学生最终回答与整段讨论过程。
- 用户参与模式的目标不是打断现有全自动模式，而是在保留现有 skill 角色分工的前提下，把 `student` 从固定 agent 扩展为可由 agent 或用户控制的讨论角色，并让 moderator 基于统一的举手/发言状态做选人。
