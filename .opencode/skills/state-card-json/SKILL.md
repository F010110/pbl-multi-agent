---
name: state-card-json
description: Shared JSON state-card schema and output requirements for discussion participants.
---

# 状态卡与 JSON 复用片段

## 适用角色

- `pbl-student`
- `pbl-ta`
- `pbl-peer-high`
- `pbl-peer-low`

## 复用目的

- 统一先更新内部 `state_card`，再生成发言。
- 统一返回以 `state_card` 为核心的结构化输出，避免在顶层重复状态字段。
- 统一跟踪少量必要状态，降低轮次成本。

## 统一 JSON 格式

- 如果被要求返回 JSON，默认采用以下简明结构：`{"state_card": {...}, "utterance": "..."}`。
- `state_card` 是唯一的状态容器；供 orchestrator 和 moderator 消费的状态变量都放在这里，不要在顶层重复展开。
- `utterance` 是唯一对外自然语言发言字段，必须非空。
- `state_card` 默认至少应包含：`belief_state`、`confidence`、`hand_raised`、`disagreement_target`、`can_end_discussion`、`remaining_confusion`。
- `state_card.belief_state`：角色当前判断或立场的简短概括。
- `state_card.confidence`：角色对当前判断的把握度，统一用 `low`、`medium`、`high`。
- `state_card.hand_raised`：布尔值，表示该角色当前是否举手想发言。
- `state_card.disagreement_target`：角色本轮主要回应、质疑、修正或附和的人/观点；若无则为空字符串。
- `state_card.can_end_discussion`：布尔值，表示该角色是否认为自由讨论已可结束。
- `state_card.remaining_confusion`：角色仍未解决的困惑；若无则为空字符串。
- 角色可以在 `state_card` 中补充少量必要字段，但应保持简短，优先服务于轮次编排和状态跟踪。
- 如果 role packet 中提供了“上一次输出的 state_card”，应先阅读它，再决定这轮如何更新状态和发言。
- `hand_raised` 的更新规则：如果当前有明确想反驳的点，或有尚未表达的疑惑，就应升为 `true`；一旦相关反驳已经说出，或疑惑已经表达过，就应降为 `false`。
