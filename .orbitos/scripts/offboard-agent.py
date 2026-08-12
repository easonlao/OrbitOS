"""Offboard a registered agent from OrbitOS: four-step lifecycle close-out (issue #24).

Fixed four-step sequence (see .orbitos/workflows/agent-offboarding.md):
  ① status_cleanup      registry entry status -> "offboarding" (write-back immediately)
  ② resource_release    move profile / experience / env into 99-归档/agents-{id}-{YYYYMMDD}/
  ③ dependency_unbind   mark open work items / collaboration sessions / handoffs as
                        "负责人已注销" (mark only, never auto-transfer)
  ④ record_finalize     registry -> "offboarded" (+offboarded_at/offboard_reason/
                        offboard_exception), README list sync, write event

Idempotency / recovery (progress inferred from registry status, no progress file):
  - status=offboarded + archive dir + event present  -> already_offboarded short-circuit
  - status=offboarded but archive dir missing        -> patch step ② only
  - status=offboarded but event missing              -> patch step ④ only
  - status=offboarding                               -> step ① done, resume ②③④
Every write path (including recovery) requires --confirm.

run-validation is intentionally NOT a hard gate here: once an agent is offboarded,
run-validation's agent-collaboration-evidence check exempts status=offboarded /
offboarding entries (profile archive expected), and the offboarded entry's own
integrity is covered by the actual.offboarding-consistency eval case.
The offboard event uses event_type=agent_offboarding (event schema enum extended).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYS_DIR = "00-系统"
ARCHIVE_DIR = "99-归档"
AGENTS_SUB = "agents"
UNBIND_MARK = "负责人已注销"
UNBIND_ACTION = f"{UNBIND_MARK}，待人工裁决（user）"
OPEN_WORK = {"active", "waiting", "blocked"}
OPEN_SESSION = {"open", "claimed", "working", "review_required", "returned", "blocked"}
OPEN_HANDOFF = {"delegated", "working", "returned"}


class UsageError(Exception):
    """Bad arguments / confirmation / agent or registry lookup failure -> exit 1."""


class RetryableError(Exception):
    """Recoverable I/O failure (moves, writes, event) -> exit 2."""


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def try_lock(handle):
    handle.seek(0)
    if os.name == "nt":
        import msvcrt
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def unlock(handle):
    handle.seek(0)
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked(root, timeout_seconds=10):
    """Serialise offboarding writes with .orbitos/state/offboard-agent.lock."""
    path = root / ".orbitos/state/offboard-agent.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout_seconds
    while not try_lock(handle):
        if time.monotonic() >= deadline:
            handle.close()
            raise RetryableError(f"offboard lock timed out: {path}")
        time.sleep(0.05)
    try:
        yield
    finally:
        unlock(handle)
        handle.close()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def read_registry(root):
    path = root / ".orbitos/agents/registry.yaml"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read agent registry {path}: {error}")
    if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
        raise UsageError(f"agent registry has invalid structure: {path}")
    return data


def write_registry(root, registry):
    path = root / ".orbitos/agents/registry.yaml"
    try:
        write_json(path, registry)
    except OSError as error:
        raise RetryableError(f"cannot write agent registry {path}: {error}")


def find_agent(registry, agent_id):
    for item in registry.get("agents", []):
        if isinstance(item, dict) and item.get("agent_id") == agent_id:
            return item
    raise UsageError(f"agent is not in registry: {agent_id}")


def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"frontmatter is missing: {path}")
    values = dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", match.group(1), re.MULTILINE))
    return text, match, values


def update_frontmatter(path, changes):
    text, match, values = read_frontmatter(path)
    header = match.group(1)
    for key, value in changes.items():
        line = f"{key}: {value}"
        if re.search(rf"^{re.escape(key)}:\s*.*$", header, re.MULTILINE):
            header = re.sub(rf"^{re.escape(key)}:\s*.*$", line, header, flags=re.MULTILINE)
        else:
            header += f"\n{line}"
    path.write_text(
        f"---\n{header}\n---\n" + text[match.end():],
        encoding="utf-8",
        newline="\n",
    )


def mark_profile_archived(path):
    """Rewrite lifecycle: archived on the archived profile copy (never the source)."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        path.write_text(f"---\nlifecycle: archived\n---\n{text}", encoding="utf-8", newline="\n")
        return
    header = match.group(1)
    if re.search(r"^lifecycle:", header, re.MULTILINE):
        header = re.sub(r"^lifecycle:.*$", "lifecycle: archived", header, flags=re.MULTILINE)
    else:
        header += "\nlifecycle: archived"
    path.write_text(
        f"---\n{header}\n---\n" + text[match.end():],
        encoding="utf-8",
        newline="\n",
    )


def board_remove(root, stem):
    path = root / f"{SYS_DIR}/agents/BOARD.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(rf"^- \[\[handoff/{re.escape(stem)}\|[^\n]*\n?", "", text, flags=re.MULTILINE)
    if count > 1:
        raise RetryableError("handoff board entry is ambiguous")
    if count == 0:
        return  # already removed; idempotent
    if "## 当前交接\n\n##" in updated:
        updated = updated.replace("## 当前交接\n\n##", "## 当前交接\n\n暂无开放交接。\n\n##")
    path.write_text(updated, encoding="utf-8", newline="\n")


def event_exists(root, slug):
    events = root / ".orbitos/logs/events"
    if not events.is_dir():
        return False
    return any(f"_{slug}.yaml" in name.name for name in events.glob("*.yaml"))


def archive_rel(agent_id, date_str):
    return f"{ARCHIVE_DIR}/agents-{agent_id}-{date_str}"


def new_plan():
    return {
        "steps": {
            "status_cleanup": "pending",
            "resource_release": "pending",
            "dependency_unbind": "pending",
            "record_finalize": "pending",
        },
        "archive_dir": None,
        "dependencies": {"work_items": 0, "collaboration_sessions": 0, "handoffs": 0},
        "moved_files": [],
        "skipped": [],
        "event_ref": None,
        "already_offboarded": False,
        "recovery": None,
    }


# ---------------------------------------------------------------------------
# Step ① status_cleanup
# ---------------------------------------------------------------------------
def step_status_cleanup(root, registry, entry, date):
    # Only ever touch status (deployment / profile_ref / last_seen stay intact).
    entry["status"] = "offboarding"
    registry["updated"] = date
    write_registry(root, registry)


# ---------------------------------------------------------------------------
# Step ② resource_release
# ---------------------------------------------------------------------------
def step_resource_release(root, args, plan, date_str):
    agent_id = args.agent_id
    archive = root / archive_rel(agent_id, date_str)
    plan["archive_dir"] = archive.relative_to(root).as_posix()
    try:
        archive.mkdir(parents=True, exist_ok=True)  # reuse existing dir, never wipe
    except OSError as error:
        if args.exception:
            plan["skipped"].append(f"archive_dir: {error}")
            plan["steps"]["resource_release"] = "done"
            return
        raise RetryableError(f"cannot create archive dir {archive}: {error}")
    sources = [
        (root / f"{SYS_DIR}/agents/{agent_id}.md", archive / f"{agent_id}.md", "profile"),
        (root / f"{SYS_DIR}/agents/{agent_id}-experience.md", archive / f"{agent_id}-experience.md", "experience"),
        (root / f".orbitos/state/env/{agent_id}.json", archive / f"env-{agent_id}.json", "env"),
    ]
    for src, dst, kind in sources:
        if not src.is_file():
            plan["skipped"].append(f"{kind}: missing")
            continue
        if dst.exists():
            plan["skipped"].append(f"{kind}: exists (already archived)")
            continue
        try:
            shutil.move(str(src), str(dst))
        except OSError as error:
            if args.exception:
                plan["skipped"].append(f"{kind}: {error}")
                continue
            raise RetryableError(f"failed to archive {kind} of {agent_id}: {error}")
        plan["moved_files"].append(
            (src.relative_to(root).as_posix(), dst.relative_to(root).as_posix())
        )
        if kind == "profile":
            mark_profile_archived(dst)
    plan["steps"]["resource_release"] = "done"


# ---------------------------------------------------------------------------
# Step ③ dependency_unbind (mark only, never auto-transfer)
# ---------------------------------------------------------------------------
def unbind_work_items(root, args, plan):
    path = root / ".orbitos/state/work-items.json"
    try:
        data = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise RetryableError(f"work-items state unreadable: {error}")
    changed = False
    for record in data.get("items", {}).values():
        if record.get("status") not in OPEN_WORK or record.get("agent_id") != args.agent_id:
            continue
        if record.get("agent_id") is None or UNBIND_MARK in (record.get("next_action") or ""):
            continue  # already unbound
        record["agent_id"] = None
        record["next_action"] = UNBIND_ACTION
        record["requires_user"] = True
        record["lease_owner"] = None
        record["lease_until"] = None
        record["revision"] = record.get("revision", 0) + 1
        record["updated_at"] = now()
        plan["dependencies"]["work_items"] += 1
        changed = True
    if changed:
        try:
            write_json(path, data)
        except OSError as error:
            if args.exception:
                plan["skipped"].append(f"work_items write: {error}")
            else:
                raise RetryableError(f"failed to write work-items.json: {error}")


def unbind_sessions(root, args, plan):
    path = root / ".orbitos/state/collaboration-sessions.json"
    try:
        data = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise RetryableError(f"collaboration session state unreadable: {error}")
    changed = False
    for record in data.get("sessions", {}).values():
        if record.get("status") not in OPEN_SESSION or record.get("agent_id") != args.agent_id:
            continue
        if record.get("status") == "blocked" and UNBIND_MARK in (
            (record.get("return_reason") or "") + (record.get("blocked_reason") or "")
        ):
            continue  # already closed out
        record["status"] = "blocked"  # keep record + agent_id for history
        record["return_reason"] = f"{UNBIND_MARK}，待人工裁决"
        record["lease_owner"] = None
        record["lease_until"] = None
        record["revision"] = record.get("revision", 0) + 1
        record["updated_at"] = now()
        plan["dependencies"]["collaboration_sessions"] += 1
        changed = True
    if changed:
        try:
            write_json(path, data)
        except OSError as error:
            if args.exception:
                plan["skipped"].append(f"collaboration_sessions write: {error}")
            else:
                raise RetryableError(f"failed to write collaboration-sessions.json: {error}")


def unbind_handoffs(root, args, plan):
    handoff_dir = root / f"{SYS_DIR}/agents/handoff"
    if not handoff_dir.is_dir():
        return
    for path in sorted(handoff_dir.glob("*.md")):
        try:
            _text, _match, meta = read_frontmatter(path)
        except ValueError as error:
            plan["skipped"].append(f"handoff frontmatter unreadable: {path.name}")
            continue
        if meta.get("handoff_status") not in OPEN_HANDOFF or meta.get("current_owner") != args.agent_id:
            continue
        if not meta.get("current_owner") or UNBIND_MARK in (meta.get("next_action") or ""):
            continue  # already unbound
        update_frontmatter(path, {"current_owner": "", "next_action": f"{UNBIND_MARK}，待人工裁决"})
        try:
            board_remove(root, path.stem)
        except RetryableError as error:
            if args.exception:
                plan["skipped"].append(f"board_remove {path.stem}: {error}")
            else:
                raise
        plan["dependencies"]["handoffs"] += 1


def step_dependency_unbind(root, args, plan):
    unbind_work_items(root, args, plan)
    unbind_sessions(root, args, plan)
    unbind_handoffs(root, args, plan)
    if sum(plan["dependencies"].values()) == 0:
        plan["steps"]["dependency_unbind"] = "skipped"
    else:
        plan["steps"]["dependency_unbind"] = "done"


# ---------------------------------------------------------------------------
# Step ④ record_finalize (registry offboarded + README + event)
# ---------------------------------------------------------------------------
def update_readme(root, agent_id, date, plan):
    path = root / f"{SYS_DIR}/agents/README.md"
    if not path.is_file():
        plan["skipped"].append("README: missing")
        return
    text = path.read_text(encoding="utf-8")
    # 1) remove the agent bullet from the "当前 Agents" list (idempotent)
    text = re.sub(rf"^- \[\[{re.escape(agent_id)}\|[^\n]*\n?", "", text, flags=re.MULTILINE)
    # 2) remove the id from the backtick registry list line (idempotent)
    def _without_agent(m):
        rest = [i for i in m.group(1).split(" / ") if i != agent_id]
        return "`" + (" / ".join(rest) if rest else "（无）") + "`"
    text = re.sub(
        r"`([a-z0-9_]+(?: / [a-z0-9_]+)*)`",
        _without_agent,
        text,
    )
    # 3) keep a human-readable history note (idempotent)
    note_line = f"- `{agent_id}`：{date} 注销。"
    if "## 已注销" in text:
        if not re.search(rf"^- `{re.escape(agent_id)}`", text, re.MULTILINE):
            text = text.rstrip() + "\n" + note_line + "\n"
    else:
        text = text.rstrip() + "\n\n## 已注销\n\n" + note_line + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def write_event(root, args, plan):
    slug = f"offboard_{args.agent_id}"
    script = root / ".orbitos/scripts/write_event.py"
    if not script.is_file():
        raise RetryableError(f"write_event.py is missing: {script}")
    command = [
        sys.executable, str(script),
        "--agent-id", args.agent_id,
        "--slug", slug,
        "--summary", f"agent offboarded: {args.agent_id}",
        "--reason", args.reason,
        "--project", "OrbitOS",
        "--event-type", "agent_offboarding",
        "--validation", "not_required",
        "--thinking-bypassed",
    ]
    for source, dest in plan["moved_files"]:
        command += ["--file", f"moved:{source}:archived to {dest}"]
    if plan.get("archive_dir"):
        # Archive directory is an output artifact, not a files_changed entry;
        # "archived" is not a valid change_type/status enum value.
        command += ["--output", f"artifact|{plan['archive_dir']}|created"]
    if args.exception:
        command += [
            "--review-required",
            "--review-item", "offboard_exception=true 的终态需用户人工复核",
        ]
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise RetryableError(
            (result.stderr or "").strip() or (result.stdout or "").strip() or "write_event failed"
        )
    return (result.stdout or "").strip()


def step_record_finalize(root, args, registry, entry, plan, date_str, date):
    if entry.get("status") != "offboarded":
        # First finalize: record the offboard fields.
        entry["status"] = "offboarded"
        entry["offboarded_at"] = date
        entry["offboard_reason"] = args.reason
        entry["offboard_exception"] = bool(args.exception)
    # Recovery re-run: entry already offboarded -> keep first offboarded_at/reason.
    registry["updated"] = date
    write_registry(root, registry)
    update_readme(root, args.agent_id, date, plan)
    slug = f"offboard_{args.agent_id}"
    if not event_exists(root, slug):
        plan["event_ref"] = write_event(root, args, plan)
    plan["steps"]["record_finalize"] = "done"


# ---------------------------------------------------------------------------
# offboard / status commands
# ---------------------------------------------------------------------------
def build_result(args, plan):
    return {
        "ok": True,
        "agent_id": args.agent_id,
        "status": "offboarded",
        "already_offboarded": plan["already_offboarded"],
        "steps": plan["steps"],
        "archive_dir": plan["archive_dir"],
        "dependencies": plan["dependencies"],
        "skipped": plan["skipped"],
        "event_ref": plan["event_ref"],
        "recovery": plan["recovery"],
    }


def cmd_offboard(args, root):
    if args.dry_run:
        return dry_run(args, root)
    # Confirmation gate: every write path (including recovery) requires it.
    if not args.confirm:
        raise UsageError("offboard requires --confirm (user confirmation)")
    if args.exception and not args.confirm_exception:
        raise UsageError("--exception requires --confirm-exception (second confirmation for partial resource release)")

    with locked(root):
        registry = read_registry(root)
        entry = find_agent(registry, args.agent_id)
        status = entry.get("status") or "active"
        date = today()
        date_str = (entry.get("offboarded_at") or date).replace("-", "")
        plan = new_plan()

        if status == "offboarded":
            # Idempotent short-circuit / tail-patch path.
            plan["already_offboarded"] = True
            plan["archive_dir"] = archive_rel(args.agent_id, date_str)
            event_missing = not event_exists(root, f"offboard_{args.agent_id}")
            if (root / plan["archive_dir"]).is_dir() and not event_missing:
                for name in plan["steps"]:
                    plan["steps"][name] = "skipped"
                return build_result(args, plan)
            if not (root / plan["archive_dir"]).is_dir():
                plan["recovery"] = "patch_step2"
                step_resource_release(root, args, plan, date_str)
            if event_missing:
                plan["recovery"] = "patch_step4"
                step_record_finalize(root, args, registry, entry, plan, date_str, entry.get("offboarded_at") or date)
            return build_result(args, plan)

        # status == active (fresh offboard) or offboarding (resume after ①)
        if status == "offboarding":
            plan["recovery"] = "resume_234"
            plan["steps"]["status_cleanup"] = "done"  # ① completed by prior run
        else:
            step_status_cleanup(root, registry, entry, date)
            plan["steps"]["status_cleanup"] = "done"
        step_resource_release(root, args, plan, date_str)  # ②
        step_dependency_unbind(root, args, plan)          # ③
        step_record_finalize(root, args, registry, entry, plan, date_str, date)  # ④
        return build_result(args, plan)


def dry_run(args, root):
    registry = read_registry(root)
    entry = find_agent(registry, args.agent_id)
    status = entry.get("status") or "active"
    if status == "offboarded":
        date_str = (entry.get("offboarded_at") or today()).replace("-", "")
        planned = []
        if not (root / archive_rel(args.agent_id, date_str)).is_dir():
            planned.append("resource_release (patch: archive dir missing)")
        if not event_exists(root, f"offboard_{args.agent_id}"):
            planned.append("record_finalize (patch: event missing)")
    else:
        planned = ["status_cleanup", "resource_release", "dependency_unbind", "record_finalize"]
    return {
        "ok": True,
        "dry_run": True,
        "agent_id": args.agent_id,
        "status": status,
        "already_offboarded": status == "offboarded",
        "planned_steps": planned,
    }


def count_dependencies(root, agent_id):
    deps = {"work_items": 0, "collaboration_sessions": 0, "handoffs": 0}
    try:
        data = read_json(root / ".orbitos/state/work-items.json")
        deps["work_items"] = sum(
            1 for record in data.get("items", {}).values()
            if record.get("status") in OPEN_WORK and record.get("agent_id") == agent_id
        )
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    try:
        data = read_json(root / ".orbitos/state/collaboration-sessions.json")
        deps["collaboration_sessions"] = sum(
            1 for record in data.get("sessions", {}).values()
            if record.get("status") in OPEN_SESSION and record.get("agent_id") == agent_id
        )
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    handoff_dir = root / f"{SYS_DIR}/agents/handoff"
    if handoff_dir.is_dir():
        for path in handoff_dir.glob("*.md"):
            try:
                _text, _match, meta = read_frontmatter(path)
                if meta.get("handoff_status") in OPEN_HANDOFF and meta.get("current_owner") == agent_id:
                    deps["handoffs"] += 1
            except ValueError:
                pass
    return deps


def cmd_status(args, root):
    registry = read_registry(root)
    entry = find_agent(registry, args.agent_id)
    status = entry.get("status") or "active"
    date_str = (entry.get("offboarded_at") or today()).replace("-", "")
    archive_dir = archive_rel(args.agent_id, date_str)
    return {
        "ok": True,
        "agent_id": args.agent_id,
        "status": status,
        "offboarded_at": entry.get("offboarded_at"),
        "offboard_reason": entry.get("offboard_reason"),
        "offboard_exception": entry.get("offboard_exception", False),
        "archive_dir_exists": (root / archive_dir).is_dir(),
        "dependencies": count_dependencies(root, args.agent_id),
        "already_offboarded": status == "offboarded" and (root / archive_dir).is_dir(),
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Offboard a registered agent from OrbitOS (four-step lifecycle close-out)."
    )
    parser.add_argument("--root", default=None)
    commands = parser.add_subparsers(dest="command", required=True)

    offboard = commands.add_parser("offboard", help="execute the four-step offboarding flow (idempotent, recoverable)")
    offboard.add_argument("--agent-id", required=True, help="registered registry agent_id")
    offboard.add_argument("--reason", required=True, help="human-readable offboard reason (-> offboard_reason / event reason)")
    offboard.add_argument("--exception", action="store_true", help="exceptional offboarding: partial release allowed, event review_required=true")
    offboard.add_argument("--confirm", default=None, help="required user confirmation for any write path, including recovery")
    offboard.add_argument("--confirm-exception", default=None, help="required second confirmation when --exception is set")
    offboard.add_argument("--dry-run", action="store_true", help="only report planned steps; write nothing")

    status = commands.add_parser("status", help="read-only offboarding status report")
    status.add_argument("--agent-id", required=True)
    return parser


def main():
    args = build_parser().parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        if args.command == "offboard":
            result = cmd_offboard(args, root)
        else:
            result = cmd_status(args, root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except UsageError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except RetryableError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
