"""Drive the Formal Handoff queue CLI against throwaway runtimes.

Two layers:
- mini runtime: a small skeleton for fast command-level assertions.
- full clone: a copy of the Product Repo with dynamic state reset, so the
  real `handoff-control.py close` chain (governance session -> archive ->
  receipt -> event -> validation) runs against the real validation suite.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
QUEUE_SCRIPT = REPO / ".orbitos/scripts/handoff-queue.py"
CONTROL_SCRIPT = REPO / ".orbitos/scripts/handoff-control.py"
PASSED = 0
FAILED = 0


def check(condition, label):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  {label} PASS")
    else:
        FAILED += 1
        print(f"  {label} FAIL")


def run_script(script, tmp, command, args, expect_ok):
    global PASSED, FAILED
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp), command, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    ok = result.returncode == 0
    label = f"{command} {'PASS' if ok == expect_ok else 'FAIL'}"
    if ok != expect_ok:
        FAILED += 1
        print(f"  {label} rc={result.returncode} stderr={result.stderr.strip()}")
    else:
        PASSED += 1
        print(f"  {label}")
    return result


def queue(args):
    out = []
    for spec in args:
        out.append("--queue")
        out.append("|".join([
            spec["stage_id"],
            spec["tool"],
            spec["role"],
            spec["deliverable"],
            spec["scope"],
            spec["acceptance"],
            spec.get("next_stage", ""),
        ]))
    return out


def proposed_queue(args):
    out = []
    for spec in args:
        out.append("--proposed-queue")
        out.append("|".join([
            spec["stage_id"],
            spec["tool"],
            spec["role"],
            spec["deliverable"],
            spec["scope"],
            spec["acceptance"],
            spec.get("next_stage", ""),
        ]))
    return out


def read_state(tmp):
    return json.loads((tmp / ".orbitos/state/handoff-queues.json").read_text(encoding="utf-8"))


def queue_record(tmp, relative):
    return read_state(tmp)["queues"][relative]


def write_handoff(tmp, name, owner="agent_a", return_owner="agent_a"):
    path = tmp / "00-系统/agents/handoff" / f"{name}.md"
    path.write_text(
        "---\n"
        "title: Flow Test\n"
        "area: system\n"
        "purpose: record\n"
        "lifecycle: draft\n"
        "created: 2026-01-01\n"
        "updated: 2026-01-01\n"
        "handoff_status: delegated\n"
        f"current_owner: {owner}\n"
        f"return_owner: {return_owner}\n"
        "next_action: start\n"
        "governance_required: false\n"
        "collaboration_session_id:\n"
        "plan_status: none\n"
        "plan_revision: 0\n"
        "current_stage: none\n"
        "tags:\n"
        "  - orbitos\n"
        "---\n\n"
        "# Flow Test\n\n## 任务\n\n- relay test\n",
        encoding="utf-8",
        newline="\n",
    )
    return f"00-系统/agents/handoff/{name}.md"


def mini_runtime():
    tmp = Path(tempfile.mkdtemp(prefix="handoff-flow-"))
    (tmp / "00-系统/agents/handoff/archive").mkdir(parents=True)
    shutil.copy(REPO / "00-系统/agents/BOARD.md", tmp / "00-系统/agents/BOARD.md")
    roles_dir = tmp / ".orbitos/module-packages/collaboration"
    roles_dir.mkdir(parents=True)
    shutil.copy(REPO / ".orbitos/module-packages/collaboration/roles.json", roles_dir / "roles.json")
    scripts_dir = tmp / ".orbitos/scripts"
    scripts_dir.mkdir(parents=True)
    for name in ("handoff-queue.py", "handoff-control.py"):
        shutil.copy(REPO / f".orbitos/scripts/{name}", scripts_dir / name)
    state_dir = tmp / ".orbitos/state"
    state_dir.mkdir(parents=True)
    for name, content in {
        "handoff-queues.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "queues": {}}',
        "work-items.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "items": {}}',
        "collaboration-sessions.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "sessions": {}}',
    }.items():
        (state_dir / name).write_text(content, encoding="utf-8")
    agents_dir = tmp / ".orbitos/agents"
    agents_dir.mkdir(parents=True)
    registry = {
        "version": 1,
        "updated": "2026-01-01",
        "agents": [
            {"agent_id": "agent_a", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/a.md"},
            {"agent_id": "agent_b", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/b.md"},
            {"agent_id": "agent_c", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/c.md"},
            {"agent_id": "agent_d", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/d.md"},
        ],
    }
    (agents_dir / "registry.yaml").write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    return tmp


STAGE_S = {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "define task", "scope": "read only", "acceptance": "defined", "next_stage": "s2"}
STAGE_R2 = {"stage_id": "s2", "tool": "agent_b", "role": "researcher", "deliverable": "collect evidence", "scope": "read only", "acceptance": "evidence ready", "next_stage": ""}
STAGE_R = {"stage_id": "s2", "tool": "agent_b", "role": "researcher", "deliverable": "collect evidence", "scope": "read only", "acceptance": "evidence ready", "next_stage": "s3"}
STAGE_C = {"stage_id": "s3", "tool": "agent_c", "role": "coordinator", "deliverable": "summarize", "scope": "read only", "acceptance": "summary ready", "next_stage": ""}


# --- schema probe (mirrors run-validation.validate_value for the queue schema) ---

def probe_type(value, types):
    if not types:
        return True
    for schema_type in types:
        if schema_type == "null" and value is None:
            return True
        if schema_type == "array" and isinstance(value, list):
            return True
        if schema_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if schema_type == "object" and isinstance(value, dict):
            return True
        if schema_type == "string" and isinstance(value, str):
            return True
        if schema_type == "boolean" and isinstance(value, bool):
            return True
    return False


def probe_allowed(schema):
    if "type" not in schema:
        return []
    schema_type = schema["type"]
    return schema_type if isinstance(schema_type, list) else [schema_type]


def probe_schema(value, schema, path_text, errors):
    types = probe_allowed(schema)
    if not probe_type(value, types):
        errors.append(f"{path_text}: type mismatch")
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path_text}: value is not in enum")
    if "object" in types and isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path_text}.{name}: missing required field")
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in schema.get("properties", {}):
                    errors.append(f"{path_text}.{name}: additional property")
        for name, prop in schema.get("properties", {}).items():
            if name in value:
                probe_schema(value[name], prop, f"{path_text}.{name}", errors)
    if "array" in types and isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            probe_schema(item, schema["items"], f"{path_text}[{index}]", errors)


def check_state_schema(tmp, label):
    """Run the queue schema probe against the live state file (no TypeError, no enum miss)."""
    schema = json.loads((REPO / ".orbitos/schemas/handoff-queue.schema.yaml").read_text(encoding="utf-8"))
    state = json.loads((tmp / ".orbitos/state/handoff-queues.json").read_text(encoding="utf-8"))
    errors = []
    probe_schema(state, schema, "$", errors)
    check(not errors, f"{label} queue state schema valid (errors={errors})")


def test_relay_three_agent(tmp):
    print("test_relay_three_agent (#16 relay + close permissions)")
    handoff = write_handoff(tmp, "relay")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R, STAGE_C]), True)
    check_state_schema(tmp, "post-launch")
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "ok", "--evidence", "board.md"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "nope", "--evidence", "x.md"], False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "again", "--evidence", "y.md"], False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_c", "--role", "coordinator", "--stage-id", "s3", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "summary", "--evidence", "final.md"], True)
    record = queue_record(tmp, handoff)
    check(record["current_owner"] == "agent_a", "baton returned to return owner")
    check(all(record["stages"][sid]["status"] == "complete" for sid in record["stage_order"]), "all stages complete")
    # forged return owner must be rejected
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s3", "--return-owner", "agent_d", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    text = (tmp / "00-系统/agents/handoff/relay.md").read_text(encoding="utf-8")
    check("## 阶段记录" in text and "s1 由 agent_a 完成" in text and "s2 由 agent_b 完成" in text, "stage records written to handoff Markdown")
    check("next_owner:" in text and "current_role:" in text, "frontmatter carries next_owner/current_role")


def test_replan_unavailable(tmp):
    print("test_replan_unavailable (#17 unavailable substitution)")
    handoff = write_handoff(tmp, "replan")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    revised = [dict(STAGE_S), {**STAGE_R2, "tool": "agent_d"}]
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "unavailable", "--affected-stage", "s2", "--reason", "agent_b offline", "--date", "2026-01-01"] + proposed_queue(revised), True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_d", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "1", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_d", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    record = queue_record(tmp, handoff)
    check(record["plan_revision"] == 1 and record["stages"]["s2"]["tool"] == "agent_d", "replan revision and substitution persisted")
    text = (tmp / "00-系统/agents/handoff/replan.md").read_text(encoding="utf-8")
    check("## 计划修订" in text and "plan_revision：1" in text, "replan section written to handoff Markdown")


def test_consecutive_replans(tmp):
    print("test_consecutive_replans (#17 multiple revisions, no partial state)")
    handoff = write_handoff(tmp, "multi-replan")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "scope", "--affected-stage", "s2", "--reason", "scope grew", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "collect more evidence"}]), True)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "unavailable", "--affected-stage", "s2", "--reason", "agent_b busy", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "tool": "agent_d", "deliverable": "collect more evidence"}]), True)
    record = queue_record(tmp, handoff)
    check(record["plan_revision"] == 2, "two consecutive replans advance revision to 2")
    check(len(record["replans"]) == 2 and all(item["revision"] in {1, 2} for item in record["replans"]), "replan history intact")
    text = (tmp / "00-系统/agents/handoff/multi-replan.md").read_text(encoding="utf-8")
    check(text.count("## 计划修订") == 1 and "plan_revision：1" in text and "plan_revision：2" in text, "replan section appended idempotently")


def test_builder_editor_identity_and_close(tmp):
    print("test_builder_editor_identity_and_close (#18 identity isolation + close permission)")
    same_tool = write_handoff(tmp, "self-review")
    queue_bad = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_b", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", same_tool, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_bad), False)

    handoff = write_handoff(tmp, "engineer")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "scoped", "--evidence", "board.md"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md"], True)
    # editor evidence must reference the reviewed stage
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "review.md"], False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "s2 review.md"], True)
    close = subprocess.run(
        [sys.executable, str(CONTROL_SCRIPT), "--root", str(tmp), "close",
         "--handoff", handoff, "--work-id", "w1", "--expected-work-revision", "1", "--agent-id", "agent_b",
         "--session-id", "sess-x", "--summary", "x", "--reason", "x", "--slug", "x", "--output", "x", "--date", "2026-01-01"],
        capture_output=True, text=True, encoding="utf-8",
    )
    check(close.returncode != 0, "builder close rejected")
    record = queue_record(tmp, handoff)
    check(record["current_owner"] == "agent_a", "baton returned to return owner after editor approval")


def test_forged_return_owner(tmp):
    print("test_forged_return_owner (P1: launch persists authoritative return owner)")
    handoff = write_handoff(tmp, "forge", owner="agent_a", return_owner="agent_a")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    # an unrelated agent cannot confirm itself into the return owner seat
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_d", "--date", "2026-01-01"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_d", "--plan-revision", "0", "--return-owner", "agent_d", "--date", "2026-01-01"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    record = queue_record(tmp, handoff)
    check(record["return_owner"] == "agent_a" and record["confirmed_by"] == "user", "authoritative return owner recorded at launch")


def test_replan_failure_escalation(tmp):
    print("test_replan_failure_escalation (#17 second failure threshold)")
    handoff = write_handoff(tmp, "escalate")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "data missing"], True)
    # one failure alone is not enough for a failure re-plan
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_b", "--trigger", "failure", "--affected-stage", "s2", "--reason", "premature", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "collect evidence again"}]), False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "still missing"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_b", "--trigger", "failure", "--affected-stage", "s2", "--reason", "second failure", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "collect evidence again"}]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "1", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    record = queue_record(tmp, handoff)
    check(record["replans"][0]["trigger"] == "failure" and record["replans"][0]["confirmed_at"], "failure re-plan confirmed after second failure")
    text = (tmp / "00-系统/agents/handoff/escalate.md").read_text(encoding="utf-8")
    check(text.count("## 阶段记录") == 1 and text.count("s2 由 agent_b 阻塞") == 2, "blocked stage records appended to Markdown")


# --- full clone: real close chain with real validation ---

def clone_runtime():
    """Copy the Product Repo and reset dynamic state so the real close chain can run."""
    root = Path(REPO).resolve()
    top_state = root / ".orbitos/state"
    top_handoff = root / "00-系统/agents/handoff"
    top_events = root / ".orbitos/logs/events"

    def ignore(directory, names):
        directory = Path(directory).resolve()
        ignored = set()
        for name in names:
            p = Path(directory) / name
            if name in {".git", ".pytest_cache", "__pycache__"} or name.endswith(".pyc"):
                ignored.add(name)
            elif p.is_dir() and p == top_handoff:
                ignored.add(name)
            elif p.is_dir() and p == top_state:
                ignored.add(name)
            elif p.is_dir() and p == top_events:
                ignored.add(name)
        return ignored

    tmp = Path(tempfile.mkdtemp(prefix="handoff-clone-"))
    shutil.copytree(root, tmp, ignore=ignore, dirs_exist_ok=True)
    state_dir = tmp / ".orbitos/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    for item in (root / ".orbitos/state").iterdir():
        if item.is_file():
            shutil.copy2(item, state_dir / item.name)
    for name, content in {
        "collaboration-sessions.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "sessions": {}}',
        "work-items.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "items": {}}',
        "handoff-queues.json": '{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "queues": {}}',
    }.items():
        (state_dir / name).write_text(content, encoding="utf-8")
    (tmp / "00-系统/agents/handoff/archive").mkdir(parents=True, exist_ok=True)
    (tmp / "00-系统/agents/handoff/archive/.gitkeep").write_text("", encoding="utf-8")
    profiles = tmp / "profiles"
    profiles.mkdir(exist_ok=True)
    for aid in ["agent_a", "agent_b", "agent_c", "agent_d"]:
        (profiles / f"{aid}.md").write_text(f"# {aid}\n\n## 经验入口\n\n- none\n\n## 启动关注\n\n- none\n", encoding="utf-8")
    events = tmp / ".orbitos/logs/events"
    events.mkdir(parents=True, exist_ok=True)
    for aid in ["agent_a", "agent_b", "agent_c", "agent_d"]:
        (events / f"flow-{aid}.yaml").write_text(f"agent_id: {aid}\nslug: flow-{aid}\nsummary: flow test evidence\nevent_type: progress_sync\n", encoding="utf-8")
    reg_path = tmp / ".orbitos/agents/registry.yaml"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    reg["agents"] = [
        {"agent_id": "agent_a", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/agent_a.md"},
        {"agent_id": "agent_b", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/agent_b.md"},
        {"agent_id": "agent_c", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/agent_c.md"},
        {"agent_id": "agent_d", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/agent_d.md"},
    ]
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return tmp


def run_command(root, relative, args, expect_ok):
    global PASSED, FAILED
    result = subprocess.run(
        [sys.executable, str(root / relative), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    ok = result.returncode == 0
    if ok != expect_ok:
        FAILED += 1
        print(f"  {relative} {'PASS' if ok == expect_ok else 'FAIL'} rc={result.returncode} stderr={result.stderr.strip()}")
    else:
        PASSED += 1
        print(f"  {relative} {'PASS' if ok == expect_ok else 'FAIL'}")
    return result


def validate_clone(tmp, expect_pass=True):
    result = subprocess.run(
        [sys.executable, str(tmp / ".orbitos/scripts/run-validation.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    passed = result.returncode == 0 and "Validation eval passed" in result.stdout
    check(passed == expect_pass, f"clone validation {'PASS' if passed == expect_pass else 'FAIL'}")
    return result


def close_chain(tmp, handoff, owner="agent_a"):
    """Governed acceptance: create work item, begin, close the session, then close the handoff."""
    stem = Path(handoff).stem
    work_id = f"w-{stem}"
    session_id = f"sess-{stem}"
    run_command(tmp, ".orbitos/scripts/work-control.py", ["create", "--id", work_id, "--title", "accept", "--project", "flow-test", "--source-type", "handoff", "--source-ref", handoff, "--next-action", "accept"], True)
    run_command(tmp, ".orbitos/scripts/handoff-control.py", ["begin", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "1", "--agent-id", owner, "--role", "coordinator", "--session-id", session_id, "--next-action", "accept", "--date", "2026-01-01"], True)
    # close the governance session through its gates
    run_command(tmp, ".orbitos/scripts/collab-session.py", ["update", "--session-id", session_id, "--agent-id", owner, "--expected-revision", "1", "--status", "closed", "--evidence", "acceptance|runtime_receipt|current_snapshot|reproduced"], True)
    result = run_command(tmp, ".orbitos/scripts/handoff-control.py", ["close", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "2", "--agent-id", owner, "--session-id", session_id, "--summary", "accepted", "--reason", "all stages complete", "--slug", f"flow_close_{stem.replace('-', '_')}", "--output", f"project_file|{handoff}|updated", "--date", "2026-01-01"], True)
    return result


def test_full_close_two_agent(tmp):
    print("test_full_close_two_agent (real A -> B -> A -> closed chain)")
    handoff = write_handoff(tmp, "two-close", owner="agent_a", return_owner="agent_a")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    close_chain(tmp, handoff)
    archive = tmp / "00-系统/agents/handoff/archive/two-close.md"
    check(archive.is_file(), "handoff archived")
    board = (tmp / "00-系统/agents/BOARD.md").read_text(encoding="utf-8")
    check("two-close" not in board, "board entry removed")
    record = queue_record(tmp, handoff)
    check(record["close"] and record["close"]["accepted_by"] == "agent_a" and record["close"]["archived_ref"], "close receipt recorded in projection")
    work = json.loads((tmp / ".orbitos/state/work-items.json").read_text(encoding="utf-8"))["items"]["w-two-close"]
    check(work["status"] == "done", "work item closed")
    check(len(list((tmp / ".orbitos/logs/events").glob("*.yaml"))) >= 5, "close event written")
    validate_clone(tmp)


def test_full_close_multi_agent(tmp):
    print("test_full_close_multi_agent (real A -> B -> C -> A -> closed chain)")
    handoff = write_handoff(tmp, "multi-close", owner="agent_a", return_owner="agent_a")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R, STAGE_C]), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    for tool, role, stage, result_text, evidence in [
        ("agent_a", "coordinator", "s1", "defined", "board.md"),
        ("agent_b", "researcher", "s2", "evidence", "notes.md"),
        ("agent_c", "coordinator", "s3", "summary", "final.md"),
    ]:
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", tool, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", result_text, "--evidence", evidence], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/multi-close.md").is_file(), "multi-agent handoff archived")
    record = queue_record(tmp, handoff)
    check(record["close"]["accepted_by"] == "agent_a", "multi-agent close receipt recorded")
    validate_clone(tmp)


def test_full_editor_approve(tmp):
    print("test_full_editor_approve (real Coordinator -> Builder -> Editor -> Coordinator -> closed)")
    handoff = write_handoff(tmp, "editor-approve", owner="agent_a", return_owner="agent_a")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    for tool, role, stage, result_text, evidence in [
        ("agent_a", "coordinator", "s1", "scoped", "board.md"),
        ("agent_b", "builder", "s2", "impl", "diff.md"),
        ("agent_c", "editor", "s3", "approved", "s2 reviewed.md"),
    ]:
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", tool, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", result_text, "--evidence", evidence], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/editor-approve.md").is_file(), "editor-approve handoff archived")
    validate_clone(tmp)


def test_full_editor_reject_rework(tmp):
    print("test_full_editor_reject_rework (real reject -> re-plan -> fix -> re-review -> closed)")
    handoff = write_handoff(tmp, "editor-reject", owner="agent_a", return_owner="agent_a")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    for tool, role, stage, result_text, evidence in [
        ("agent_a", "coordinator", "s1", "scoped", "board.md"),
        ("agent_b", "builder", "s2", "impl", "diff.md"),
    ]:
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", tool, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", result_text, "--evidence", evidence], True)
    # editor rejects (blocked)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "scope creep"], True)
    # re-plan: rewrite s3 into builder fix + editor re-review
    revised = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_b", "role": "builder", "deliverable": "fix scope creep", "scope": "rejected scope only", "acceptance": "fix done", "next_stage": "s4"},
        {"stage_id": "s4", "tool": "agent_c", "role": "editor", "deliverable": "re-review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["replan", "--handoff", handoff, "--agent-id", "agent_c", "--trigger", "scope", "--affected-stage", "s3", "--reason", "scope creep", "--date", "2026-01-01"] + proposed_queue(revised), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "1", "--return-owner", "agent_a", "--date", "2026-01-01"], True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s3", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "fixed", "--evidence", "fix.md"], True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s4", "--return-owner", "agent_a", "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "s3 re-reviewed.md"], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/editor-reject.md").is_file(), "reject-rework handoff archived")
    record = queue_record(tmp, handoff)
    check(record["plan_revision"] == 1 and len(record["replans"]) == 1, "rework plan revision and history preserved")
    validate_clone(tmp)


def main():
    tmp = mini_runtime()
    print(f"mini runtime: {tmp}")
    try:
        test_relay_three_agent(tmp)
        test_forged_return_owner(tmp)
        test_replan_unavailable(tmp)
        test_consecutive_replans(tmp)
        test_builder_editor_identity_and_close(tmp)
        test_replan_failure_escalation(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    clone = clone_runtime()
    print(f"full clone: {clone}")
    try:
        validate_clone(clone)
        test_full_close_two_agent(clone)
        test_full_close_multi_agent(clone)
        test_full_editor_approve(clone)
        test_full_editor_reject_rework(clone)
    finally:
        shutil.rmtree(clone, ignore_errors=True)
    print("")
    print(f"flow test: {PASSED} assertions passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
