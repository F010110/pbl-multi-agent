---
description: 启动用户参与式 PBL 讨论工作流入口。
agent: pbl-orchestrator
---
## 适配定位

- 本文件是 `/pbl-user` 的命令入口。
- 本命令只覆盖用户参与模式。
- 它对应 `.opencode/skills/pbl-orchestrator/SKILL.md` 中的 `User-Participatory Workflow`，并要求由独立 session/runtime 与 GUI 输入通道承载用户举手和状态聚合；学生正文通过对话命令 `/pbl-say` 提交。
- 本命令采用“文件桥接 + 可恢复推进”模式：GUI 与 runtime 持续把状态写入 `data/runtime/`，编排器在关键节点主动读取这些文件并在多次 assistant 调用之间恢复会话。

## 运行要求

- 以中文启动一场用户参与式 PBL 讨论。
- 用户提供的话题：`$ARGUMENTS`
- 若本次未提供新话题，只有在用户明确表达“继续当前会话”时，才恢复 `data/runtime/current_session.txt` 指向的最近一次未完成 session；否则应先清空上一轮遗留缓存，再按 orchestrator skill 的选题规则启动新讨论。
- 必须把 `student` 视为讨论角色，而不是固定等价于 `pbl-student` 子智能体。
- 若本次提供了新话题，启动时优先通过本地 bash 调用 `python3 -m pbl_runtime.cli bootstrap --topic "$ARGUMENTS"`，实际创建 session 并启动 runtime 与 GUI；若用户未提供话题，则先判断用户是否明确要求续跑。只有明确续跑时才恢复当前未完成 session；否则必须先清空上一轮遗留 session 的活动指针、待消费学生正文与等待 checkpoint，再按 orchestrator skill 的避重规则重新选题并启动 bootstrap。
- 无论是新建还是恢复，进入正式编排前都必须通过本地 bash 调用 `python3 -m pbl_runtime.cli ensure-services --session-id <id>` 确认 runtime 与 GUI 仍在运行；若后台 Python 进程已退出，应自动重启，而不是继续假定 GUI 仍可用。
- 必须由运行时统一维护学生角色的用户举手状态、待消费正文、是否已被选中发言与聚合后的发言意愿，并把该聚合状态作为 moderator 的官方学生输入。
- 在学生首次发言开始前，必须先启动本地 runtime/session 与 GUI，并进入等待学生输入的状态。
- moderator 必须实时监测 runtime 聚合出的学生举手状态；当选中 `student` 发言时，运行时必须把“已选中发言”的提示同步到 GUI。
- 当 moderator 选中 `student` 发言时，优先通过本地 bash 调用 `python3 -m pbl_runtime.cli select-student --session-id <id> --prompt "..."` 同步 GUI 状态；用户随后应在对话界面使用 `/pbl-say ...` 提交正文；编排器再通过读取 `data/runtime/` 下 session 文件或通过 `python3 -m pbl_runtime.cli wait-student --session-id <id> --timeout <短超时>` 检查正文是否已到达；拿到正文后再通过 `python3 -m pbl_runtime.cli consume-student --session-id <id>` 安全消费该发言。
- 如果短超时后仍未收到正文，必须明确报告当前 session 正在等待 GUI 输入，并把当前 `session_id`、日志路径和恢复方式返回给用户；这属于正常等待状态，不属于链路失败。
- 编排器应把以下本地命令视为用户参与工作流的正式桥接接口：`python3 -m pbl_runtime.cli ensure-services`、`resume-info`、`phase`、`status`、`checkpoint`、`init-transcripts`、`append-public`、`select-student`、`submit-student`、`wait-student`、`consume-student`。
- 在 user 模式下，编排器在每次 moderator 选人前都应优先读取 `python3 -m pbl_runtime.cli resume-info --session-id <id>` 或对应 `state.json`；学生是否举手必须以 `moderator_view.student_hand_raised`、`participants.student.effective_hand_raised` 等 runtime 字段为准，而不是靠 prompt 内推断。
- 在 teacher 选题、材料包、教师引导、每轮正文发言、教师追问、学生作答、教师终评等任一步骤产生可公开正文后，都必须立刻通过 `python3 -m pbl_runtime.cli append-public ...` 同步写入单次转录与 `data/transcripts/latest.md`。
- 在每个关键阶段切换后，都应通过 `python3 -m pbl_runtime.cli phase ...` 和 `checkpoint ...` 把当前阶段与恢复点写回 runtime 状态，保证下次 `/pbl-user` 能从最近检查点继续，而不是重新开始整场讨论。
- 当整场讨论结束或被明确放弃时，应通过 `python3 -m pbl_runtime.cli complete-session --session-id <id>` 把当前 session 标记为完成或取消，并清空 `data/runtime/current_session.txt`，避免下一轮默认误续上一次会话。
- teacher、material researcher、ta、两位同伴、moderator 和 summarizer 仍按各自 skill 调用对应子智能体。
- 转录实时落盘、材料包质量与教师追问/终评阶段仍遵守 orchestrator skill 中的 user 模式契约；自由讨论状态刷新在 user 模式下只适用于 ta、`peer_high`、`peer_low`，学生状态不走常规刷新，而是直接读取 runtime 聚合结果。
- 若当前环境无法启动本地 Python 进程或无法打开 GUI，再明确报告失败原因；不要在 runtime 未真正启动的情况下伪装成已进入用户参与式讨论。
