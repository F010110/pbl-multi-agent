from __future__ import annotations

from pathlib import Path


def runtime_root(base_dir: str | Path | None = None) -> Path:
    if base_dir is None:
        return Path("data/runtime")
    return Path(base_dir)


def sessions_root(base_dir: str | Path | None = None) -> Path:
    return runtime_root(base_dir) / "sessions"


def current_session_file(base_dir: str | Path | None = None) -> Path:
    return runtime_root(base_dir) / "current_session.txt"


def latest_session_file(base_dir: str | Path | None = None) -> Path:
    return runtime_root(base_dir) / "latest_session.txt"


def session_dir(session_id: str, base_dir: str | Path | None = None) -> Path:
    return sessions_root(base_dir) / session_id


def inbox_dir(session_id: str, base_dir: str | Path | None = None) -> Path:
    return session_dir(session_id, base_dir) / "inbox"


def session_file(session_id: str, base_dir: str | Path | None = None) -> Path:
    return session_dir(session_id, base_dir) / "session.json"


def state_file(session_id: str, base_dir: str | Path | None = None) -> Path:
    return session_dir(session_id, base_dir) / "state.json"


def runtime_state_file(session_id: str, base_dir: str | Path | None = None) -> Path:
    return session_dir(session_id, base_dir) / "runtime_state.json"


def events_file(session_id: str, base_dir: str | Path | None = None) -> Path:
    return session_dir(session_id, base_dir) / "events.jsonl"
