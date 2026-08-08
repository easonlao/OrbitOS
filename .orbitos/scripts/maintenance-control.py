"""Manage the single current OrbitOS maintenance state."""

import argparse
from contextlib import contextmanager
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path


OPEN_STATUSES = {"detected", "classified", "assigned", "repairing", "verifying", "blocked"}
VALID_STATUSES = OPEN_STATUSES | {"closed", "expired"}
REQUIRED_ITEM_FIELDS = {
    "maintenance_id",
    "subject",
    "status",
    "owner_agent",
    "executor",
    "attempt",
    "max_attempts",
    "revision",
    "lease_owner",
    "lease_until",
    "last_observed_at",
    "last_verified_at",
    "last_verification_receipt",
    "evidence_refs",
    "next_action",
    "requires_user",
    "updated_at",
    "blocked_reason",
}


class MaintenanceError(Exception):
    pass


def now_text():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def root_from_args(args):
    return Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]


def state_path(root):
    return root / ".orbitos/state/maintenance.json"


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
def maintenance_lock(root, timeout_seconds=10):
    """Serialize read-modify-write cycles across agents and executors."""
    lock_path = root / ".orbitos/state/maintenance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    while not try_lock(handle):
        if time.monotonic() >= deadline:
            handle.close()
            raise MaintenanceError(f"maintenance state lock timed out: {lock_path}")
        time.sleep(0.05)
    try:
        yield
    finally:
        unlock(handle)
        handle.close()


def load_state(root):
    path = state_path(root)
    if not path.is_file():
        raise MaintenanceError(f"maintenance state is missing: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MaintenanceError(f"maintenance state is invalid JSON: {error}") from error
    if not isinstance(state, dict) or state.get("version") != 1:
        raise MaintenanceError("maintenance state must have version=1")
    state.setdefault("items", {})
    state.setdefault("receipts", [])
    validate_state(state)
    return state


def validate_state(state):
    if not isinstance(state.get("items"), dict) or not isinstance(state.get("receipts"), list):
        raise MaintenanceError("maintenance state items/receipts have invalid types")
    for maintenance_id, item in state["items"].items():
        if not isinstance(item, dict) or not REQUIRED_ITEM_FIELDS.issubset(item):
            raise MaintenanceError(f"maintenance item is missing required fields: {maintenance_id}")
        if item["status"] not in VALID_STATUSES:
            raise MaintenanceError(f"invalid maintenance status: {item['status']}")
        if item["maintenance_id"] != maintenance_id:
            raise MaintenanceError(f"maintenance id key mismatch: {maintenance_id}")


def save_state(root, state):
    validate_state(state)
    state["updated_at"] = now_text()
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def get_item(state, maintenance_id):
    item = state.get("items", {}).get(maintenance_id)
    if not isinstance(item, dict):
        raise MaintenanceError(f"maintenance item not found: {maintenance_id}")
    return item


def require_revision(item, expected_revision):
    if expected_revision is None:
        raise MaintenanceError("mutating an existing item requires --expected-revision")
    if item.get("revision") != expected_revision:
        raise MaintenanceError(
            f"revision conflict: expected {expected_revision}, current {item.get('revision')}"
        )


def lease_active(item, when=None):
    lease_until = parse_time(item.get("lease_until"))
    return bool(lease_until and lease_until > (when or datetime.now().astimezone()))


def require_actor(item, actor):
    if not actor:
        raise MaintenanceError("this action requires --agent-id")
    if lease_active(item) and item.get("lease_owner") != actor:
        raise MaintenanceError(f"lease conflict: item is leased by {item.get('lease_owner')}")
    owner = item.get("owner_agent")
    if owner and owner not in {actor, "any", "automation-health"} and not lease_active(item):
        raise MaintenanceError(f"owner conflict: item belongs to {owner}")


def require_observer(item, observer):
    if lease_active(item) and item.get("lease_owner") != observer:
        raise MaintenanceError(f"lease conflict: item is leased by {item.get('lease_owner')}")


def bump(item):
    item["revision"] = int(item.get("revision", 0)) + 1
    item["updated_at"] = now_text()


def append_evidence(item, evidence, receipt_id=None):
    refs = item.setdefault("evidence_refs", [])
    for value in (receipt_id, evidence):
        if value and value not in refs:
            refs.append(value)


def base_item(args, observed_at):
    return {
        "maintenance_id": args.maintenance_id,
        "subject": args.subject,
        "status": "detected",
        "owner_agent": getattr(args, "owner_agent", None),
        "executor": getattr(args, "executor", None),
        "attempt": 0,
        "max_attempts": getattr(args, "max_attempts", 3),
        "revision": 1,
        "lease_owner": None,
        "lease_until": None,
        "last_observed_at": observed_at,
        "last_verified_at": None,
        "last_verification_receipt": None,
        "evidence_refs": [args.evidence],
        "next_action": getattr(args, "next_action", None),
        "requires_user": False,
        "updated_at": now_text(),
        "blocked_reason": None,
    }


def cmd_detect(args, root):
    state = load_state(root)
    observed_at = args.observed_at or now_text()
    existing = state.get("items", {}).get(args.maintenance_id)
    if existing:
        require_revision(existing, args.expected_revision)
        require_observer(existing, args.executor or args.owner_agent or "system")
        if args.owner_agent and existing.get("owner_agent") not in {None, args.owner_agent}:
            raise MaintenanceError("owner changes require assign or claim")
        preserve_user_block = existing.get("status") == "blocked" or existing.get("requires_user")
        existing.update(
            {
                "subject": args.subject,
                "executor": args.executor,
                "last_observed_at": observed_at,
                "last_verified_at": None,
                "last_verification_receipt": None,
            }
        )
        if not preserve_user_block:
            existing.update(
                {
                    "status": "detected",
                    "next_action": args.next_action,
                    "requires_user": False,
                    "blocked_reason": None,
                }
            )
        if args.owner_agent:
            existing["owner_agent"] = args.owner_agent
        append_evidence(existing, args.evidence)
        bump(existing)
        item = existing
    else:
        item = base_item(args, observed_at)
        state.setdefault("items", {})[args.maintenance_id] = item
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_classify(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    item["status"] = "classified"
    if args.owner_agent is not None:
        item["owner_agent"] = args.owner_agent
    if args.next_action is not None:
        item["next_action"] = args.next_action
    if args.requires_user:
        item["requires_user"] = True
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_claim(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    if lease_active(item) and item.get("lease_owner") != args.agent_id:
        raise MaintenanceError(f"lease conflict: item is leased by {item.get('lease_owner')}")
    lease_until = datetime.now().astimezone() + timedelta(seconds=args.lease_seconds)
    item["owner_agent"] = args.agent_id
    item["lease_owner"] = args.agent_id
    item["lease_until"] = lease_until.isoformat(timespec="seconds")
    item["status"] = "assigned"
    if args.executor is not None:
        item["executor"] = args.executor
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_record(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    phase = args.phase or (args.command if args.command in {"repair", "retry"} else None)
    if phase is None:
        raise MaintenanceError("record requires --phase repair|retry")
    item["attempt"] = int(item.get("attempt", 0)) + 1
    item["last_observed_at"] = args.observed_at or now_text()
    append_evidence(item, args.evidence, args.receipt_id)
    if args.executor is not None:
        item["executor"] = args.executor
    if item["attempt"] >= int(item.get("max_attempts", 3)):
        item["status"] = "blocked"
        item["requires_user"] = True
        item["blocked_reason"] = "attempt limit exceeded"
        item["next_action"] = "等待用户决定下一步"
        item["lease_owner"] = None
        item["lease_until"] = None
    else:
        item["status"] = "repairing"
        item["next_action"] = args.next_action or f"继续 {phase}"
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_verify(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    observed_at = args.observed_at or now_text()
    item["status"] = "verifying"
    item["last_observed_at"] = observed_at
    item["last_verified_at"] = observed_at
    item["last_verification_receipt"] = args.receipt_id
    item["next_action"] = "验证通过后关闭维护事项"
    item["requires_user"] = False
    append_evidence(item, args.evidence, args.receipt_id)
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_close(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    if item.get("status") != "verifying":
        raise MaintenanceError("close requires status=verifying")
    if item.get("last_verification_receipt") != args.verification_receipt:
        raise MaintenanceError("close requires the latest verification receipt")
    verified_at = parse_time(item.get("last_verified_at"))
    age_seconds = (datetime.now().astimezone() - verified_at).total_seconds() if verified_at else None
    if verified_at is None or age_seconds < 0 or age_seconds > args.max_age_seconds:
        raise MaintenanceError("close requires fresh verification evidence")
    item["status"] = "closed"
    item["requires_user"] = False
    item["next_action"] = None
    item["blocked_reason"] = None
    item["lease_owner"] = None
    item["lease_until"] = None
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_block(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    item["status"] = "blocked"
    item["requires_user"] = True
    item["blocked_reason"] = args.reason
    item["next_action"] = "等待用户决定下一步"
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_expire(args, root):
    state = load_state(root)
    item = get_item(state, args.maintenance_id)
    require_revision(item, args.expected_revision)
    require_actor(item, args.agent_id)
    item["status"] = "expired"
    item["requires_user"] = False
    item["blocked_reason"] = None
    item["next_action"] = "重新检测"
    item["lease_owner"] = None
    item["lease_until"] = None
    bump(item)
    save_state(root, state)
    emit({"ok": True, "item": item})


def cmd_reconcile(args, root):
    state = load_state(root)
    now = datetime.now().astimezone()
    expirable = {"detected", "classified", "assigned", "repairing", "verifying"}
    expired_ids = []
    for maintenance_id, item in state.get("items", {}).items():
        if item.get("status") not in expirable or item.get("requires_user") or lease_active(item, now):
            continue
        observed_at = parse_time(item.get("last_observed_at"))
        age_seconds = (now - observed_at).total_seconds() if observed_at else None
        if age_seconds is None or age_seconds <= args.max_age_seconds:
            continue
        item["status"] = "expired"
        item["requires_user"] = False
        item["blocked_reason"] = None
        item["next_action"] = "重新检测"
        item["lease_owner"] = None
        item["lease_until"] = None
        if args.executor is not None:
            item["executor"] = args.executor
        bump(item)
        expired_ids.append(maintenance_id)
    if expired_ids:
        save_state(root, state)
    emit({"ok": True, "expired": expired_ids})


def cmd_receipt(args, root):
    state = load_state(root)
    observed_at = args.observed_at or now_text()
    receipt_id = args.receipt_id or f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    receipt = {
        "id": receipt_id,
        "kind": args.kind,
        "executor": args.executor,
        "observed_at": observed_at,
        "status": args.status,
        "validation_command": args.validation_command,
        "evidence": args.evidence,
        "errors": args.error,
    }
    state.setdefault("receipts", []).append(receipt)
    state["receipts"] = state["receipts"][-100:]
    item = state.setdefault("items", {}).get(args.maintenance_id)
    actor = args.owner_agent or args.executor
    if args.status == "failed":
        if item is None:
            item = {
                "maintenance_id": args.maintenance_id,
                "subject": args.subject,
                "status": "detected",
                "owner_agent": args.owner_agent or "automation-health",
                "executor": args.executor,
                "attempt": 0,
                "max_attempts": args.max_attempts,
                "revision": 1,
                "lease_owner": None,
                "lease_until": None,
                "last_observed_at": observed_at,
                "last_verified_at": None,
                "last_verification_receipt": None,
                "evidence_refs": [receipt_id],
                "next_action": "修复 System Check 暴露的结构问题",
                "requires_user": False,
                "updated_at": now_text(),
                "blocked_reason": None,
            }
            state["items"][args.maintenance_id] = item
        elif not lease_active(item) or item.get("lease_owner") == actor:
            item.update(
                {
                    "subject": args.subject,
                    "status": "detected",
                    "executor": args.executor,
                    "last_observed_at": observed_at,
                    "last_verified_at": None,
                    "last_verification_receipt": None,
                    "next_action": "修复 System Check 暴露的结构问题",
                    "requires_user": False,
                    "blocked_reason": None,
                }
            )
            append_evidence(item, args.evidence, receipt_id)
            bump(item)
    elif args.maintenance_id == "system-check" and item and item.get("status") not in {"closed", "expired"}:
        if lease_active(item) and item.get("lease_owner") not in {None, actor}:
            raise MaintenanceError(f"lease conflict: item is leased by {item.get('lease_owner')}")
        item["status"] = "closed"
        item["last_observed_at"] = observed_at
        item["last_verified_at"] = observed_at
        item["last_verification_receipt"] = receipt_id
        item["requires_user"] = False
        item["next_action"] = None
        item["blocked_reason"] = None
        item["lease_owner"] = None
        item["lease_until"] = None
        append_evidence(item, args.evidence, receipt_id)
        bump(item)
    save_state(root, state)
    emit({"ok": True, "receipt": receipt, "item": item})


def cmd_get(args, root):
    state = load_state(root)
    emit({"ok": True, "item": get_item(state, args.maintenance_id)})


def cmd_list(args, root):
    state = load_state(root)
    items = list(state.get("items", {}).values())
    if not args.all:
        items = [item for item in items if item.get("status") in OPEN_STATUSES]
    emit({"ok": True, "items": items})


def add_id_revision(parser, required_revision=True):
    parser.add_argument("--id", dest="maintenance_id", required=True)
    parser.add_argument("--expected-revision", type=int, required=required_revision)


def build_parser():
    parser = argparse.ArgumentParser(description="Manage OrbitOS maintenance state.")
    parser.add_argument("--root", default=None, help="OrbitOS runtime root")
    commands = parser.add_subparsers(dest="command", required=True)

    for name in ("detect", "observe"):
        command = commands.add_parser(name, help="detect or observe a maintenance item")
        command.add_argument("--id", dest="maintenance_id", required=True)
        command.add_argument("--subject", required=True)
        command.add_argument("--evidence", required=True)
        command.add_argument("--observed-at")
        command.add_argument("--owner-agent")
        command.add_argument("--executor")
        command.add_argument("--next-action")
        command.add_argument("--max-attempts", type=int, default=3)
        command.add_argument("--expected-revision", type=int)
        command.set_defaults(handler=cmd_detect)

    command = commands.add_parser("classify", aliases=["assign"], help="classify and assign a maintenance item")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--owner-agent")
    command.add_argument("--next-action")
    command.add_argument("--requires-user", action="store_true")
    command.set_defaults(handler=cmd_classify)

    command = commands.add_parser("claim", help="claim a short maintenance lease")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--lease-seconds", type=int, default=300)
    command.add_argument("--executor")
    command.set_defaults(handler=cmd_claim)

    command = commands.add_parser("record", aliases=["repair", "retry"], help="record a repair or retry attempt")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--phase", choices=("repair", "retry"))
    command.add_argument("--evidence", required=True)
    command.add_argument("--receipt-id")
    command.add_argument("--observed-at")
    command.add_argument("--executor")
    command.add_argument("--next-action")
    command.set_defaults(handler=cmd_record)

    command = commands.add_parser("verify", help="record fresh verification evidence")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--evidence", required=True)
    command.add_argument("--receipt-id", required=True)
    command.add_argument("--observed-at")
    command.set_defaults(handler=cmd_verify)

    command = commands.add_parser("close", help="close after fresh verification")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--verification-receipt", required=True)
    command.add_argument("--max-age-seconds", type=int, default=3600)
    command.set_defaults(handler=cmd_close)

    command = commands.add_parser("block", help="block and request user confirmation")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.add_argument("--reason", required=True)
    command.set_defaults(handler=cmd_block)

    command = commands.add_parser("expire", help="expire stale maintenance state")
    add_id_revision(command)
    command.add_argument("--agent-id", required=True)
    command.set_defaults(handler=cmd_expire)

    command = commands.add_parser("reconcile", help="expire stale open maintenance state")
    command.add_argument("--max-age-seconds", type=int, default=86400)
    command.add_argument("--executor")
    command.set_defaults(handler=cmd_reconcile)

    command = commands.add_parser("receipt", help="record a runtime validation receipt")
    command.add_argument("--kind", default="system_check")
    command.add_argument("--status", choices=("passed", "failed"), required=True)
    command.add_argument("--executor", required=True)
    command.add_argument("--observed-at")
    command.add_argument("--receipt-id")
    command.add_argument("--evidence", required=True)
    command.add_argument("--validation-command")
    command.add_argument("--error", action="append", default=[])
    command.add_argument("--id", dest="maintenance_id", default="system-check")
    command.add_argument("--subject", default="System Check")
    command.add_argument("--owner-agent")
    command.add_argument("--max-attempts", type=int, default=3)
    command.set_defaults(handler=cmd_receipt)

    command = commands.add_parser("get", help="read one maintenance item")
    command.add_argument("--id", dest="maintenance_id", required=True)
    command.set_defaults(handler=cmd_get)

    command = commands.add_parser("list", help="list current maintenance items")
    command.add_argument("--all", action="store_true")
    command.set_defaults(handler=cmd_list)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        root = root_from_args(args)
        if args.handler in {cmd_get, cmd_list}:
            args.handler(args, root)
        else:
            with maintenance_lock(root):
                args.handler(args, root)
    except (MaintenanceError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
