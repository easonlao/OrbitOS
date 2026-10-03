"""Manage collaboration sessions and role claims without replacing business state sources."""

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_CATALOG = ".orbitos/module-packages/collaboration/roles.json"
STATE = ".orbitos/state/collaboration-sessions.json"
SCHEMA = ".orbitos/schemas/collaboration-sessions.schema.yaml"
OPEN = {"open", "claimed", "working", "review_required", "returned", "blocked"}
TRANSITIONS = {
    "open": {"claimed", "working", "returned", "blocked", "closed"},
    "claimed": {"working", "review_required", "returned", "blocked", "closed"},
    "working": {"working", "review_required", "returned", "blocked", "closed"},
    "review_required": {"returned", "blocked", "closed"},
    "returned": {"claimed", "working", "blocked"},
    "blocked": {"claimed", "working", "returned"},
    "closed": set(),
}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path):
    if not path.is_file():
        raise ValueError(f"missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(root, relative):
    return root / relative


def registered_agents(root):
    candidates = [
        resolve(root, ".orbitos/agents/registry.yaml"),
        resolve(root, ".orbitos/templates/.orbitos/agents/registry.yaml"),
    ]
    for path in candidates:
        if path.is_file():
            registry = read_json(path)
            return {
                item.get("agent_id")
                for item in registry.get("agents", [])
                if isinstance(item, dict) and (item.get("status") or "active") == "active"
            }
    raise ValueError("agent registry is missing")


def roles(root):
    catalog = read_json(resolve(root, ROLE_CATALOG))
    return catalog.get("roles", {})


def load(root):
    path = resolve(root, STATE)
    data = read_json(path)
    if data.get("version") != 1 or not isinstance(data.get("sessions"), dict):
        raise ValueError("collaboration session state must have version=1 and object sessions")
    return data


def save(root, data):
    data["updated_at"] = now()
    resolve(root, STATE).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get(data, session_id):
    if session_id not in data["sessions"]:
        raise ValueError(f"session not found: {session_id}")
    return data["sessions"][session_id]


def check_revision(record, expected):
    if expected is not None and record["revision"] != expected:
        raise ValueError(f"revision conflict: expected {expected}, actual {record['revision']}")


def lease_valid(record):
    until = record.get("lease_until")
    return bool(until and datetime.fromisoformat(until) > datetime.now().astimezone())


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
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked(root, timeout_seconds=10):
    path = resolve(root, ".orbitos/state/collaboration-sessions.lock")
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
            raise ValueError(f"collaboration session lock timed out: {path}")
        time.sleep(0.05)
    try:
        yield
    finally:
        unlock(handle)
        handle.close()


def validate_identity(root, agent_id, role):
    if agent_id not in registered_agents(root):
        raise ValueError(f"agent is not registered: {agent_id}")
    if role not in roles(root):
        raise ValueError(f"role is not registered: {role}")


EVIDENCE_KINDS = {
    "primary_doc",
    "runtime_receipt",
    "validation_run",
    "source_quote",
    "human_confirmed",
    "external_primary",
    "agent_inference",
}
SOURCE_STATES = {"current_primary", "current_snapshot", "secondary", "archived", "stale", "unknown"}
VERIFICATION_STATUSES = {"unverified", "source_checked", "reproduced", "independently_reviewed", "contradicted"}


def parse_evidence(raw, actor_agent_id, allow_review=False):
    parts = raw.split("|", 3)
    if len(parts) != 4 or not all(part.strip() for part in parts):
        raise ValueError("evidence must use ref|evidence_kind|source_state|verification_status")
    ref, evidence_kind, source_state, verification_status = [part.strip() for part in parts]
    if evidence_kind not in EVIDENCE_KINDS:
        raise ValueError(f"unsupported evidence_kind: {evidence_kind}")
    if source_state not in SOURCE_STATES:
        raise ValueError(f"unsupported source_state: {source_state}")
    if verification_status not in VERIFICATION_STATUSES:
        raise ValueError(f"unsupported verification_status: {verification_status}")
    if not allow_review and verification_status in {"independently_reviewed", "contradicted"}:
        raise ValueError("researcher cannot self-submit independent_reviewed or contradicted evidence")
    if evidence_kind == "agent_inference" and verification_status != "unverified":
        raise ValueError("agent_inference must remain unverified")
    return {
        "ref": ref,
        "evidence_kind": evidence_kind,
        "source_state": source_state,
        "verification_status": verification_status,
        "actor_agent_id": actor_agent_id,
        "observed_at": now(),
    }


def derive_research(evidence):
    if not evidence:
        return {"confidence_tier": "red", "source_state": "unknown", "verification_status": "unverified", "evidence_count": 0, "submitted_at": now()}
    if all(item["evidence_kind"] == "agent_inference" for item in evidence):
        tier = "red"
    elif any(item["verification_status"] == "contradicted" for item in evidence):
        tier = "red"
    elif any(item["source_state"] in {"stale", "unknown", "archived"} for item in evidence) and not any(item["source_state"] in {"current_primary", "current_snapshot"} for item in evidence):
        tier = "red"
    elif any(
        (item["verification_status"] == "reproduced" and item["evidence_kind"] in {"runtime_receipt", "validation_run"})
        or (item["evidence_kind"] == "human_confirmed")
        or (item["source_state"] == "current_primary" and item["verification_status"] == "independently_reviewed")
        for item in evidence
    ):
        tier = "green"
    elif any(item["source_state"] in {"current_primary", "current_snapshot"} and item["verification_status"] in {"source_checked", "reproduced"} for item in evidence):
        tier = "yellow"
    else:
        tier = "red"
    source_order = {"current_primary": 0, "current_snapshot": 1, "secondary": 2, "archived": 3, "stale": 4, "unknown": 5}
    verification_order = {"reproduced": 0, "independently_reviewed": 1, "source_checked": 2, "user_confirmed": 3, "unverified": 4, "contradicted": 5}
    source_state = min((item["source_state"] for item in evidence), key=source_order.get)
    verification_status = min((item["verification_status"] for item in evidence), key=verification_order.get)
    return {
        "confidence_tier": tier,
        "source_state": source_state,
        "verification_status": verification_status,
        "evidence_count": len(evidence),
        "submitted_at": now(),
    }


def research_ready(record):
    if record["role"] in {"coordinator", "editor"}:
        return True
    return record["research"]["confidence_tier"] == "green"


def recompute_gate(record):
    gate = record["gate_state"]
    gate["review_status"] = record["review"]["status"]
    gate["lease_valid"] = lease_valid(record)
    gate["evidence_present"] = bool(record.get("evidence"))
    gate["research_ready"] = research_ready(record)
    gate["hard_gate_passed"] = (
        gate["schema_valid"]
        and gate["role_valid"]
        and gate["lease_valid"]
        and gate["evidence_present"]
        and gate["research_ready"]
        and (not gate["review_required"] or gate["review_status"] == "approved")
    )


def downstream_source(root, data, args):
    if args.role not in {"writer", "builder"}:
        if args.source_session_id:
            raise ValueError("source_session_id is only valid for writer or builder")
        return None
    if not args.source_session_id:
        raise ValueError(f"{args.role} requires source_session_id")
    source = get(data, args.source_session_id)
    if source["role"] != "researcher" or source["project"] != args.project or source["task_ref"] != args.task_ref:
        raise ValueError("downstream source must be a Researcher session for the same project and task_ref")
    if source["status"] not in {"returned", "review_required", "closed"}:
        raise ValueError("Researcher must submit its result before downstream role can claim it")
    if source["research"]["confidence_tier"] != "green":
        raise ValueError("yellow/red research cannot flow into writer or builder")
    return source


def parent_for(root, data, parent_id, agent_id):
    parent = get(data, parent_id)
    if parent["agent_id"] != agent_id:
        raise ValueError("single-agent child session must use the parent agent")
    if parent["status"] == "closed":
        raise ValueError("cannot create a child session under a closed parent")
    return parent


def initial_record(args, root, data):
    validate_identity(root, args.agent_id, args.role)
    if args.session_id in data["sessions"]:
        raise ValueError(f"session already exists: {args.session_id}")
    if args.mode == "single_agent_subsession":
        if not args.parent_session_id:
            raise ValueError("single_agent_subsession requires parent_session_id")
        parent_for(root, data, args.parent_session_id, args.agent_id)
    elif args.parent_session_id:
        raise ValueError("multi_agent_claim cannot declare parent_session_id")
    review_target = None
    if args.role == "editor":
        if args.source_session_id:
            raise ValueError("editor uses review_target_session_id, not source_session_id")
        if not args.review_target_session_id:
            raise ValueError("editor requires review_target_session_id")
        review_target = get(data, args.review_target_session_id)
        if review_target["role"] not in {"writer", "builder"}:
            raise ValueError("Editor can only review a Writer or Builder session")
        if review_target["project"] != args.project or review_target["task_ref"] != args.task_ref:
            raise ValueError("review target must use the same project and task_ref")
        if review_target["status"] != "review_required" or review_target["gate_state"]["review_status"] != "pending":
            raise ValueError("review target must be in review_required with a pending review")
        if review_target["agent_id"] == args.agent_id:
            raise ValueError("Editor cannot review the same agent's session")
    elif args.review_target_session_id:
        raise ValueError("review_target_session_id is only valid for editor")
    source = downstream_source(root, data, args)
    timestamp = now()
    lease_until = (datetime.now().astimezone() + timedelta(seconds=args.lease_seconds)).isoformat(timespec="seconds")
    return {
        "session_id": args.session_id,
        "parent_session_id": args.parent_session_id,
        "mode": args.mode,
        "task_ref": args.task_ref,
        "project": args.project,
        "agent_id": args.agent_id,
        "role": args.role,
        "source_session_id": source["session_id"] if source else None,
        "review_target_session_id": review_target["session_id"] if review_target else None,
        "status": "claimed",
        "lease_owner": args.agent_id,
        "lease_until": lease_until,
        "revision": 1,
        "evidence_refs": [],
        "evidence": [],
        "research": {
            "confidence_tier": "red",
            "source_state": "unknown",
            "verification_status": "unverified",
            "evidence_count": 0,
            "submitted_at": None,
        },
        "return_reason": None,
        "return_target_session_id": None,
        "return_count": 0,
        "review": {
            "status": "pending" if args.role in {"writer", "builder"} else "not_required",
            "reviewer_session_id": None,
            "reviewer_agent_id": None,
            "evidence_refs": [],
            "reason": None,
            "reviewed_at": None,
        },
        "gate_state": {
            "schema_valid": True,
            "role_valid": True,
            "lease_valid": True,
            "evidence_present": False,
            "research_ready": bool(source) or args.role in {"coordinator", "editor"},
            "review_required": args.role in {"writer", "builder"},
            "review_status": "pending" if args.role in {"writer", "builder"} else "not_required",
            "hard_gate_passed": False,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def claim_record(record, root, data, agent_id, lease_seconds):
    validate_identity(root, agent_id, record["role"])
    if record["status"] == "closed":
        raise ValueError("cannot claim a closed session")
    if record["mode"] == "single_agent_subsession" and record.get("parent_session_id"):
        parent_for(root, data, record["parent_session_id"], agent_id)
    if record["role"] in {"writer", "builder"}:
        source = get(data, record["source_session_id"])
        if source["research"]["confidence_tier"] != "green":
            raise ValueError("yellow/red research cannot flow into writer or builder")
    if lease_valid(record) and record.get("lease_owner") not in (None, agent_id):
        raise ValueError(f"session is leased by {record['lease_owner']}")
    record["agent_id"] = agent_id
    record["lease_owner"] = agent_id
    record["lease_until"] = (datetime.now().astimezone() + timedelta(seconds=lease_seconds)).isoformat(timespec="seconds")
    record["status"] = "claimed"
    record["revision"] += 1
    record["updated_at"] = now()
    recompute_gate(record)


def submit_research(record, args):
    if record["role"] != "researcher":
        raise ValueError("submit-research requires a researcher session")
    if record["status"] not in {"claimed", "working", "returned", "blocked"}:
        raise ValueError(f"cannot submit research from status={record['status']}")
    if record.get("lease_owner") != args.agent_id:
        raise ValueError(f"session is leased by {record.get('lease_owner')}")
    new_evidence = [parse_evidence(raw, args.agent_id) for raw in args.evidence]
    if not new_evidence:
        raise ValueError("submit-research requires typed evidence")
    record.setdefault("evidence", []).extend(new_evidence)
    record.setdefault("evidence_refs", []).extend(item["ref"] for item in new_evidence)
    record["research"] = derive_research(record["evidence"])
    record["status"] = "returned"
    record["lease_owner"] = None
    record["lease_until"] = None
    record["return_reason"] = None
    record["return_target_session_id"] = None
    record["revision"] += 1
    record["updated_at"] = now()
    recompute_gate(record)


def update_record(record, args):
    if record["status"] == "closed":
        raise ValueError("closed session is immutable")
    if record.get("lease_owner") != args.agent_id:
        raise ValueError(f"session is leased by {record['lease_owner']}")
    if args.status != record["status"] and args.status not in TRANSITIONS.get(record["status"], set()):
        raise ValueError(f"illegal session transition: {record['status']} -> {args.status}")
    if args.evidence:
        evidence = parse_evidence(args.evidence, args.agent_id)
        record.setdefault("evidence", []).append(evidence)
        record.setdefault("evidence_refs", []).append(evidence["ref"])
        record["research"] = derive_research(record["evidence"])
    if args.status in {"returned", "blocked"}:
        if not args.reason:
            raise ValueError(f"{args.status} requires --reason")
        record["return_reason"] = args.reason
        record["return_target_session_id"] = args.target_session_id
        record["return_count"] = record.get("return_count", 0) + 1
    if args.status == "review_required":
        record["review"]["status"] = "pending"
        record["review"]["reviewer_session_id"] = None
        record["review"]["reviewer_agent_id"] = None
        record["review"]["evidence_refs"] = []
        record["review"]["reason"] = None
        record["review"]["reviewed_at"] = None
        record["gate_state"]["review_required"] = True
        record["gate_state"]["review_status"] = "pending"
    recompute_gate(record)
    gate = record["gate_state"]
    if args.status == "closed":
        if gate["review_required"] and gate["review_status"] != "approved":
            raise ValueError("review-required session cannot close before review approval")
        if not gate["hard_gate_passed"]:
            raise ValueError("session close requires evidence and all hard gates")
        record["lease_owner"] = None
        record["lease_until"] = None
    else:
        record["lease_owner"] = args.agent_id
    record["status"] = args.status
    record["revision"] += 1
    record["updated_at"] = now()


def submit_review(record, data, root, args):
    if record["role"] != "editor":
        raise ValueError("review requires an editor session")
    if record.get("lease_owner") != args.agent_id:
        raise ValueError(f"session is leased by {record.get('lease_owner')}")
    if not lease_valid(record):
        raise ValueError("review requires a valid Editor lease")
    target = get(data, record.get("review_target_session_id"))
    check_revision(target, args.target_expected_revision)
    if target["role"] not in {"writer", "builder"}:
        raise ValueError("Editor can only review a Writer or Builder session")
    if target["project"] != record["project"] or target["task_ref"] != record["task_ref"]:
        raise ValueError("review target must use the same project and task_ref")
    if target["status"] != "review_required" or target["gate_state"]["review_status"] != "pending":
        raise ValueError("review target must be in review_required with a pending review")
    if target["agent_id"] == args.agent_id:
        raise ValueError("Editor cannot review the same agent's session")
    if not target["gate_state"]["evidence_present"]:
        raise ValueError("review target must provide evidence before Editor review")
    evidence = [parse_evidence(raw, args.agent_id, allow_review=True) for raw in args.evidence]
    if not evidence:
        raise ValueError("review requires typed evidence")
    if args.decision == "approved" and not any(item["verification_status"] == "independently_reviewed" for item in evidence):
        raise ValueError("approved review requires independently_reviewed evidence")
    if args.decision == "rejected" and not args.reason:
        raise ValueError("rejected review requires --reason")

    record["evidence"].extend(evidence)
    record["evidence_refs"].extend(item["ref"] for item in evidence)
    record["research"] = derive_research(record["evidence"])
    # As in update_record(closed), retain the gate snapshot taken BEFORE
    # releasing the lease. A completed rejection is not handoff acceptance.
    recompute_gate(record)
    record["gate_state"]["hard_gate_passed"] &= args.decision == "approved"
    record["status"] = "closed"
    record["lease_owner"] = None
    record["lease_until"] = None
    record["revision"] += 1
    record["updated_at"] = now()

    target["review"]["status"] = args.decision
    target["review"]["reviewer_session_id"] = record["session_id"]
    target["review"]["reviewer_agent_id"] = args.agent_id
    target["review"]["evidence_refs"] = [item["ref"] for item in evidence]
    target["review"]["reason"] = args.reason
    target["review"]["reviewed_at"] = now()
    target["gate_state"]["review_status"] = args.decision
    if args.decision == "rejected":
        target["status"] = "returned"
        target["return_reason"] = args.reason
        target["return_target_session_id"] = None
        target["return_count"] = target.get("return_count", 0) + 1
    target["revision"] += 1
    target["updated_at"] = now()
    recompute_gate(target)


def repair_review_close(record, data, root, args):
    """Revalidate an old approved Editor closure; never reopen/change a review.

    This explicit owner-only recovery appends fresh independent evidence and
    refreshes the derived gate cache. It does not repair arbitrary closed
    sessions or infer approval from the cache being repaired.
    """
    validate_identity(root, args.agent_id, "editor")
    if record["role"] != "editor" or record["status"] != "closed" or record["agent_id"] != args.agent_id:
        raise ValueError("repair requires the owner of a closed Editor session")
    if record.get("lease_owner") or record.get("lease_until"):
        raise ValueError("closed Editor repair requires no outstanding lease")
    target = get(data, record.get("review_target_session_id"))
    check_revision(target, args.target_expected_revision)
    review = target["review"]
    if (target["role"] not in {"writer", "builder"}
            or target["agent_id"] == args.agent_id
            or target["project"] != record["project"] or target["task_ref"] != record["task_ref"]
            or target["status"] not in {"review_required", "closed"}
            or review["status"] != "approved"
            or review["reviewer_session_id"] != record["session_id"]
            or review["reviewer_agent_id"] != args.agent_id
            or not review.get("reviewed_at") or not target.get("evidence")):
        raise ValueError("repair requires the matching independent approved review")
    original_refs = {item["ref"] for item in record.get("evidence", [])
                     if item["actor_agent_id"] == args.agent_id
                     and item["verification_status"] == "independently_reviewed"}
    if not original_refs.intersection(review.get("evidence_refs", [])):
        raise ValueError("repair requires original independent review evidence")
    if record["review"]["status"] != "not_required" or record["gate_state"]["review_required"]:
        raise ValueError("repair cannot bypass a pending review gate")
    evidence = parse_evidence(args.evidence, args.agent_id, allow_review=True)
    if evidence["verification_status"] != "independently_reviewed":
        raise ValueError("repair requires fresh independently_reviewed evidence")
    if record["gate_state"]["hard_gate_passed"]:
        return  # idempotent, after checking the approval chain
    record["evidence"].append(evidence)
    record["evidence_refs"].append(evidence["ref"])
    record["research"] = derive_research(record["evidence"])
    # Hold a fresh recovery lease under the state lock, evaluate the normal
    # gates, then release it without persisting an open/claimed state.
    record["lease_owner"] = args.agent_id
    record["lease_until"] = (datetime.now().astimezone() + timedelta(seconds=60)).isoformat(timespec="seconds")
    recompute_gate(record)
    if not record["gate_state"]["hard_gate_passed"]:
        raise ValueError("repair requires all existing hard gates")
    record["lease_owner"] = None
    record["lease_until"] = None
    record["revision"] += 1
    record["updated_at"] = now()


def main():
    parser = argparse.ArgumentParser(description="Manage OrbitOS collaboration sessions and role claims.")
    parser.add_argument("--root", default=None)
    commands = parser.add_subparsers(dest="command", required=True)

    opening = commands.add_parser("open")
    opening.add_argument("--session-id", required=True)
    opening.add_argument("--parent-session-id")
    opening.add_argument("--mode", choices=("single_agent_subsession", "multi_agent_claim"), required=True)
    opening.add_argument("--task-ref", required=True)
    opening.add_argument("--project", required=True)
    opening.add_argument("--agent-id", required=True)
    opening.add_argument("--role", required=True)
    opening.add_argument("--source-session-id")
    opening.add_argument("--review-target-session-id")
    opening.add_argument("--lease-seconds", type=int, default=900)

    claiming = commands.add_parser("claim")
    claiming.add_argument("--session-id", required=True)
    claiming.add_argument("--agent-id", required=True)
    claiming.add_argument("--expected-revision", type=int, required=True)
    claiming.add_argument("--lease-seconds", type=int, default=900)

    heartbeat = commands.add_parser("heartbeat")
    heartbeat.add_argument("--session-id", required=True)
    heartbeat.add_argument("--agent-id", required=True)
    heartbeat.add_argument("--expected-revision", type=int, required=True)
    heartbeat.add_argument("--lease-seconds", type=int, default=900)

    updating = commands.add_parser("update")
    updating.add_argument("--session-id", required=True)
    updating.add_argument("--agent-id", required=True)
    updating.add_argument("--expected-revision", type=int, required=True)
    updating.add_argument("--status", choices=sorted(set(TRANSITIONS) | {"closed"}), required=True)
    updating.add_argument("--evidence")
    updating.add_argument("--reason")
    updating.add_argument("--target-session-id")

    research_submit = commands.add_parser("submit-research")
    research_submit.add_argument("--session-id", required=True)
    research_submit.add_argument("--agent-id", required=True)
    research_submit.add_argument("--expected-revision", type=int, required=True)
    research_submit.add_argument("--evidence", action="append", required=True)

    reviewing = commands.add_parser("review")
    reviewing.add_argument("--session-id", required=True)
    reviewing.add_argument("--agent-id", required=True)
    reviewing.add_argument("--expected-revision", type=int, required=True)
    reviewing.add_argument("--target-expected-revision", type=int, required=True)
    reviewing.add_argument("--decision", choices=("approved", "rejected"), required=True)
    reviewing.add_argument("--evidence", action="append", required=True)
    reviewing.add_argument("--reason")

    repairing = commands.add_parser("repair-review-close")
    repairing.add_argument("--session-id", required=True)
    repairing.add_argument("--agent-id", required=True)
    repairing.add_argument("--expected-revision", type=int, required=True)
    repairing.add_argument("--target-expected-revision", type=int, required=True)
    repairing.add_argument("--evidence", required=True)

    listing = commands.add_parser("list")
    listing.add_argument("--agent-id")
    listing.add_argument("--project")
    listing.add_argument("--task-ref")
    listing.add_argument("--include-closed", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        with locked(root):
            data = load(root)
            if args.command == "open":
                record = initial_record(args, root, data)
                data["sessions"][args.session_id] = record
                save(root, data)
                result = {"ok": True, "session": record}
            elif args.command == "claim":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                claim_record(record, root, data, args.agent_id, args.lease_seconds)
                save(root, data)
                result = {"ok": True, "session": record}
            elif args.command == "heartbeat":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                if record.get("lease_owner") != args.agent_id:
                    raise ValueError("only the lease owner can heartbeat")
                if record["status"] == "closed":
                    raise ValueError("closed session cannot heartbeat")
                record["lease_until"] = (datetime.now().astimezone() + timedelta(seconds=args.lease_seconds)).isoformat(timespec="seconds")
                record["status"] = "working"
                record["revision"] += 1
                record["updated_at"] = now()
                recompute_gate(record)
                save(root, data)
                result = {"ok": True, "session": record}
            elif args.command == "submit-research":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                submit_research(record, args)
                save(root, data)
                result = {"ok": True, "session": record}
            elif args.command == "review":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                submit_review(record, data, root, args)
                save(root, data)
                result = {
                    "ok": True,
                    "session": record,
                    "target": get(data, record["review_target_session_id"]),
                }
            elif args.command == "repair-review-close":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                repair_review_close(record, data, root, args)
                save(root, data)
                result = {"ok": True, "session": record}
            elif args.command == "update":
                record = get(data, args.session_id)
                check_revision(record, args.expected_revision)
                update_record(record, args)
                save(root, data)
                result = {"ok": True, "session": record}
            else:
                records = list(data["sessions"].values())
                if not args.include_closed:
                    records = [record for record in records if record["status"] != "closed"]
                if args.agent_id:
                    records = [record for record in records if record.get("agent_id") == args.agent_id]
                if args.project:
                    records = [record for record in records if record.get("project") == args.project]
                if args.task_ref:
                    records = [record for record in records if record.get("task_ref") == args.task_ref]
                records.sort(key=lambda record: record["session_id"])
                result = {"ok": True, "sessions": records}
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
