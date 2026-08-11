"""Bind governed role sessions to handoffs and close the whole collaboration record."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_ROOT = Path("00-系统/agents/handoff")
ARCHIVE_ROOT = ACTIVE_ROOT / "archive"
# Keep filesystem literals ASCII-safe across Windows agent runtimes.
ACTIVE_ROOT = Path("00-" + "\u7cfb\u7edf/agents/handoff")
ARCHIVE_ROOT = ACTIVE_ROOT / "archive"
ROLES = {"coordinator", "researcher", "writer", "builder", "editor"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"handoff frontmatter is missing: {path}")
    values = dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", match.group(1), re.MULTILINE))
    return text, match, values


def update_frontmatter(path, changes):
    text, match, values = frontmatter(path)
    header = match.group(1)
    for key, value in changes.items():
        line = f"{key}: {value}"
        if re.search(rf"^{re.escape(key)}:\s*.*$", header, re.MULTILINE):
            header = re.sub(rf"^{re.escape(key)}:\s*.*$", line, header, flags=re.MULTILINE)
        else:
            header += f"\n{line}"
    path.write_text(f"---\n{header}\n---\n" + text[match.end():], encoding="utf-8", newline="\n")


def active_handoff(root, relative):
    path = (root / relative).resolve()
    active_root = (root / ACTIVE_ROOT).resolve()
    if active_root not in path.parents or path.suffix != ".md" or not path.is_file():
        raise ValueError("handoff must be an existing Markdown file under the active handoff directory")
    return path


def run(command, root):
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise ValueError(
            (result.stderr or "").strip()
            or (result.stdout or "").strip()
            or "subcommand failed"
        )
    return (result.stdout or "").strip()


def board_replace(root, stem, status, owner, next_action):
    path = root / "00-系统/agents/BOARD.md"
    text = path.read_text(encoding="utf-8")
    pattern = rf"^- \[\[handoff/{re.escape(stem)}\|([^\]]+)\]\].*$"
    replacement = rf"- [[handoff/{stem}|\1]] | 状态：{status} | 当前负责人：{owner} | 下一步：{next_action}"
    updated, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("handoff board entry is missing or ambiguous")
    path.write_text(updated, encoding="utf-8", newline="\n")


def board_remove(root, stem):
    path = root / "00-系统/agents/BOARD.md"
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(rf"^- \[\[handoff/{re.escape(stem)}\|[^\n]*\n?", "", text, flags=re.MULTILINE)
    if count > 1:
        raise ValueError("handoff board entry is ambiguous")
    if count == 0:
        return  # already removed; idempotent close
    if "## 当前交接\n\n##" in updated:
        updated = updated.replace("## 当前交接\n\n##", "## 当前交接\n\n暂无开放交接。\n\n##")
    path.write_text(updated, encoding="utf-8", newline="\n")


def work_record(root, work_id):
    record = read_json(root / ".orbitos/state/work-items.json")["items"].get(work_id)
    if not record:
        raise ValueError(f"work item not found: {work_id}")
    return record


def queue_payload(root, handoff_relative):
    """Return the queue projection, or None when the handoff has no queue plan.

    Failures (corrupt state, missing script) raise instead of being treated as
    "no queue", so begin/close fail closed when the queue is unreadable.
    """
    result = subprocess.run(
        [sys.executable, str(root / ".orbitos/scripts/handoff-queue.py"), "--root", str(root), "status", "--handoff", handoff_relative],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise ValueError(
            (result.stderr or "").strip()
            or (result.stdout or "").strip()
            or "handoff queue status failed"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"handoff queue status returned invalid JSON: {error}")
    return payload.get("queue")


def queue_or_die(root, handoff_relative, metadata):
    """Read the queue projection; fail closed when a handoff declares a plan
    that its projection no longer carries (record lost, state reset)."""
    queue = queue_payload(root, handoff_relative)
    if queue is None:
        declares_plan = (metadata.get("plan_status") or "").strip() not in {"", "none"}
        declares_stage = (metadata.get("current_stage") or "").strip() not in {"", "none"}
        if declares_plan or declares_stage:
            raise ValueError("handoff declares a queue plan but its projection is missing; refusing to bypass queue gates")
    return queue


def require_queue_position(root, handoff_relative, agent_id, role, metadata=None):
    """Reject governed work when the handoff has a queue the Agent is not
    positioned for; returns the queue projection (or None)."""
    queue = queue_or_die(root, handoff_relative, metadata or {})
    if queue is None:
        return None
    if queue.get("plan_status") != "confirmed":
        raise ValueError("queue plan must be user-confirmed before work begins")
    if queue.get("replans") and not queue["replans"][-1].get("confirmed_at"):
        raise ValueError("the latest re-plan is waiting for user confirmation")
    if queue.get("current_owner") != agent_id:
        raise ValueError(f"begin requires the current queue owner: {queue.get('current_owner')}")
    current_role = queue.get("current_role")
    if current_role and current_role != role:
        raise ValueError(f"begin requires the current queue role: {current_role}")
    return queue


def session_record(root, session_id):
    record = read_json(root / ".orbitos/state/collaboration-sessions.json")["sessions"].get(session_id)
    if not record:
        raise ValueError(f"collaboration session not found: {session_id}")
    return record


def begin(args, root):
    handoff = active_handoff(root, args.handoff)
    _text, _match, metadata = frontmatter(handoff)
    if metadata.get("handoff_status") not in {"delegated", "returned"}:
        raise ValueError("only delegated or returned handoffs can begin governed work")
    queue = require_queue_position(root, args.handoff, args.agent_id, args.role, metadata)
    stage_id = (queue or {}).get("current_stage")
    stage = (queue or {}).get("stages", {}).get(stage_id) if queue else None
    if stage is not None and stage["status"] != "complete" and stage.get("session_id") and stage["session_id"] != args.session_id:
        raise ValueError(f"stage {stage_id} is already bound to session {stage['session_id']}; do not begin a second session for the same stage")
    work = work_record(root, args.work_id)
    if work["source_type"] != "handoff" or work["source_ref"] != args.handoff:
        raise ValueError("work item must point to this handoff")
    if work["revision"] != args.expected_work_revision:
        raise ValueError(f"work revision conflict: expected {args.expected_work_revision}, actual {work['revision']}")
    command = [sys.executable, str(root / ".orbitos/scripts/collab-session.py"), "--root", str(root), "open", "--session-id", args.session_id, "--mode", "multi_agent_claim", "--task-ref", args.handoff, "--project", work["project"], "--agent-id", args.agent_id, "--role", args.role, "--lease-seconds", str(args.lease_seconds)]
    if args.source_session_id:
        command += ["--source-session-id", args.source_session_id]
    if args.review_target_session_id:
        command += ["--review-target-session-id", args.review_target_session_id]
    run(command, root)
    run([sys.executable, str(root / ".orbitos/scripts/work-control.py"), "--root", str(root), "claim", "--id", args.work_id, "--agent-id", args.agent_id, "--expected-revision", str(args.expected_work_revision), "--lease-seconds", str(args.lease_seconds)], root)
    if stage is not None and stage["status"] != "complete":
        # Bind the governed session to the stage projection so a later advance
        # can only use the session this begin created.
        run([sys.executable, str(root / ".orbitos/scripts/handoff-queue.py"), "--root", str(root), "bind-session", "--handoff", args.handoff, "--stage-id", stage_id, "--session-id", args.session_id, "--date", args.date], root)
    update_frontmatter(handoff, {"updated": args.date, "handoff_status": "working", "current_owner": args.agent_id, "next_action": args.next_action, "governance_required": "true", "collaboration_session_id": args.session_id})
    board_replace(root, handoff.stem, "working", args.agent_id, args.next_action)
    print(json.dumps({"ok": True, "handoff": args.handoff, "session_id": args.session_id}))


def _write_close_receipt(root, handoff_relative, accepted_by, archived_ref):
    """Persist the acceptance receipt in the queue projection (idempotent).

    The receipt is only ever written from the governed close path; there is no
    public command that can forge it.
    """
    path = root / ".orbitos/state/handoff-queues.json"
    data = read_json(path)
    record = data["queues"].get(handoff_relative)
    if record is None:
        raise ValueError("handoff has no queue plan")
    if record.get("close"):
        return
    if record.get("plan_status") != "confirmed":
        raise ValueError("close receipt requires a user-confirmed queue plan")
    if record.get("replans") and not record["replans"][-1].get("confirmed_at"):
        raise ValueError("the latest re-plan is still waiting for user confirmation")
    incomplete = [
        stage_id
        for stage_id in record.get("stage_order", [])
        if record.get("stages", {}).get(stage_id, {}).get("status") != "complete"
    ]
    if incomplete:
        raise ValueError(f"close receipt requires all planned stages complete; pending: {incomplete}")
    if record.get("return_owner") != accepted_by:
        raise ValueError("close receipt must be issued by the authoritative return owner")
    if record.get("current_owner") != accepted_by:
        raise ValueError("close receipt requires the return owner to hold the baton")
    if not archived_ref.startswith("00-" + "\u7cfb\u7edf/agents/handoff/archive/"):
        raise ValueError("close receipt archive reference must live under the archive directory")
    record["close"] = {
        "accepted_by": accepted_by,
        "accepted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "archived_ref": archived_ref,
    }
    record["updated_at"] = record["close"]["accepted_at"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def close(args, root):
    # Recoverable, idempotent close: if the handoff is already archived, the
    # retry continues the remaining steps (work item, event, validation)
    # instead of pretending success. Every path still re-verifies the
    # governance hard gate, so a missing work item or event fails loudly
    # instead of returning success.
    try:
        handoff = active_handoff(root, args.handoff)
        archived = False
    except ValueError:
        archive_candidate = root / ARCHIVE_ROOT / Path(args.handoff).name
        if not archive_candidate.is_file():
            raise
        handoff = archive_candidate
        archived = True
    _text, _match, metadata = frontmatter(handoff)
    if metadata.get("return_owner") != args.agent_id:
        raise ValueError("only the return owner can accept and close this handoff")
    if metadata.get("collaboration_session_id") != args.session_id:
        raise ValueError("handoff is not bound to this collaboration session")
    session = session_record(root, args.session_id)
    if session["status"] != "closed" or not session["gate_state"]["hard_gate_passed"]:
        raise ValueError("handoff close requires a closed collaboration session that passed hard gates")
    if session["agent_id"] != args.agent_id:
        raise ValueError("only the session owner can close its handoff")
    queue = queue_or_die(root, args.handoff, metadata)
    for output in args.output:
        if not re.match(r"^[^|]+\|[^|]+(\|[^|]+)*$", output):
            raise ValueError(f"output must use KIND|REF|STATUS[|NOTE]: {output}")
    archive_relative = (ARCHIVE_ROOT / Path(args.handoff).name).as_posix()
    archive_path = root / archive_relative
    if not archived and archive_path.exists():
        raise ValueError("archive target already exists")
    # The queue gates (confirmed plan, latest re-plan confirmed, all stages
    # complete, return owner holds the baton, archive target location) live in
    # _write_close_receipt as the single source of truth; close never repeats
    # them so the gates cannot drift apart. The receipt is written on the first
    # pass before the archive move and re-applied on recovery (idempotent).
    if queue is not None:
        _write_close_receipt(root, args.handoff, args.agent_id, archive_relative)
    # idempotent close-out: frontmatter + board are safe to re-apply on recovery
    update_frontmatter(handoff, {"updated": args.date, "handoff_status": "closed", "current_owner": args.agent_id, "next_action": "无。协作已完成并归档。"})
    board_remove(root, handoff.stem)
    if not archived:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(handoff), str(archive_path))
    # work item close-out (idempotent when already done; a missing work item
    # fails the close instead of being silently skipped)
    work = work_record(root, args.work_id)
    if work["status"] != "done":
        run([sys.executable, str(root / ".orbitos/scripts/work-control.py"), "--root", str(root), "update", "--id", args.work_id, "--agent-id", args.agent_id, "--expected-revision", str(args.expected_work_revision), "--status", "done", "--next-action", "closed and archived", "--source-ref", archive_relative, "--evidence", f".orbitos/state/collaboration-sessions.json#{args.session_id}", "--no-user-required"], root)
    validation = run([sys.executable, str(root / ".orbitos/scripts/run-validation.py")], root)
    if "Validation eval passed" not in validation:
        raise ValueError("post-close validation did not pass")
    events_root = root / ".orbitos/logs/events"
    if events_root.is_dir() and not any(args.slug in path.name for path in events_root.glob("*.yaml")):
        event_command = [sys.executable, str(root / ".orbitos/scripts/write_event.py"), "--agent-id", args.agent_id, "--role", session["role"], "--slug", args.slug, "--summary", args.summary, "--reason", args.reason, "--project", work["project"], "--event-type", "progress_sync", "--file", f"moved:{args.handoff}:closed handoff archived", "--file", f"updated:.orbitos/state/work-items.json:closed work item source migrated", "--collaboration-session", args.session_id, "--review-status", session.get("review", {}).get("status", "not_required"), "--validation", "passed", "--thinking-bypassed"]
        if session.get("review", {}).get("status") == "approved":
            event_command += ["--reviewer-session", session["review"].get("reviewer_session_id"), "--reviewer-agent", session["review"].get("reviewer_agent_id")]
        for output in args.output:
            event_command += ["--output", output]
        event_ref = run(event_command, root)
    else:
        event_ref = None
    final_validation = run([sys.executable, str(root / ".orbitos/scripts/run-validation.py")], root)
    if "Validation eval passed" not in final_validation:
        raise ValueError("final validation did not pass")
    print(json.dumps({"ok": True, "handoff": archive_relative, "event_ref": event_ref, "already_closed": archived}))


def parser():
    root = argparse.ArgumentParser(description="Bind governed sessions to formal handoffs and close them consistently.")
    root.add_argument("--root")
    commands = root.add_subparsers(dest="command", required=True)
    beginning = commands.add_parser("begin")
    beginning.add_argument("--handoff", required=True)
    beginning.add_argument("--work-id", required=True)
    beginning.add_argument("--expected-work-revision", type=int, required=True)
    beginning.add_argument("--agent-id", required=True)
    beginning.add_argument("--role", choices=sorted(ROLES), required=True)
    beginning.add_argument("--session-id", required=True)
    beginning.add_argument("--source-session-id")
    beginning.add_argument("--review-target-session-id")
    beginning.add_argument("--next-action", required=True)
    beginning.add_argument("--date", required=True)
    beginning.add_argument("--lease-seconds", type=int, default=900)
    closing = commands.add_parser("close")
    closing.add_argument("--handoff", required=True)
    closing.add_argument("--work-id", required=True)
    closing.add_argument("--expected-work-revision", type=int, required=True)
    closing.add_argument("--agent-id", required=True)
    closing.add_argument("--session-id", required=True)
    closing.add_argument("--summary", required=True)
    closing.add_argument("--reason", required=True)
    closing.add_argument("--slug", required=True)
    closing.add_argument("--output", action="append", required=True)
    closing.add_argument("--date", required=True)
    return root


def main():
    args = parser().parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        if args.command == "begin":
            begin(args, root)
        else:
            close(args, root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
