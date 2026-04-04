from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .session import SessionRuntime, format_state_summary


def resolve_runtime(session_id: str | None, base_dir: str | Path | None) -> SessionRuntime:
    if session_id:
        return SessionRuntime(session_id=session_id, base_dir=base_dir)
    return SessionRuntime.from_current(base_dir=base_dir)


def resolve_latest_runtime(base_dir: str | Path | None) -> SessionRuntime:
    return SessionRuntime.from_latest(base_dir=base_dir)


def cmd_init(args: argparse.Namespace) -> int:
    runtime = SessionRuntime.create(topic=args.topic, student_mode=args.student_mode, base_dir=args.base_dir)
    print(runtime.session_id)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    runtime.run_forever(poll_interval=args.interval)
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    count = runtime.process_inbox_once()
    print(count)
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    state = runtime.read_state()
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(format_state_summary(state), end="")
    return 0


def cmd_resume_info(args: argparse.Namespace) -> int:
    runtime = resolve_latest_runtime(args.base_dir) if args.latest else resolve_runtime(args.session_id, args.base_dir)
    print(json.dumps(runtime.resume_info(), ensure_ascii=False, indent=2))
    return 0


def cmd_phase(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    state = runtime.update_phase(args.phase)
    print(json.dumps({"phase": state["phase"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    state = runtime.update_status(args.status)
    print(json.dumps({"status": state["status"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    state = runtime.update_orchestrator_state(
        checkpoint=args.checkpoint,
        waiting_reason=args.waiting_reason,
        transcript_path=args.transcript_path,
        latest_transcript_path=args.latest_transcript_path,
        last_public_content_at=args.last_public_content_at,
    )
    print(json.dumps(state["orchestrator"], ensure_ascii=False, indent=2))
    return 0


def cmd_init_transcripts(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    payload = runtime.initialize_transcripts(
        topic=args.topic,
        transcript_path=args.transcript_path,
        latest_path=args.latest_transcript_path,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_append_public(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    payload = runtime.append_public_content(args.markdown.replace("\\n", "\n"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_complete_session(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    session_meta = runtime.mark_session_completed(status=args.status)
    print(json.dumps(session_meta, ensure_ascii=False, indent=2))
    return 0


def _pid_is_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _service_commands(runtime: SessionRuntime) -> tuple[list[str], list[str]]:
    run_cmd = [
        sys.executable,
        "-m",
        "pbl_runtime.cli",
        "--base-dir",
        str(runtime.base_dir),
        "run",
        "--session-id",
        runtime.session_id,
    ]
    gui_cmd = [
        sys.executable,
        "-m",
        "pbl_runtime.cli",
        "--base-dir",
        str(runtime.base_dir),
        "gui",
        "--session-id",
        runtime.session_id,
    ]
    return run_cmd, gui_cmd


def cmd_ensure_services(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    session_meta = runtime.read_session()
    logs_dir = Path(runtime.base_dir) / "logs" / runtime.session_id
    run_log = Path(session_meta.get("runtime_log") or logs_dir / "runtime.log")
    gui_log = Path(session_meta.get("gui_log") or logs_dir / "gui.log")

    run_pid = session_meta.get("run_pid")
    gui_pid = session_meta.get("gui_pid")
    run_restarted = False
    gui_restarted = False
    run_cmd, gui_cmd = _service_commands(runtime)

    if not _pid_is_alive(run_pid):
        run_pid = _spawn_background(run_cmd, run_log)
        run_restarted = True

    if not args.no_gui and not _pid_is_alive(gui_pid):
        gui_pid = _spawn_background(gui_cmd, gui_log)
        gui_restarted = True

    runtime.update_session_meta(
        run_pid=run_pid,
        gui_pid=None if args.no_gui else gui_pid,
        runtime_log=str(run_log),
        gui_log="" if args.no_gui else str(gui_log),
    )

    payload = {
        "session_id": runtime.session_id,
        "run_pid": run_pid,
        "gui_pid": None if args.no_gui else gui_pid,
        "runtime_log": str(run_log),
        "gui_log": "" if args.no_gui else str(gui_log),
        "run_restarted": run_restarted,
        "gui_restarted": gui_restarted,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_event(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    payload = {"type": args.type, "source": args.source}
    if args.text:
        payload["text"] = args.text
    if args.role:
        payload["role"] = args.role
    if args.phase:
        payload["phase"] = args.phase
    if args.status:
        payload["status"] = args.status
    if args.student_mode:
        payload["student_mode"] = args.student_mode
    if args.checkpoint:
        payload["checkpoint"] = args.checkpoint
    if args.waiting_reason:
        payload["waiting_reason"] = args.waiting_reason
    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path
    if args.latest_transcript_path:
        payload["latest_transcript_path"] = args.latest_transcript_path
    if args.last_public_content_at:
        payload["last_public_content_at"] = args.last_public_content_at
    runtime.enqueue_event(payload)
    if args.process:
        runtime.process_inbox_once()
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    try:
        from .gui import launch_gui
    except ModuleNotFoundError as exc:
        if exc.name == "tkinter":
            raise SystemExit("tkinter is not installed in this environment; the GUI cannot be launched here.") from exc
        raise

    runtime = resolve_runtime(args.session_id, args.base_dir)
    launch_gui(runtime.session_id, base_dir=runtime.base_dir)
    return 0


def cmd_select_student(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    state = runtime.select_student_turn(
        args.prompt or "",
        source_priority=args.source_priority,
        checkpoint=args.checkpoint,
        waiting_reason=args.waiting_reason,
    )
    print(json.dumps(runtime.resume_info() | {"session_id": state["session_id"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_submit_student(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    text = args.text.strip()
    if not text:
        raise SystemExit("Student utterance cannot be empty.")
    runtime.enqueue_event(
        {
            "type": "UTTERANCE_SUBMITTED",
            "source": args.source,
            "text": text,
        }
    )
    runtime.process_inbox_once()
    print(json.dumps(runtime.resume_info(), ensure_ascii=False, indent=2))
    return 0


def cmd_wait_student(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    pending = runtime.wait_for_student_utterance(
        timeout_seconds=args.timeout,
        poll_interval=args.interval,
    )
    if pending is None:
        print(json.dumps({"status": "timeout"}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ok", **pending}, ensure_ascii=False, indent=2))
    return 0


def cmd_consume_student(args: argparse.Namespace) -> int:
    runtime = resolve_runtime(args.session_id, args.base_dir)
    pending = runtime.consume_student_utterance()
    if pending is None:
        print(json.dumps({"status": "empty"}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ok", **pending}, ensure_ascii=False, indent=2))
    return 0


def _spawn_background(command: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            command,
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    return proc.pid


def cmd_bootstrap(args: argparse.Namespace) -> int:
    runtime = SessionRuntime.create(topic=args.topic, student_mode=args.student_mode, base_dir=args.base_dir)
    logs_dir = Path(runtime.base_dir) / "logs" / runtime.session_id
    run_log = logs_dir / "runtime.log"
    gui_log = logs_dir / "gui.log"

    run_cmd, gui_cmd = _service_commands(runtime)
    run_pid = _spawn_background(run_cmd, run_log)

    gui_pid = None
    if not args.no_gui:
        gui_pid = _spawn_background(gui_cmd, gui_log)

    runtime.update_session_meta(
        run_pid=run_pid,
        gui_pid=gui_pid,
        runtime_log=str(run_log),
        gui_log=str(gui_log) if not args.no_gui else "",
    )
    runtime.update_status("waiting_for_orchestrator")
    runtime.update_orchestrator_state(
        checkpoint="bootstrap",
        waiting_reason="awaiting_orchestrator_resume",
    )

    payload = {
        "session_id": runtime.session_id,
        "run_pid": run_pid,
        "gui_pid": gui_pid,
        "runtime_log": str(run_log),
        "gui_log": str(gui_log) if not args.no_gui else "",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="User-participatory PBL runtime helpers")
    parser.add_argument("--base-dir", default="data/runtime", help="Runtime storage root")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Create a new user-participatory session")
    init_parser.add_argument("--topic", required=True)
    init_parser.add_argument("--student-mode", default="hybrid", choices=["agent_only", "human_only", "hybrid"])
    init_parser.set_defaults(func=cmd_init)

    bootstrap_parser = sub.add_parser("bootstrap", help="Create a session and start runtime services")
    bootstrap_parser.add_argument("--topic", required=True)
    bootstrap_parser.add_argument("--student-mode", default="hybrid", choices=["agent_only", "human_only", "hybrid"])
    bootstrap_parser.add_argument("--no-gui", action="store_true")
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    ensure_parser = sub.add_parser("ensure-services", help="Ensure runtime and GUI services are running")
    ensure_parser.add_argument("--session-id")
    ensure_parser.add_argument("--no-gui", action="store_true")
    ensure_parser.set_defaults(func=cmd_ensure_services)

    run_parser = sub.add_parser("run", help="Continuously process inbox events")
    run_parser.add_argument("--session-id")
    run_parser.add_argument("--interval", type=float, default=0.5)
    run_parser.set_defaults(func=cmd_run)

    tick_parser = sub.add_parser("tick", help="Process inbox events once")
    tick_parser.add_argument("--session-id")
    tick_parser.set_defaults(func=cmd_tick)

    snapshot_parser = sub.add_parser("snapshot", help="Print current state")
    snapshot_parser.add_argument("--session-id")
    snapshot_parser.add_argument("--json", action="store_true")
    snapshot_parser.set_defaults(func=cmd_snapshot)

    resume_parser = sub.add_parser("resume-info", help="Print resumable orchestrator state")
    resume_parser.add_argument("--session-id")
    resume_parser.add_argument("--latest", action="store_true")
    resume_parser.set_defaults(func=cmd_resume_info)

    phase_parser = sub.add_parser("phase", help="Update current discussion phase")
    phase_parser.add_argument("--session-id")
    phase_parser.add_argument("--phase", required=True)
    phase_parser.set_defaults(func=cmd_phase)

    status_parser = sub.add_parser("status", help="Update runtime status")
    status_parser.add_argument("--session-id")
    status_parser.add_argument("--status", required=True)
    status_parser.set_defaults(func=cmd_status)

    checkpoint_parser = sub.add_parser("checkpoint", help="Update orchestrator checkpoint state")
    checkpoint_parser.add_argument("--session-id")
    checkpoint_parser.add_argument("--checkpoint")
    checkpoint_parser.add_argument("--waiting-reason")
    checkpoint_parser.add_argument("--transcript-path")
    checkpoint_parser.add_argument("--latest-transcript-path")
    checkpoint_parser.add_argument("--last-public-content-at")
    checkpoint_parser.set_defaults(func=cmd_checkpoint)

    init_transcripts_parser = sub.add_parser("init-transcripts", help="Initialize realtime transcript files")
    init_transcripts_parser.add_argument("--session-id")
    init_transcripts_parser.add_argument("--topic")
    init_transcripts_parser.add_argument("--transcript-path")
    init_transcripts_parser.add_argument("--latest-transcript-path")
    init_transcripts_parser.set_defaults(func=cmd_init_transcripts)

    append_parser = sub.add_parser("append-public", help="Append public markdown to transcript files")
    append_parser.add_argument("--session-id")
    append_parser.add_argument("--markdown", required=True)
    append_parser.set_defaults(func=cmd_append_public)

    complete_parser = sub.add_parser("complete-session", help="Mark session complete and clear current pointer")
    complete_parser.add_argument("--session-id")
    complete_parser.add_argument("--status", default="completed", choices=["completed", "cancelled"])
    complete_parser.set_defaults(func=cmd_complete_session)

    event_parser = sub.add_parser("event", help="Enqueue a runtime event")
    event_parser.add_argument("--session-id")
    event_parser.add_argument("--type", required=True)
    event_parser.add_argument("--source", default="manual")
    event_parser.add_argument("--text")
    event_parser.add_argument("--role")
    event_parser.add_argument("--phase")
    event_parser.add_argument("--status")
    event_parser.add_argument("--student-mode", choices=["agent_only", "human_only", "hybrid"])
    event_parser.add_argument("--checkpoint")
    event_parser.add_argument("--waiting-reason")
    event_parser.add_argument("--transcript-path")
    event_parser.add_argument("--latest-transcript-path")
    event_parser.add_argument("--last-public-content-at")
    event_parser.add_argument("--process", action="store_true")
    event_parser.set_defaults(func=cmd_event)

    gui_parser = sub.add_parser("gui", help="Launch the local tkinter GUI")
    gui_parser.add_argument("--session-id")
    gui_parser.set_defaults(func=cmd_gui)

    select_parser = sub.add_parser("select-student", help="Mark student as selected to speak")
    select_parser.add_argument("--session-id")
    select_parser.add_argument("--source-priority", default="human")
    select_parser.add_argument("--prompt")
    select_parser.add_argument("--checkpoint", default="waiting_for_student_turn")
    select_parser.add_argument("--waiting-reason", default="awaiting_student_utterance")
    select_parser.set_defaults(func=cmd_select_student)

    submit_parser = sub.add_parser("submit-student", help="Submit a student utterance from chat")
    submit_parser.add_argument("--session-id")
    submit_parser.add_argument("--source", default="chat")
    submit_parser.add_argument("--text", required=True)
    submit_parser.set_defaults(func=cmd_submit_student)

    wait_parser = sub.add_parser("wait-student", help="Wait for a pending student utterance")
    wait_parser.add_argument("--session-id")
    wait_parser.add_argument("--timeout", type=float, default=60.0)
    wait_parser.add_argument("--interval", type=float, default=0.5)
    wait_parser.set_defaults(func=cmd_wait_student)

    consume_parser = sub.add_parser("consume-student", help="Consume the current student utterance")
    consume_parser.add_argument("--session-id")
    consume_parser.set_defaults(func=cmd_consume_student)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
