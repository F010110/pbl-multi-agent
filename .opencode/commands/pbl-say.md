---
description: 在用户参与式 PBL 会话中提交学生发言。
agent: pbl-orchestrator
---
## 适配定位

- 本文件是 `/pbl-say` 的命令入口。
- 本命令只负责把当前用户输入作为 `student` 的一轮发言写入当前活动 session。
- 本命令在提交成功后应直接继续当前 `/pbl-user` 会话的后续编排，而不是要求用户再额外输入一次 `/pbl-user`。

## 运行要求

- 用户本次提交的学生发言正文：`$ARGUMENTS`
- 若 `data/runtime/current_session.txt` 不存在有效活动 session，必须明确报错，不要伪造提交成功。
- 优先通过本地 bash 调用 `python3 -m pbl_runtime.cli submit-student --text "$ARGUMENTS"` 写入当前活动 session。
- 提交成功后，应继续按当前 session 的最新 checkpoint 推进用户参与式讨论；仅当推进过程中再次进入等待状态时，才向用户返回新的等待提示。
- 若正文为空，也必须明确报错。
