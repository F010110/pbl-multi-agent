from __future__ import annotations

from typing import Any

APPEND_POINT = "<!-- PBL_APPEND_POINT -->"
DEFAULT_LATEST_TRANSCRIPT_PATH = "data/transcripts/latest.md"


def student_effective_state_template() -> dict[str, Any]:
    return {
        "hand_raised": False,
        "can_end_discussion": False,
    }


def student_input_template() -> dict[str, Any]:
    return {
        "hand_raised": False,
        "wants_to_end_discussion": False,
    }


def state_template(session_id: str, topic: str, student_mode: str, updated_at: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "topic": topic,
        "mode": "user_participatory",
        "status": "waiting_for_runtime",
        "phase": "topic_selection",
        "student_mode": student_mode,
        "latest_event_id": 0,
        "updated_at": updated_at,
        "participants": {
            "student": {
                "human_hand_raised": False,
                "agent_hand_raised": False,
                "effective_hand_raised": False,
                "pending_human_utterance": "",
                "pending_human_utterance_id": "",
                "latest_human_utterance_at": "",
                "latest_agent_state_card": None,
                "effective_state_card": student_effective_state_template(),
            },
            "ta": {"latest_state_card": None},
            "peer_high": {"latest_state_card": None},
            "peer_low": {"latest_state_card": None},
        },
        "runtime": {
            "waiting_for_student_input": False,
            "selected_next_role": "",
            "selected_next_source": "",
            "student_selected_to_speak": False,
            "selection_prompt": "",
            "last_runtime_tick_at": "",
            "last_consumed_inbox_file": "",
        },
        "orchestrator": {
            "checkpoint": "bootstrap",
            "waiting_reason": "",
            "transcript_path": "",
            "latest_transcript_path": DEFAULT_LATEST_TRANSCRIPT_PATH,
            "last_public_content_at": "",
        },
        "moderator_view": {
            "student_hand_raised": False,
            "student_wants_to_end_discussion": False,
            "student_pending_utterance": False,
            "student_source_priority": "agent",
        },
    }


def session_meta_template(session_id: str, topic: str, student_mode: str, updated_at: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "topic": topic,
        "mode": "user_participatory",
        "student_mode": student_mode,
        "session_status": "active",
        "run_pid": None,
        "gui_pid": None,
        "runtime_log": "",
        "gui_log": "",
        "completed_at": "",
        "created_at": updated_at,
        "updated_at": updated_at,
    }


def transcript_skeleton(topic: str) -> str:
    return f"# PBL 讨论转录\n\n主题：{topic}\n\n{APPEND_POINT}\n"
