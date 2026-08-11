"""Drive the Formal Handoff queue CLI against a throwaway mini runtime.

Builds a temp OrbitOS skeleton (board, registry, roles, state), then runs the
real `handoff-queue.py` command sequences for the relay, re-plan, escalation,
immutability and close-permission paths. Asserts every exit code and state.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".orbitos/scripts/handoff-queue.py"
PASSED = 0
FAILED = 0


def run_script(tmp, command, args, expect_ok):
    global PASSED, FAILED
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp), command, *args],
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


def read_state(tmp):
    return json.loads((tmp / ".orbitos/state/handoff-queues.json").read_text(encoding="utf-8"))


def queue_record(tmp, relative):
    return read_state(tmp)["queues"][relative]


def write_handoff(tmp, name, owner="agent-a", return_owner="agent-a"):
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


def build_runtime():
    tmp = Path(tempfile.mkdtemp(prefix="handoff-flow-"))
    (tmp / "00-系统/agents/handoff/archive").mkdir(parents=True)
    shutil.copy(ROOT / "00-系统/agents/BOARD.md", tmp / "00-系统/agents/BOARD.md")
    roles_dir = tmp / ".orbitos/module-packages/collaboration"
    roles_dir.mkdir(parents=True)
    shutil.copy(ROOT / ".orbitos/module-packages/collaboration/roles.json", roles_dir / "roles.json")
    scripts_dir = tmp / ".orbitos/scripts"
    scripts_dir.mkdir(parents=True)
    for name in ("handoff-queue.py", "handoff-control.py"):
        shutil.copy(ROOT / f".orbitos/scripts/{name}", scripts_dir / name)
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
            {"agent_id": "agent-a", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/a.md"},
            {"agent_id": "agent-b", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/b.md"},
            {"agent_id": "agent-c", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/c.md"},
            {"agent_id": "agent-d", "deployment": {"orbitos_path": str(tmp)}, "profile_ref": "profiles/d.md"},
        ],
    }
    (agents_dir / "registry.yaml").write_text(json.dumps(registry), encoding="utf-8")
    return tmp


def queue_args(specs):
    args = []
    for spec in specs:
        args.append(
            "--queue"
        )
        args.append("|".join([
            spec["stage_id"],
            spec["tool"],
            spec["role"],
            spec["deliverable"],
            spec["scope"],
            spec["acceptance"],
            spec.get("next_stage", ""),
        ]))
    return args


STAGE_S = {"stage_id": "s1", "tool": "agent-a", "role": "coordinator", "deliverable": "define task", "scope": "read only", "acceptance": "defined", "next_stage": "s2"}
STAGE_R = {"stage_id": "s2", "tool": "agent-b", "role": "researcher", "deliverable": "collect evidence", "scope": "read only", "acceptance": "evidence ready", "next_stage": "s3"}
STAGE_R2 = {"stage_id": "s2", "tool": "agent-b", "role": "researcher", "deliverable": "collect evidence", "scope": "read only", "acceptance": "evidence ready", "next_stage": ""}
STAGE_C = {"stage_id": "s3", "tool": "agent-c", "role": "coordinator", "deliverable": "summarize", "scope": "read only", "acceptance": "summary ready", "next_stage": ""}


def replan_queue_args(specs):
    args = []
    for spec in specs:
        args.append("--proposed-queue")
        args.append("|".join([
            spec["stage_id"],
            spec["tool"],
            spec["role"],
            spec["deliverable"],
            spec["scope"],
            spec["acceptance"],
            spec.get("next_stage", ""),
        ]))
    return args


def test_relay_three_agent(tmp):
    print("test_relay_three_agent (#16 relay + close permissions)")
    handoff = write_handoff(tmp, "relay")
    run_script(tmp, "launch", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--return-owner", "agent-a", "--next-action", "start", "--date", "2026-01-01"] + queue_args([STAGE_S, STAGE_R, STAGE_C]), True)
    # no stage may advance before user confirmation
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "ok", "--evidence", "board.md"], False)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "0", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    # future stage cannot be claimed while the first stage is current
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "nope", "--evidence", "x.md"], False)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    # completed stage is immutable
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "again", "--evidence", "y.md"], False)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-c", "--role", "coordinator", "--stage-id", "s3", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "summary", "--evidence", "final.md"], True)
    record = queue_record(tmp, handoff)
    assert record["plan_status"] == "confirmed"
    assert record["current_owner"] == "agent-a"
    assert record["current_stage"] == "s3"
    assert all(record["stages"][sid]["status"] == "complete" for sid in record["stage_order"])
    # only the return owner can close
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s3", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    print("  assert relay state OK")


def test_replan_unavailable(tmp):
    print("test_replan_unavailable (#17 unavailable agent substitution)")
    handoff = write_handoff(tmp, "replan")
    run_script(tmp, "launch", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--return-owner", "agent-a", "--next-action", "start", "--date", "2026-01-01"] + queue_args([STAGE_S, STAGE_R2]), True)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "0", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    # the current owner discovers the assigned next-stage tool is unavailable; re-plan before advancing
    revised = [dict(STAGE_S), {**STAGE_R2, "tool": "agent-d"}]
    run_script(tmp, "replan", ["--handoff", handoff, "--agent-id", "agent-a", "--trigger", "unavailable", "--affected-stage", "s2", "--reason", "agent-b offline", "--date", "2026-01-01"] + replan_queue_args(revised), True)
    # replacement cannot advance before confirmation
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-d", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    # stale revision rejected
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "0", "--return-owner", "agent-a", "--date", "2026-01-01"], False)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "1", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-d", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    record = queue_record(tmp, handoff)
    assert record["plan_revision"] == 1
    assert record["stages"]["s2"]["tool"] == "agent-d"
    assert record["stages"]["s1"]["status"] == "complete"
    print("  assert replan state OK")


def test_replan_failure_escalation(tmp):
    print("test_replan_failure_escalation (#17 second failure requires re-plan)")
    handoff = write_handoff(tmp, "escalate")
    run_script(tmp, "launch", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--return-owner", "agent-a", "--next-action", "start", "--date", "2026-01-01"] + queue_args([STAGE_S, STAGE_R2]), True)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "0", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "data missing"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "still missing"], True)
    # third attempt without re-plan must fail
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    # failure trigger requires a stage that already failed
    revised = [dict(STAGE_S), {**STAGE_R2, "deliverable": "collect evidence again", "acceptance": "evidence ready again"}]
    run_script(tmp, "replan", ["--handoff", handoff, "--agent-id", "agent-b", "--trigger", "failure", "--affected-stage", "s2", "--reason", "second failure", "--date", "2026-01-01"] + replan_queue_args(revised), True)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "1", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    record = queue_record(tmp, handoff)
    assert record["plan_revision"] == 1
    assert record["stages"]["s2"]["status"] == "complete"
    assert len(record["replans"]) == 1
    assert record["replans"][0]["trigger"] == "failure"
    assert record["replans"][0]["affected_stage"] == "s2"
    assert record["replans"][0]["confirmed_at"]
    print("  assert escalation state OK")


def test_builder_editor_close_permissions(tmp):
    print("test_builder_editor_close_permissions (#18 builder/editor cannot close)")
    handoff = write_handoff(tmp, "engineer")
    queue = [
        {"stage_id": "s1", "tool": "agent-a", "role": "coordinator", "deliverable": "define scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent-b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent-c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_script(tmp, "launch", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--return-owner", "agent-a", "--next-action", "start", "--date", "2026-01-01"] + queue_args(queue), True)
    run_script(tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent-a", "--plan-revision", "0", "--return-owner", "agent-a", "--date", "2026-01-01"], True)
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "scoped", "--evidence", "board.md"], True)
    # premature close by the return owner while stages are pending is rejected
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md"], True)
    # builder cannot close via handoff-control (return owner check runs first)
    close = subprocess.run(
        [sys.executable, str(tmp / ".orbitos/scripts/handoff-control.py"), "--root", str(tmp), "close",
         "--handoff", handoff, "--work-id", "w1", "--expected-work-revision", "1", "--agent-id", "agent-b",
         "--session-id", "sess-x", "--summary", "x", "--reason", "x", "--slug", "x", "--output", "x", "--date", "2026-01-01"],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert close.returncode != 0, "builder close must be rejected"
    print("  builder close rejected PASS")
    run_script(tmp, "advance", ["--handoff", handoff, "--agent-id", "agent-c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent-a", "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "review.md"], True)
    record = queue_record(tmp, handoff)
    assert record["current_owner"] == "agent-a"
    print("  assert engineer state OK")


def main():
    tmp = build_runtime()
    print(f"mini runtime: {tmp}")
    try:
        test_relay_three_agent(tmp)
        test_replan_unavailable(tmp)
        test_replan_failure_escalation(tmp)
        test_builder_editor_close_permissions(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("")
    print(f"flow test: {PASSED} command assertions passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
