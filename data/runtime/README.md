# Runtime Data

这个目录是 `/pbl-user` 的本地会话运行时持久化层。

这里保存的是可恢复讨论所需的官方状态源，不是给用户手工编辑的工作区。编排器、GUI 和其他适配器应通过 `pbl_runtime.cli` 或投递事件来更新它。

这些落盘文件的默认模版统一维护在 `pbl_runtime/templates.py`，避免 `state.json`、`runtime_state.json`、`session.json` 和转录骨架在不同位置各写一份而发生漂移。

## 目录结构

- `current_session.txt`：当前活动且未完成的 session id；会话完成或取消后会被清空
- `latest_session.txt`：最近一次创建的 session id；即使该 session 已结束也会保留
- `sessions/<session_id>/session.json`：会话元信息，例如 `topic`、`student_mode`、后台 `run_pid` / `gui_pid`、日志路径和完成状态
- `sessions/<session_id>/state.json`：学生侧的人类输入开关，仅保存 `hand_raised` 与 `wants_to_end_discussion`
- `sessions/<session_id>/runtime_state.json`：编排器恢复所需的内部聚合状态快照，包括 `phase`、`status`、`orchestrator`、`runtime`、`moderator_view` 与各角色最新状态；其中学生的聚合 `effective_state_card` 只保留 `hand_raised` 和 `can_end_discussion`
- `sessions/<session_id>/events.jsonl`：已被 runtime 正式消费并落盘的事件日志
- `sessions/<session_id>/inbox/*.json`：待 runtime 消费的事件队列；GUI、`/pbl-say` 或其他桥接接口先写这里，再由 runtime 处理并追加到 `events.jsonl`
- `logs/<session_id>/runtime.log`：后台 runtime 进程日志
- `logs/<session_id>/gui.log`：GUI 进程日志

## 关键约定

- 每场讨论都必须使用独立的 `sessions/<session_id>/` 目录；`session_id` 由时间戳、topic slug 和随机后缀组成，避免复用旧目录。
- 默认 runtime 根目录是 `data/runtime`；测试或临时运行可以通过 `python3 -m pbl_runtime.cli --base-dir ...` 改到别的目录。
- `bootstrap` 会创建 session、启动后台 runtime 与 GUI、写入 `current_session.txt` / `latest_session.txt`，并把会话置为可恢复状态。
- `ensure-services` 会根据 `session.json` 中记录的 pid 和日志路径确认后台进程是否仍在运行；如已退出会自动重启。
- `complete-session` 只会清空匹配当前 session 的 `current_session.txt`；`latest_session.txt` 会继续指向最近一次创建的 session。

## 学生状态来源

- GUI 的“举手 / 放下手 / 想结束研讨 / 继续讨论”会通过事件更新 `state.json` 里的用户输入状态；内部聚合结果再同步写入 `runtime_state.json`。
- `/pbl-say` 或 `submit-student` 会投递 `UTTERANCE_SUBMITTED`；当编排器消费完该正文后，再通过 `consume-student` 生成 `UTTERANCE_CONSUMED`。
- moderator 选中学生发言时，runtime 会记录 `NEXT_SPEAKER_SELECTED`，并把 `runtime.student_selected_to_speak`、`runtime.waiting_for_student_input` 与 `runtime.selection_prompt` 写入 `runtime_state.json`，供 GUI 和编排器同步读取。

## 编排器读取入口

- 对 orchestrator 和 moderator，`runtime_state.json` 中的 `moderator_view` 是最直接的学生聚合视图。
- 最常用字段是：`moderator_view.student_hand_raised`、`moderator_view.student_pending_utterance`、`moderator_view.student_wants_to_end_discussion`、`moderator_view.student_source_priority`。
- 若需要更完整上下文，再结合 `participants.student.pending_human_utterance`、`runtime.student_selected_to_speak`、`orchestrator.checkpoint` 与 `orchestrator.waiting_reason` 一起判断。

## 与转录的关系

- 公开讨论正文不保存在 `data/runtime/`，而是通过 `init-transcripts` 和 `append-public` 实时写入 `data/transcripts/`。
- `runtime_state.json` 的 `orchestrator.transcript_path`、`orchestrator.latest_transcript_path` 和 `orchestrator.last_public_content_at` 只负责记录当前转录落盘位置与最近一次公开追加时间。
