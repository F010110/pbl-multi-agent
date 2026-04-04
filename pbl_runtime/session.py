from __future__ import annotations

import json
import re
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import current_session_file, events_file, inbox_dir, latest_session_file, runtime_root, runtime_state_file, session_dir, session_file, state_file
from .templates import APPEND_POINT, DEFAULT_LATEST_TRANSCRIPT_PATH, session_meta_template, state_template, student_effective_state_template, student_input_template, transcript_skeleton


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "session"


def allocate_session_id(topic: str, base_dir: str | Path | None = None) -> str:
    base = runtime_root(base_dir)
    slug = slugify(topic)[:40]
    while True:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:6]
        session_id = f"{timestamp}-{slug}-{suffix}"
        if not session_dir(session_id, base).exists():
            return session_id


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def insert_before_append_point(content: str, block: str) -> str:
    if content.count(APPEND_POINT) != 1:
        raise ValueError("Transcript must contain exactly one append point.")
    normalized = block.rstrip()
    if normalized:
        normalized += "\n\n"
    return content.replace(APPEND_POINT, normalized + APPEND_POINT)


def default_student_effective_state() -> dict[str, Any]:
    return student_effective_state_template()


def default_student_input_state() -> dict[str, Any]:
    return student_input_template()


def default_state(session_id: str, topic: str, student_mode: str) -> dict[str, Any]:
    return state_template(session_id, topic, student_mode, utc_now())


def default_session_meta(session_id: str, topic: str, student_mode: str) -> dict[str, Any]:
    return session_meta_template(session_id, topic, student_mode, utc_now())


def ensure_state_shape(state: dict[str, Any]) -> dict[str, Any]:
    runtime = state.setdefault("runtime", {})
    runtime.setdefault("waiting_for_student_input", False)
    runtime.setdefault("selected_next_role", "")
    runtime.setdefault("selected_next_source", "")
    runtime.setdefault("student_selected_to_speak", False)
    runtime.setdefault("selection_prompt", "")
    runtime.setdefault("last_runtime_tick_at", "")
    runtime.setdefault("last_consumed_inbox_file", "")

    orchestrator = state.setdefault("orchestrator", {})
    orchestrator.setdefault("checkpoint", "bootstrap")
    orchestrator.setdefault("waiting_reason", "")
    orchestrator.setdefault("transcript_path", "")
    orchestrator.setdefault("latest_transcript_path", DEFAULT_LATEST_TRANSCRIPT_PATH)
    orchestrator.setdefault("last_public_content_at", "")

    moderator_view = state.setdefault("moderator_view", {})
    moderator_view.setdefault("student_hand_raised", False)
    moderator_view.setdefault("student_wants_to_end_discussion", False)
    moderator_view.setdefault("student_pending_utterance", False)
    moderator_view.setdefault("student_source_priority", "agent")
    return state


def maybe_pending_student_utterance(state: dict[str, Any]) -> dict[str, Any] | None:
    student = state["participants"]["student"]
    text = student.get("pending_human_utterance", "").strip()
    utterance_id = student.get("pending_human_utterance_id", "")
    if not text or not utterance_id:
        return None
    return {
        "utterance_id": utterance_id,
        "text": text,
        "created_at": student.get("latest_human_utterance_at", ""),
    }


@dataclass
class SessionRuntime:
    session_id: str
    base_dir: Path | str = Path("data/runtime")

    def __post_init__(self) -> None:
        self.base_dir = runtime_root(self.base_dir)

    @property
    def root(self) -> Path:
        return session_dir(self.session_id, self.base_dir)

    @property
    def inbox(self) -> Path:
        return inbox_dir(self.session_id, self.base_dir)

    @property
    def session_path(self) -> Path:
        return session_file(self.session_id, self.base_dir)

    @property
    def state_path(self) -> Path:
        return runtime_state_file(self.session_id, self.base_dir)

    @property
    def public_state_path(self) -> Path:
        return state_file(self.session_id, self.base_dir)

    @property
    def events_path(self) -> Path:
        return events_file(self.session_id, self.base_dir)

    @property
    def transcripts_root(self) -> Path:
        return self.base_dir.parent / "transcripts"

    @property
    def default_transcript_path(self) -> Path:
        return self.transcripts_root / f"{self.session_id}.md"

    @property
    def default_latest_transcript_path(self) -> Path:
        return self.transcripts_root / "latest.md"

    @classmethod
    def create(cls, topic: str, student_mode: str = "hybrid", base_dir: str | Path | None = None) -> "SessionRuntime":
        session_id = allocate_session_id(topic, base_dir)
        runtime = cls(session_id=session_id, base_dir=runtime_root(base_dir))
        runtime._ensure_layout()
        atomic_write_json(runtime.session_path, default_session_meta(session_id, topic, student_mode))
        atomic_write_json(runtime.state_path, default_state(session_id, topic, student_mode))
        atomic_write_json(runtime.public_state_path, default_student_input_state())
        atomic_write_text(runtime.events_path, "")
        atomic_write_text(current_session_file(runtime.base_dir), session_id + "\n")
        atomic_write_text(latest_session_file(runtime.base_dir), session_id + "\n")
        runtime.enqueue_event(
            {
                "type": "SESSION_CREATED",
                "topic": topic,
                "student_mode": student_mode,
                "source": "runtime",
            }
        )
        runtime.process_inbox_once()
        return runtime

    @classmethod
    def from_current(cls, base_dir: str | Path | None = None) -> "SessionRuntime":
        current = current_session_file(base_dir)
        if not current.exists():
            raise FileNotFoundError("No current session. Create one with 'python -m pbl_runtime.cli init'.")
        session_id = current.read_text(encoding="utf-8").strip()
        runtime = cls(session_id=session_id, base_dir=runtime_root(base_dir))
        if runtime.read_session().get("session_status") != "active":
            raise FileNotFoundError("No active current session. Start a new one or select an unfinished session.")
        return runtime

    @classmethod
    def from_latest(cls, base_dir: str | Path | None = None) -> "SessionRuntime":
        latest = latest_session_file(base_dir)
        if not latest.exists():
            raise FileNotFoundError("No latest session. Create one with 'python -m pbl_runtime.cli init'.")
        return cls(session_id=latest.read_text(encoding="utf-8").strip(), base_dir=runtime_root(base_dir))

    def _ensure_layout(self) -> None:
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def read_state(self) -> dict[str, Any]:
        if not self.state_path.exists() and self.public_state_path.exists():
            legacy = read_json(self.public_state_path)
            if isinstance(legacy, dict) and "participants" in legacy:
                atomic_write_json(self.state_path, ensure_state_shape(legacy))
        return ensure_state_shape(read_json(self.state_path))

    def read_student_input(self) -> dict[str, Any]:
        if not self.public_state_path.exists():
            legacy_student_input_path = self.root / "student_input.json"
            if legacy_student_input_path.exists():
                payload = read_json(legacy_student_input_path)
                normalized = {
                    "hand_raised": bool(payload.get("hand_raised", False)),
                    "wants_to_end_discussion": bool(payload.get("wants_to_end_discussion", False)),
                }
                atomic_write_json(self.public_state_path, normalized)
                return normalized
            payload = default_student_input_state()
            atomic_write_json(self.public_state_path, payload)
            return payload
        payload = read_json(self.public_state_path)
        normalized = {
            "hand_raised": bool(payload.get("hand_raised", False)),
            "wants_to_end_discussion": bool(payload.get("wants_to_end_discussion", False)),
        }
        atomic_write_json(self.public_state_path, normalized)
        return normalized

    def write_student_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "hand_raised": bool(payload.get("hand_raised", False)),
            "wants_to_end_discussion": bool(payload.get("wants_to_end_discussion", False)),
        }
        atomic_write_json(self.public_state_path, normalized)
        return normalized

    def update_student_input_state(
        self,
        *,
        hand_raised: bool | None = None,
        wants_to_end_discussion: bool | None = None,
    ) -> dict[str, Any]:
        payload = self.read_student_input()
        if hand_raised is not None:
            payload["hand_raised"] = hand_raised
        if wants_to_end_discussion is not None:
            payload["wants_to_end_discussion"] = wants_to_end_discussion
        self.write_student_input(payload)
        state = self.read_state()
        self._refresh_student_effective_state(state)
        state["updated_at"] = utc_now()
        self.write_state(state)
        return state

    def read_session(self) -> dict[str, Any]:
        return read_json(self.session_path)

    def update_session_meta(self, **updates: Any) -> dict[str, Any]:
        session_meta = self.read_session()
        session_meta.update(updates)
        session_meta["updated_at"] = utc_now()
        atomic_write_json(self.session_path, session_meta)
        return session_meta

    def mark_session_completed(self, status: str = "completed") -> dict[str, Any]:
        if status not in {"completed", "cancelled"}:
            raise ValueError("status must be 'completed' or 'cancelled'")
        session_meta = self.update_session_meta(session_status=status, completed_at=utc_now())
        current = current_session_file(self.base_dir)
        if current.exists() and current.read_text(encoding="utf-8").strip() == self.session_id:
            atomic_write_text(current, "")
        return session_meta

    def write_state(self, state: dict[str, Any]) -> None:
        atomic_write_json(self.state_path, ensure_state_shape(state))

    def update_orchestrator_state(
        self,
        *,
        checkpoint: str | None = None,
        waiting_reason: str | None = None,
        transcript_path: str | None = None,
        latest_transcript_path: str | None = None,
        last_public_content_at: str | None = None,
    ) -> dict[str, Any]:
        state = self.read_state()
        orchestrator = state["orchestrator"]
        if checkpoint is not None:
            orchestrator["checkpoint"] = checkpoint
        if waiting_reason is not None:
            orchestrator["waiting_reason"] = waiting_reason
        if transcript_path is not None:
            orchestrator["transcript_path"] = transcript_path
        if latest_transcript_path is not None:
            orchestrator["latest_transcript_path"] = latest_transcript_path
        if last_public_content_at is not None:
            orchestrator["last_public_content_at"] = last_public_content_at
        state["updated_at"] = utc_now()
        self.write_state(state)
        return state

    def update_phase(self, phase: str) -> dict[str, Any]:
        state = self.read_state()
        state["phase"] = phase
        state["updated_at"] = utc_now()
        self.write_state(state)
        return state

    def update_status(self, status: str) -> dict[str, Any]:
        state = self.read_state()
        state["status"] = status
        state["updated_at"] = utc_now()
        self.write_state(state)
        return state

    def initialize_transcripts(
        self,
        *,
        topic: str | None = None,
        transcript_path: str | Path | None = None,
        latest_path: str | Path | None = None,
    ) -> dict[str, str]:
        actual_topic = topic or self.read_state().get("topic", "")
        run_path = Path(transcript_path) if transcript_path else self.default_transcript_path
        latest = Path(latest_path) if latest_path else self.default_latest_transcript_path
        skeleton = transcript_skeleton(actual_topic)
        atomic_write_text(run_path, skeleton)
        atomic_write_text(latest, skeleton)
        self.update_orchestrator_state(
            transcript_path=str(run_path),
            latest_transcript_path=str(latest),
        )
        return {"transcript_path": str(run_path), "latest_transcript_path": str(latest)}

    def append_public_content(self, markdown: str) -> dict[str, str]:
        state = self.read_state()
        orchestrator = state["orchestrator"]
        run_path = Path(orchestrator.get("transcript_path") or self.default_transcript_path)
        latest = Path(orchestrator.get("latest_transcript_path") or self.default_latest_transcript_path)
        for path in [run_path, latest]:
            if not path.exists():
                raise FileNotFoundError(f"Transcript file not initialized: {path}")
            updated = insert_before_append_point(path.read_text(encoding="utf-8"), markdown)
            atomic_write_text(path, updated)
        timestamp = utc_now()
        self.update_orchestrator_state(
            transcript_path=str(run_path),
            latest_transcript_path=str(latest),
            last_public_content_at=timestamp,
        )
        return {
            "transcript_path": str(run_path),
            "latest_transcript_path": str(latest),
            "last_public_content_at": timestamp,
        }

    def select_student_turn(
        self,
        prompt: str,
        *,
        source_priority: str = "human",
        checkpoint: str = "waiting_for_student_turn",
        waiting_reason: str = "awaiting_student_utterance",
    ) -> dict[str, Any]:
        self.enqueue_event(
            {
                "type": "NEXT_SPEAKER_SELECTED",
                "source": "runtime",
                "role": "student",
                "source_priority": source_priority,
                "prompt": prompt,
            }
        )
        self.process_inbox_once()
        state = self.read_state()
        state["runtime"]["waiting_for_student_input"] = True
        state["runtime"]["student_selected_to_speak"] = True
        state["runtime"]["selected_next_role"] = "student"
        state["runtime"]["selected_next_source"] = source_priority
        state["runtime"]["selection_prompt"] = prompt
        state["orchestrator"]["checkpoint"] = checkpoint
        state["orchestrator"]["waiting_reason"] = waiting_reason
        state["updated_at"] = utc_now()
        self.write_state(state)
        return state

    def resume_info(self) -> dict[str, Any]:
        state = self.read_state()
        session_meta = self.read_session()
        pending = maybe_pending_student_utterance(state)
        return {
            "session_id": state["session_id"],
            "topic": state["topic"],
            "phase": state["phase"],
            "status": state["status"],
            "student_mode": state["student_mode"],
            "session": deepcopy(session_meta),
            "orchestrator": deepcopy(state["orchestrator"]),
            "runtime": deepcopy(state["runtime"]),
            "moderator_view": deepcopy(state["moderator_view"]),
            "pending_student_utterance": pending,
        }

    def enqueue_event(self, event: dict[str, Any]) -> Path:
        self._ensure_layout()
        envelope = {
            "event_id": uuid.uuid4().hex,
            "session_id": self.session_id,
            "created_at": utc_now(),
            **event,
        }
        filename = f"{int(time.time() * 1000)}-{envelope['event_id']}.json"
        path = self.inbox / filename
        atomic_write_json(path, envelope)
        return path

    def process_inbox_once(self) -> int:
        self._ensure_layout()
        count = 0
        for path in sorted(self.inbox.glob("*.json")):
            event = read_json(path)
            self._append_event(event)
            self._apply_event(event)
            path.unlink()
            count += 1
        if count:
            state = self.read_state()
            state["runtime"]["last_runtime_tick_at"] = utc_now()
            atomic_write_json(self.state_path, state)
        return count

    def run_forever(self, poll_interval: float = 0.5) -> None:
        while True:
            self.process_inbox_once()
            time.sleep(poll_interval)

    def wait_for_student_utterance(self, timeout_seconds: float = 60.0, poll_interval: float = 0.5) -> dict[str, Any] | None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            self.process_inbox_once()
            state = self.read_state()
            pending = maybe_pending_student_utterance(state)
            if pending is not None:
                return pending
            time.sleep(poll_interval)
        self.process_inbox_once()
        return maybe_pending_student_utterance(self.read_state())

    def consume_student_utterance(self) -> dict[str, Any] | None:
        state = self.read_state()
        pending = maybe_pending_student_utterance(state)
        if pending is None:
            return None
        self.enqueue_event(
            {
                "type": "UTTERANCE_CONSUMED",
                "source": "runtime",
                "utterance_id": pending["utterance_id"],
            }
        )
        self.process_inbox_once()
        return pending

    def _append_event(self, event: dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _apply_event(self, event: dict[str, Any]) -> None:
        state = self.read_state()
        participants = state["participants"]
        student = participants["student"]
        event_type = event["type"]

        if event_type == "SESSION_CREATED":
            state["status"] = "ready"
        elif event_type == "HAND_RAISED":
            self.write_student_input({"hand_raised": True, "wants_to_end_discussion": False})
        elif event_type == "HAND_LOWERED":
            payload = self.read_student_input()
            payload["hand_raised"] = False
            self.write_student_input(payload)
        elif event_type == "END_DISCUSSION_REQUESTED":
            self.write_student_input({"hand_raised": False, "wants_to_end_discussion": True})
        elif event_type == "END_DISCUSSION_CLEARED":
            payload = self.read_student_input()
            payload["wants_to_end_discussion"] = False
            self.write_student_input(payload)
        elif event_type == "UTTERANCE_SUBMITTED":
            student["pending_human_utterance"] = event.get("text", "").strip()
            student["pending_human_utterance_id"] = event["event_id"]
            student["latest_human_utterance_at"] = event["created_at"]
            state["runtime"]["waiting_for_student_input"] = False
            state["runtime"]["student_selected_to_speak"] = False
            state["runtime"]["selected_next_role"] = ""
            state["runtime"]["selected_next_source"] = ""
            state["runtime"]["selection_prompt"] = ""
        elif event_type == "UTTERANCE_CONSUMED":
            if event.get("utterance_id") == student.get("pending_human_utterance_id"):
                student["pending_human_utterance"] = ""
                student["pending_human_utterance_id"] = ""
        elif event_type == "NEXT_SPEAKER_SELECTED":
            selected_role = event.get("role", "")
            state["runtime"]["selected_next_role"] = selected_role
            state["runtime"]["selected_next_source"] = event.get("source_priority", "")
            state["runtime"]["selection_prompt"] = event.get("prompt", "")
            state["runtime"]["student_selected_to_speak"] = selected_role == "student"
            state["runtime"]["waiting_for_student_input"] = selected_role == "student"
        elif event_type == "STUDENT_AGENT_STATE_UPDATED":
            card = deepcopy(event.get("state_card") or {})
            student["latest_agent_state_card"] = card
            student["agent_hand_raised"] = bool(card.get("hand_raised"))
        elif event_type == "ROLE_STATE_UPDATED":
            role = event.get("role")
            if role in participants and role != "student":
                participants[role]["latest_state_card"] = deepcopy(event.get("state_card") or {})
        elif event_type == "PHASE_UPDATED":
            state["phase"] = event.get("phase", state["phase"])
        elif event_type == "RUNTIME_STATUS_UPDATED":
            state["status"] = event.get("status", state["status"])
            state["runtime"]["waiting_for_student_input"] = bool(event.get("waiting_for_student_input", False))
            state["runtime"]["selected_next_role"] = event.get("selected_next_role", "")
            state["runtime"]["selected_next_source"] = event.get("selected_next_source", "")
        elif event_type == "ORCHESTRATOR_CHECKPOINT_UPDATED":
            orchestrator = state["orchestrator"]
            orchestrator["checkpoint"] = event.get("checkpoint", orchestrator["checkpoint"])
            orchestrator["waiting_reason"] = event.get("waiting_reason", orchestrator["waiting_reason"])
            orchestrator["transcript_path"] = event.get("transcript_path", orchestrator["transcript_path"])
            orchestrator["latest_transcript_path"] = event.get(
                "latest_transcript_path", orchestrator["latest_transcript_path"]
            )
            orchestrator["last_public_content_at"] = event.get(
                "last_public_content_at", orchestrator["last_public_content_at"]
            )
        elif event_type == "STUDENT_MODE_UPDATED":
            state["student_mode"] = event.get("student_mode", state["student_mode"])
            session_meta = self.read_session()
            session_meta["student_mode"] = state["student_mode"]
            session_meta["updated_at"] = utc_now()
            atomic_write_json(self.session_path, session_meta)

        self._refresh_student_effective_state(state)
        state["latest_event_id"] += 1
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)

    def _refresh_student_effective_state(self, state: dict[str, Any]) -> None:
        student = state["participants"]["student"]
        student_input = self.read_student_input()
        agent_card = deepcopy(student.get("latest_agent_state_card") or {})
        effective = default_student_effective_state()
        effective["can_end_discussion"] = bool(agent_card.get("can_end_discussion", False))

        human_pending = bool(student.get("pending_human_utterance"))
        human_hand = bool(student_input.get("hand_raised", False))
        wants_to_end_discussion = bool(student_input.get("wants_to_end_discussion", False))
        agent_hand = bool(student.get("agent_hand_raised"))
        effective_hand = human_pending or human_hand or agent_hand

        effective["hand_raised"] = effective_hand
        if human_pending:
            effective["can_end_discussion"] = False
        elif wants_to_end_discussion and not effective_hand:
            effective["can_end_discussion"] = True

        student["human_hand_raised"] = human_hand
        student["wants_to_end_discussion"] = wants_to_end_discussion
        student["effective_hand_raised"] = effective_hand
        student["effective_state_card"] = effective
        state["moderator_view"]["student_hand_raised"] = effective_hand
        state["moderator_view"]["student_wants_to_end_discussion"] = wants_to_end_discussion
        state["moderator_view"]["student_pending_utterance"] = human_pending
        state["moderator_view"]["student_source_priority"] = "human" if (human_pending or human_hand) else "agent"


def format_state_summary(state: dict[str, Any]) -> str:
    student = state["participants"]["student"]
    effective = student["effective_state_card"]
    return (
        f"session={state['session_id']}\n"
        f"topic={state['topic']}\n"
        f"phase={state['phase']}\n"
        f"status={state['status']}\n"
        f"checkpoint={state['orchestrator']['checkpoint']}\n"
        f"waiting_reason={state['orchestrator']['waiting_reason']}\n"
        f"student_mode={state['student_mode']}\n"
        f"human_hand_raised={student['human_hand_raised']}\n"
        f"wants_to_end_discussion={student.get('wants_to_end_discussion', False)}\n"
        f"agent_hand_raised={student['agent_hand_raised']}\n"
        f"effective_hand_raised={student['effective_hand_raised']}\n"
        f"pending_human_utterance={bool(student['pending_human_utterance'])}\n"
        f"source_priority={state['moderator_view']['student_source_priority']}\n"
        f"student_selected_to_speak={state['runtime']['student_selected_to_speak']}\n"
        f"waiting_for_student_input={state['runtime']['waiting_for_student_input']}\n"
    )
