"""Manage the shared Agent work index without replacing project state sources."""

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPEN = {"active", "waiting", "blocked"}
TRANSITIONS = {
    "active": OPEN | {"done", "cancelled"},
    "waiting": {"active", "blocked", "cancelled"},
    "blocked": {"active", "cancelled"},
}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
    path = root / ".orbitos/state/work-items.lock"
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
            raise ValueError(f"work state lock timed out: {path}")
        time.sleep(0.05)
    try:
        yield
    finally:
        unlock(handle)
        handle.close()


def load(root):
    path = root / ".orbitos/state/work-items.json"
    if not path.is_file():
        raise ValueError(f"work state is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("items"), dict):
        raise ValueError("work state must have version=1 and object items")
    return data


def save(root, data):
    data["updated_at"] = now()
    (root / ".orbitos/state/work-items.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def item(data, work_id):
    if work_id not in data["items"]:
        raise ValueError(f"work item not found: {work_id}")
    return data["items"][work_id]


def check_revision(record, expected):
    if expected is not None and record["revision"] != expected:
        raise ValueError(f"revision conflict: expected {expected}, actual {record['revision']}")


def main():
    parser = argparse.ArgumentParser(description="Manage the OrbitOS Agent work index.")
    parser.add_argument("--root", default=None)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create")
    create.add_argument("--id", dest="work_id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--project", required=True)
    create.add_argument("--agent-id")
    create.add_argument("--source-type", choices=("project_task", "issue", "handoff", "maintenance", "confirmation"), required=True)
    create.add_argument("--source-ref", required=True)
    create.add_argument("--next-action", required=True)
    create.add_argument("--requires-user", action="store_true")

    claim = commands.add_parser("claim")
    claim.add_argument("--id", dest="work_id", required=True)
    claim.add_argument("--agent-id", required=True)
    claim.add_argument("--expected-revision", type=int)
    claim.add_argument("--lease-seconds", type=int, default=900)

    update = commands.add_parser("update")
    update.add_argument("--id", dest="work_id", required=True)
    update.add_argument("--agent-id", required=True)
    update.add_argument("--expected-revision", type=int, required=True)
    update.add_argument("--status", choices=sorted(OPEN | {"done", "cancelled"}), required=True)
    update.add_argument("--next-action", required=True)
    update.add_argument("--evidence")
    update.add_argument("--source-ref")
    update.add_argument("--requires-user", action="store_true", default=None)
    update.add_argument("--no-user-required", action="store_false", dest="requires_user")

    listing = commands.add_parser("list")
    listing.add_argument("--agent-id")
    listing.add_argument("--project")
    listing.add_argument("--include-closed", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        with locked(root):
            data = load(root)
            if args.command == "create":
                if args.work_id in data["items"]:
                    raise ValueError(f"work item already exists: {args.work_id}")
                data["items"][args.work_id] = {
                    "work_id": args.work_id,
                    "agent_id": args.agent_id,
                    "project": args.project,
                    "title": args.title,
                    "source_type": args.source_type,
                    "source_ref": args.source_ref,
                    "status": "active" if args.agent_id else "waiting",
                    "next_action": args.next_action,
                    "requires_user": args.requires_user,
                    "blocked_reason": None,
                    "revision": 1,
                    "lease_owner": None,
                    "lease_until": None,
                    "evidence_refs": [],
                    "updated_at": now(),
                }
                save(root, data)
                result = {"ok": True, "item": data["items"][args.work_id]}
            elif args.command == "claim":
                record = item(data, args.work_id)
                check_revision(record, args.expected_revision)
                if record["status"] not in OPEN:
                    raise ValueError(f"cannot claim status={record['status']}")
                lease_until = record.get("lease_until")
                if lease_until and datetime.fromisoformat(lease_until) > datetime.now().astimezone() and record.get("lease_owner") != args.agent_id:
                    raise ValueError(f"work item is leased by {record['lease_owner']}")
                record["agent_id"] = args.agent_id
                record["lease_owner"] = args.agent_id
                record["lease_until"] = (datetime.now().astimezone() + timedelta(seconds=args.lease_seconds)).isoformat(timespec="seconds")
                record["status"] = "active"
                record["revision"] += 1
                record["updated_at"] = now()
                save(root, data)
                result = {"ok": True, "item": record}
            elif args.command == "update":
                record = item(data, args.work_id)
                check_revision(record, args.expected_revision)
                if record.get("lease_owner") not in (None, args.agent_id):
                    raise ValueError(f"work item is leased by {record['lease_owner']}")
                if args.status != record["status"] and args.status not in TRANSITIONS.get(record["status"], set()):
                    raise ValueError(f"illegal work transition: {record['status']} -> {args.status}")
                if args.status == "done" and not args.evidence:
                    raise ValueError("done requires completion evidence")
                if args.status == "done" and record.get("requires_user") and args.requires_user is not False:
                    raise ValueError("user-required work must be explicitly cleared before done")
                record["status"] = args.status
                record["next_action"] = args.next_action
                if args.source_ref:
                    record["source_ref"] = args.source_ref
                if args.requires_user is not None:
                    record["requires_user"] = args.requires_user
                record["blocked_reason"] = args.next_action if args.status == "blocked" else None
                if args.evidence:
                    record.setdefault("evidence_refs", []).append(args.evidence)
                if args.status in {"done", "cancelled"}:
                    record["lease_owner"] = None
                    record["lease_until"] = None
                record["revision"] += 1
                record["updated_at"] = now()
                save(root, data)
                result = {"ok": True, "item": record}
            else:
                records = list(data["items"].values())
                if not args.include_closed:
                    records = [record for record in records if record["status"] in OPEN]
                if args.agent_id:
                    records = [record for record in records if record.get("agent_id") == args.agent_id]
                if args.project:
                    records = [record for record in records if record.get("project") == args.project]
                records.sort(key=lambda record: (record.get("project", ""), record.get("work_id", "")))
                result = {"ok": True, "items": records}
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
