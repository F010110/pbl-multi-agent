# 状态卡与 JSON 复用片段

## 适用角色

- `pbl-student`
- `pbl-ta`
- `pbl-peer-high`
- `pbl-peer-low`

## 复用目的

- 统一先生成内部 `state_card`，再生成发言。
- 统一返回可被 orchestrator 和 moderator 消费的结构化状态字段。
- 统一跟踪 `can_end_discussion`、`wants_to_continue`、`remaining_confusion` 等结束信号。
