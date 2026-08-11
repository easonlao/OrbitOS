"""Drive the Formal Handoff queue CLI against throwaway runtimes.

Two layers:
- mini runtime: a small skeleton for fast command-level assertions.
- fresh runtime: built from an empty temp dir through the official
  init-runtime.py, then layered with the repo assets, so the real
  `handoff-control.py close` chain runs against the real validation suite.

Every stage advance is bound to a governance session (agent/role/task), and
close is exercised as a recoverable idempotent sequence including a
fault-injection recovery test.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def locate_repo():
    """Locate the Product Repo whether this script runs inside it or under a
    runtime root (which may carry extra dirs like .runtime that must not be cloned)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".orbitos/scripts/handoff-queue.py").is_file() and parent.name == "repo":
            return parent
    fallback = here.parents[3] / "03-项目/OrbitOS/repo"
    if (fallback / ".orbitos/scripts/handoff-queue.py").is_file():
        return fallback
    raise RuntimeError("cannot locate the OrbitOS product repo")


REPO = locate_repo()
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
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    ok = result.returncode == 0
    if ok != expect_ok:
        FAILED += 1
        print(f"  {command} FAIL rc={result.returncode} stderr={result.stderr.strip()}")
    else:
        PASSED += 1
        print(f"  {command} {'PASS' if ok == expect_ok else 'FAIL'}")
    return result


def run_command(tmp, relative, args, expect_ok):
    global PASSED, FAILED
    result = subprocess.run(
        [sys.executable, str(tmp / relative), "--root", str(tmp), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    ok = result.returncode == 0
    if ok != expect_ok:
        FAILED += 1
        print(f"  {relative} FAIL rc={result.returncode} stderr={result.stderr.strip()}")
    else:
        PASSED += 1
        print(f"  {relative} PASS")
    return result


def queue(args):
    out = []
    for spec in args:
        out.append("--queue")
        out.append("|".join([
            spec["stage_id"], spec["tool"], spec["role"], spec["deliverable"],
            spec["scope"], spec["acceptance"], spec.get("next_stage", ""),
        ]))
    return out


def proposed_queue(args):
    out = []
    for spec in args:
        out.append("--proposed-queue")
        out.append("|".join([
            spec["stage_id"], spec["tool"], spec["role"], spec["deliverable"],
            spec["scope"], spec["acceptance"], spec.get("next_stage", ""),
        ]))
    return out


def read_state(tmp):
    return json.loads((tmp / ".orbitos/state/handoff-queues.json").read_text(encoding="utf-8"))


def queue_record(tmp, relative):
    return read_state(tmp)["queues"][relative]


def write_handoff(tmp, name, owner="agent_a", return_owner="agent_a"):
    path = tmp / "00-系统/agents/handoff" / f"{name}.md"
    path.write_text(
        "---\ntitle: Flow Test\narea: system\npurpose: record\nlifecycle: draft\n"
        "created: 2026-01-01\nupdated: 2026-01-01\nhandoff_status: delegated\n"
        f"current_owner: {owner}\nreturn_owner: {return_owner}\nnext_action: start\n"
        "governance_required: false\ncollaboration_session_id:\nplan_status: none\n"
        "plan_revision: 0\ncurrent_stage: none\ntags:\n  - orbitos\n---\n\n"
        "# Flow Test\n\n## 任务\n\n- relay test\n",
        encoding="utf-8", newline="\n",
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
    for name in ("handoff-queue.py", "handoff-control.py", "collab-session.py", "work-control.py"):
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
        "version": 1, "updated": "2026-01-01",
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


# --- governance session helpers ---

def open_stage_session(tmp, handoff, agent, role, stage, review_target=None):
    """Open the governed session a stage advance must be bound to."""
    stem = Path(handoff).stem
    sid = f"sess-{stem}-{stage}"
    cmd = [sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp), "open",
           "--session-id", sid, "--mode", "multi_agent_claim", "--task-ref", handoff,
           "--project", "flow-test", "--agent-id", agent, "--role", role]
    if role == "builder":
        # governance requires builder to consume a green researcher source
        researcher = f"sess-{stem}-res"
        subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp), "open",
                        "--session-id", researcher, "--mode", "multi_agent_claim", "--task-ref", handoff,
                        "--project", "flow-test", "--agent-id", agent, "--role", "researcher"],
                       capture_output=True, text=True, encoding="utf-8")
        subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp),
                        "submit-research", "--session-id", researcher, "--agent-id", agent,
                        "--expected-revision", "1", "--evidence", "notes.md|human_confirmed|current_primary|reproduced"],
                       capture_output=True, text=True, encoding="utf-8")
        cmd += ["--source-session-id", researcher]
    if review_target:
        # editor target must be review_required with pending review
        subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp), "update",
                        "--session-id", review_target, "--agent-id", agent if False else review_target.split("-")[-2] and _session_agent(tmp, review_target),
                        "--expected-revision", str(_session_revision(tmp, review_target)),
                        "--status", "review_required"],
                       capture_output=True, text=True, encoding="utf-8")
        cmd += ["--review-target-session-id", review_target]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"session open failed: {result.stderr}")
    return sid


def _session_agent(tmp, sid):
    data = json.loads((tmp / ".orbitos/state/collaboration-sessions.json").read_text(encoding="utf-8"))
    return data["sessions"][sid]["agent_id"]


def _session_revision(tmp, sid):
    data = json.loads((tmp / ".orbitos/state/collaboration-sessions.json").read_text(encoding="utf-8"))
    return data["sessions"][sid]["revision"]


def session_review_required(tmp, sid):
    """Move a builder/writer session into review_required so an editor can target it."""
    result = subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp), "update",
                             "--session-id", sid, "--agent-id", _session_agent(tmp, sid),
                             "--expected-revision", str(_session_revision(tmp, sid)),
                             "--status", "review_required"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"review_required failed: {result.stderr}")


def open_editor_session(tmp, handoff, agent, review_target, stage="editor"):
    stem = Path(handoff).stem
    session_review_required(tmp, review_target)
    sid = f"sess-{stem}-editor-{stage}"
    result = subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/collab-session.py"), "--root", str(tmp), "open",
                             "--session-id", sid, "--mode", "multi_agent_claim", "--task-ref", handoff,
                             "--project", "flow-test", "--agent-id", agent, "--role", "editor",
                             "--review-target-session-id", review_target],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"editor session open failed: {result.stderr}")
    return sid


def close_chain(tmp, handoff, owner="agent_a"):
    """Governed acceptance: create work item, begin, close the session, then close the handoff."""
    stem = Path(handoff).stem
    work_id = f"w-{stem}"
    session_id = f"sess-{stem}-accept"
    run_command(tmp, ".orbitos/scripts/work-control.py", ["create", "--id", work_id, "--title", "accept", "--project", "flow-test", "--source-type", "handoff", "--source-ref", handoff, "--next-action", "accept"], True)
    run_command(tmp, ".orbitos/scripts/handoff-control.py", ["begin", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "1", "--agent-id", owner, "--role", "coordinator", "--session-id", session_id, "--next-action", "accept", "--date", "2026-01-01"], True)
    run_command(tmp, ".orbitos/scripts/collab-session.py", ["update", "--session-id", session_id, "--agent-id", owner, "--expected-revision", "1", "--status", "closed", "--evidence", "acceptance|runtime_receipt|current_snapshot|reproduced"], True)
    result = run_command(tmp, ".orbitos/scripts/handoff-control.py", ["close", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "2", "--agent-id", owner, "--session-id", session_id, "--summary", "accepted", "--reason", "all stages complete", "--slug", f"flow_close_{stem.replace('-', '_')}", "--output", f"project_file|{handoff}|updated", "--date", "2026-01-01"], True)
    return result


def validate_clone(tmp, expect_pass=True):
    result = subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/run-validation.py")],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    passed = result.returncode == 0 and "Validation eval passed" in result.stdout
    check(passed == expect_pass, f"clone validation {'PASS' if passed == expect_pass else 'FAIL'}")
    return result


# --- mini runtime tests ---

def test_relay_three_agent(tmp):
    print("test_relay_three_agent (#16 relay + session binding)")
    handoff = write_handoff(tmp, "relay")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R, STAGE_C]), True)
    # advance without a governance session must be refused
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--session-id", "nope", "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    for agent, role, stage in [("agent_a", "coordinator", "s1"), ("agent_b", "researcher", "s2"), ("agent_c", "coordinator", "s3")]:
        sid = open_stage_session(tmp, handoff, agent, role, stage)
        args = ["--handoff", handoff, "--agent-id", agent, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--session-id", sid, "--date", "2026-01-01", "--outcome", "done", "--result", f"{stage} done", "--evidence", "notes.md"]
        run_script(QUEUE_SCRIPT, tmp, "advance", args, True)
    record = queue_record(tmp, handoff)
    check(record["current_owner"] == "agent_a", "baton returned to return owner")
    check(all(record["stages"][sid]["status"] == "complete" for sid in record["stage_order"]), "all stages complete")
    text = (tmp / "00-系统/agents/handoff/relay.md").read_text(encoding="utf-8")
    check("## 阶段记录" in text and "s1 由 agent_a 完成" in text, "stage records written to Markdown")
    check(all(record["stages"][sid]["session_id"] for sid in record["stage_order"]), "stage sessions recorded")


def test_launch_card_full(tmp):
    print("test_launch_card_full (#15 mandatory card fields + receipt)")
    handoff = write_handoff(tmp, "card")
    # incomplete launch card must be refused
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), False)
    handoff = write_handoff(tmp, "card2")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), False)
    handoff = write_handoff(tmp, "card3")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不修改范围外的文件", "--return-format", "结论+证据引用", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    record = queue_record(tmp, handoff)
    check(record["prohibited"] == "不修改范围外的文件" and record["return_format"] == "结论+证据引用", "launch card fields persisted")
    text = (tmp / "00-系统/agents/handoff/card3.md").read_text(encoding="utf-8")
    check("禁止事项" in text and "返回格式" in text, "launch card section in Markdown")
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    check(queue_record(tmp, handoff)["confirmed_receipt"] == "user accepted", "confirm receipt recorded")
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "again", "--date", "2026-01-01"], False)
    # confirm without receipt refused
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--date", "2026-01-01"], False)


def test_replan_structured_and_latest(tmp):
    print("test_replan_structured_and_latest (#17 structured fields + latest-only confirmation)")
    handoff = write_handoff(tmp, "structured")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    # replan without the mandatory structured fields is refused
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "scope", "--affected-stage", "s2", "--reason", "scope grew", "--valid-results", "s1 有效", "--invalidated-assumptions", "假设过时", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "more evidence"}]), False)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "scope", "--affected-stage", "s2", "--reason", "scope grew", "--valid-results", "s1 定义有效", "--invalidated-assumptions", "s2 假设过时", "--replacement-role", "researcher", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "collect more evidence"}]), True)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_a", "--trigger", "unavailable", "--affected-stage", "s2", "--reason", "agent_b busy", "--valid-results", "s1 定义仍有效", "--invalidated-assumptions", "agent_b 可用", "--replacement-role", "researcher", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "tool": "agent_d", "deliverable": "collect more evidence"}]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "2", "--return-owner", "agent_a", "--receipt", "user accepted v2", "--date", "2026-01-01"], True)
    record = queue_record(tmp, handoff)
    check(record["replans"][0]["confirmed_at"] is None and bool(record["replans"][1]["confirmed_at"]), "only the latest re-plan confirmed")
    check(record["replans"][0]["valid_results"] and record["replans"][1]["invalidated_assumptions"] and record["replans"][1]["replacement_role"], "structured re-plan fields recorded")
    text = (tmp / "00-系统/agents/handoff/structured.md").read_text(encoding="utf-8")
    check("仍有效结果" in text and "失效假设" in text and "替换角色" in text, "structured re-plan written to Markdown")


def test_mark_close_removed(tmp):
    print("test_mark_close_removed (P1: receipt only via governed close)")
    handoff = write_handoff(tmp, "no-mark")
    result = run_script(QUEUE_SCRIPT, tmp, "mark-close", ["--handoff", handoff, "--accepted-by", "agent_a", "--archived-ref", "x"], False)
    check(result.returncode == 2, "mark-close is not a public command")


def test_queue_record_lost_fail_closed(tmp):
    print("test_queue_record_lost_fail_closed (P1: declared plan, lost projection)")
    handoff = write_handoff(tmp, "lost")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    (tmp / ".orbitos/state/handoff-queues.json").write_text('{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "queues": {}}', encoding="utf-8")
    result = run_script(CONTROL_SCRIPT, tmp, "begin", ["--handoff", handoff, "--work-id", "w1", "--expected-work-revision", "1", "--agent-id", "agent_a", "--role", "coordinator", "--session-id", "sess1", "--next-action", "x", "--date", "2026-01-01"], False)
    check("projection is missing" in (result.stderr or ""), "begin refuses a lost queue projection")


def test_builder_editor_gates(tmp):
    print("test_builder_editor_gates (#18 builder refs + editor session binding)")
    same_tool = write_handoff(tmp, "self-review")
    queue_bad = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_b", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", same_tool, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_bad), False)

    handoff = write_handoff(tmp, "engineer")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    s1 = open_stage_session(tmp, handoff, "agent_a", "coordinator", "s1")
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--session-id", s1, "--date", "2026-01-01", "--outcome", "done", "--result", "scoped", "--evidence", "board.md"], True)
    s2 = open_stage_session(tmp, handoff, "agent_b", "builder", "s2")
    # builder without diff/validation refs refused
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md"], False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md", "--diff-ref", "diff/main.md", "--validation-ref", "validation/run.md"], True)
    # editor without a bound review target refused at the governance layer too
    run_command(tmp, ".orbitos/scripts/collab-session.py", ["open", "--session-id", "sess-engineer-no-target", "--mode", "multi_agent_claim", "--task-ref", handoff, "--project", "flow-test", "--agent-id", "agent_c", "--role", "editor"], False)
    s3 = open_editor_session(tmp, handoff, "agent_c", s2, "s3")
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--session-id", s3, "--review-target-session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "s2 reviewed.md", "--reviewed-revision", "1"], True)
    record = queue_record(tmp, handoff)
    check(record["current_owner"] == "agent_a", "baton returned after editor approval")
    check(record["stages"]["s2"]["diff_ref"] and record["stages"]["s2"]["validation_ref"], "builder refs recorded")
    close = subprocess.run(
        [sys.executable, str(CONTROL_SCRIPT), "--root", str(tmp), "close",
         "--handoff", handoff, "--work-id", "w1", "--expected-work-revision", "1", "--agent-id", "agent_b",
         "--session-id", "sess-x", "--summary", "x", "--reason", "x", "--slug", "x", "--output", "x", "--date", "2026-01-01"],
        capture_output=True, text=True, encoding="utf-8",
    )
    check(close.returncode != 0, "builder close rejected")


def test_replan_failure_escalation(tmp):
    print("test_replan_failure_escalation (#17 second failure threshold)")
    handoff = write_handoff(tmp, "escalate")
    run_script(QUEUE_SCRIPT, tmp, "launch", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    s1 = open_stage_session(tmp, handoff, "agent_a", "coordinator", "s1")
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--session-id", s1, "--date", "2026-01-01", "--outcome", "done", "--result", "defined", "--evidence", "board.md"], True)
    s2 = open_stage_session(tmp, handoff, "agent_b", "researcher", "s2")
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "data missing"], True)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_b", "--trigger", "failure", "--affected-stage", "s2", "--reason", "premature", "--valid-results", "s1 有效", "--invalidated-assumptions", "无", "--replacement-role", "researcher", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "again"}]), False)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "still missing"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "x", "--evidence", "y"], False)
    run_script(QUEUE_SCRIPT, tmp, "replan", ["--handoff", handoff, "--agent-id", "agent_b", "--trigger", "failure", "--affected-stage", "s2", "--reason", "second failure", "--valid-results", "s1 定义有效", "--invalidated-assumptions", "s2 数据源不可用", "--replacement-role", "researcher", "--date", "2026-01-01"] + proposed_queue([dict(STAGE_S), {**STAGE_R2, "deliverable": "again"}]), True)
    run_script(QUEUE_SCRIPT, tmp, "confirm", ["--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "1", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    run_script(QUEUE_SCRIPT, tmp, "advance", ["--handoff", handoff, "--agent-id", "agent_b", "--role", "researcher", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "evidence", "--evidence", "notes.md"], True)
    record = queue_record(tmp, handoff)
    check(record["replans"][0]["trigger"] == "failure" and record["replans"][0]["confirmed_at"], "failure re-plan confirmed after second failure")


# --- fresh runtime tests (init-runtime path + real close chain) ---

def clone_runtime():
    """Build a fresh runtime: repo asset layer into an empty temp dir, then the
    official init-runtime.py, then seed test agents."""
    root = Path(REPO).resolve()
    top_state = root / ".orbitos/state"
    top_handoff = root / "00-系统/agents/handoff"
    top_events = root / ".orbitos/logs/events"
    top_registry = root / ".orbitos/agents/registry.yaml"

    def ignore(directory, names):
        directory = Path(directory).resolve()
        ignored = set()
        for name in names:
            p = Path(directory) / name
            if name in {".git", ".pytest_cache", "__pycache__", ".runtime"} or name.endswith(".pyc"):
                ignored.add(name)
            elif p.is_dir() and p in {top_state, top_handoff, top_events}:
                ignored.add(name)
            elif p.is_file() and p == top_registry:
                ignored.add(name)
        return ignored

    tmp = Path(tempfile.mkdtemp(prefix="handoff-init-"))
    shutil.copytree(root, tmp, ignore=ignore, dirs_exist_ok=True)
    init = subprocess.run([sys.executable, str(tmp / ".orbitos/scripts/init-runtime.py")],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if init.returncode != 0:
        raise RuntimeError(f"init-runtime failed: {init.stderr or init.stdout}")
    (tmp / ".orbitos/state/handoff-queues.json").write_text('{"version": 1, "updated_at": "2026-01-01T00:00:00+08:00", "queues": {}}', encoding="utf-8")
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


def test_full_close_two_agent(tmp):
    print("test_full_close_two_agent (real A -> B -> A -> closed chain)")
    handoff = write_handoff(tmp, "two-close")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    for agent, role, stage in [("agent_a", "coordinator", "s1"), ("agent_b", "researcher", "s2")]:
        sid = open_stage_session(tmp, handoff, agent, role, stage)
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", agent, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--session-id", sid, "--date", "2026-01-01", "--outcome", "done", "--result", f"{stage} done", "--evidence", "notes.md"], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/two-close.md").is_file(), "handoff archived")
    record = queue_record(tmp, handoff)
    check(record["close"]["accepted_by"] == "agent_a" and record["close"]["archived_ref"], "close receipt recorded in projection")
    work = json.loads((tmp / ".orbitos/state/work-items.json").read_text(encoding="utf-8"))["items"]["w-two-close"]
    check(work["status"] == "done", "work item closed")
    check(len(list((tmp / ".orbitos/logs/events").glob("*.yaml"))) >= 5, "close event written")
    validate_clone(tmp)


def test_full_close_multi_agent(tmp):
    print("test_full_close_multi_agent (real A -> B -> C -> A -> closed chain)")
    handoff = write_handoff(tmp, "multi-close")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R, STAGE_C]), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    for agent, role, stage in [("agent_a", "coordinator", "s1"), ("agent_b", "researcher", "s2"), ("agent_c", "coordinator", "s3")]:
        sid = open_stage_session(tmp, handoff, agent, role, stage)
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", agent, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--session-id", sid, "--date", "2026-01-01", "--outcome", "done", "--result", f"{stage} done", "--evidence", "notes.md"], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/multi-close.md").is_file(), "multi-agent handoff archived")
    validate_clone(tmp)


def test_full_editor_approve(tmp):
    print("test_full_editor_approve (real Coordinator -> Builder -> Editor -> Coordinator -> closed)")
    handoff = write_handoff(tmp, "editor-approve")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    s1 = open_stage_session(tmp, handoff, "agent_a", "coordinator", "s1")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--session-id", s1, "--date", "2026-01-01", "--outcome", "done", "--result", "scoped", "--evidence", "board.md"], True)
    s2 = open_stage_session(tmp, handoff, "agent_b", "builder", "s2")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md", "--diff-ref", "diff/main.md", "--validation-ref", "validation/run.md"], True)
    s3 = open_editor_session(tmp, handoff, "agent_c", s2, "s3")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--session-id", s3, "--review-target-session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "s2 reviewed.md", "--reviewed-revision", "1"], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/editor-approve.md").is_file(), "editor-approve handoff archived")
    validate_clone(tmp)


def test_full_editor_reject_rework(tmp):
    print("test_full_editor_reject_rework (real reject -> re-plan -> fix -> re-review -> closed)")
    handoff = write_handoff(tmp, "editor-reject")
    queue_ok = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_c", "role": "editor", "deliverable": "review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue(queue_ok), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    s1 = open_stage_session(tmp, handoff, "agent_a", "coordinator", "s1")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--stage-id", "s1", "--return-owner", "agent_a", "--session-id", s1, "--date", "2026-01-01", "--outcome", "done", "--result", "scoped", "--evidence", "board.md"], True)
    s2 = open_stage_session(tmp, handoff, "agent_b", "builder", "s2")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s2", "--return-owner", "agent_a", "--session-id", s2, "--date", "2026-01-01", "--outcome", "done", "--result", "impl", "--evidence", "diff.md", "--diff-ref", "diff/main.md", "--validation-ref", "validation/run.md"], True)
    # editor rejects: rejection must still carry evidence, review target and revision
    s3 = open_editor_session(tmp, handoff, "agent_c", s2, "s3")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s3", "--return-owner", "agent_a", "--session-id", s3, "--review-target-session-id", s2, "--date", "2026-01-01", "--outcome", "blocked", "--unresolved", "scope creep", "--evidence", "s2 reviewed.md", "--reviewed-revision", "1"], True)
    revised = [
        {"stage_id": "s1", "tool": "agent_a", "role": "coordinator", "deliverable": "scope", "scope": "module x", "acceptance": "scoped", "next_stage": "s2"},
        {"stage_id": "s2", "tool": "agent_b", "role": "builder", "deliverable": "implement", "scope": "module x", "acceptance": "verified", "next_stage": "s3"},
        {"stage_id": "s3", "tool": "agent_b", "role": "builder", "deliverable": "fix scope creep", "scope": "rejected scope only", "acceptance": "fix done", "next_stage": "s4"},
        {"stage_id": "s4", "tool": "agent_c", "role": "editor", "deliverable": "re-review", "scope": "reproduce", "acceptance": "approved", "next_stage": ""},
    ]
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["replan", "--handoff", handoff, "--agent-id", "agent_c", "--trigger", "scope", "--affected-stage", "s3", "--reason", "scope creep", "--valid-results", "s1/s2 完成且有效", "--invalidated-assumptions", "s3 审核可一次通过", "--replacement-role", "builder+editor", "--date", "2026-01-01"] + proposed_queue(revised), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "1", "--return-owner", "agent_a", "--receipt", "user accepted v2", "--date", "2026-01-01"], True)
    s3f = open_stage_session(tmp, handoff, "agent_b", "builder", "s3")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_b", "--role", "builder", "--stage-id", "s3", "--return-owner", "agent_a", "--session-id", s3f, "--date", "2026-01-01", "--outcome", "done", "--result", "fixed", "--evidence", "fix.md", "--diff-ref", "diff/fix.md", "--validation-ref", "validation/fix.md"], True)
    s4 = open_editor_session(tmp, handoff, "agent_c", s3f, "s4")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", "agent_c", "--role", "editor", "--stage-id", "s4", "--return-owner", "agent_a", "--session-id", s4, "--review-target-session-id", s3f, "--date", "2026-01-01", "--outcome", "done", "--result", "approved", "--evidence", "s3 re-reviewed.md", "--reviewed-revision", "1"], True)
    close_chain(tmp, handoff)
    check((tmp / "00-系统/agents/handoff/archive/editor-reject.md").is_file(), "reject-rework handoff archived")
    record = queue_record(tmp, handoff)
    check(record["plan_revision"] == 1 and record["replans"][0]["valid_results"], "rework plan revision and structured history preserved")
    validate_clone(tmp)


def test_close_recovery(tmp):
    print("test_close_recovery (fault injection: half-closed state recovers through close)")
    handoff = write_handoff(tmp, "recover")
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["launch", "--handoff", handoff, "--agent-id", "agent_a", "--role", "coordinator", "--return-owner", "agent_a", "--prohibited", "不越界", "--return-format", "结论+证据", "--next-action", "start", "--date", "2026-01-01"] + queue([STAGE_S, STAGE_R2]), True)
    run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["confirm", "--handoff", handoff, "--agent-id", "agent_a", "--plan-revision", "0", "--return-owner", "agent_a", "--receipt", "user accepted", "--date", "2026-01-01"], True)
    for agent, role, stage in [("agent_a", "coordinator", "s1"), ("agent_b", "researcher", "s2")]:
        sid = open_stage_session(tmp, handoff, agent, role, stage)
        run_command(tmp, ".orbitos/scripts/handoff-queue.py", ["advance", "--handoff", handoff, "--agent-id", agent, "--role", role, "--stage-id", stage, "--return-owner", "agent_a", "--session-id", sid, "--date", "2026-01-01", "--outcome", "done", "--result", f"{stage} done", "--evidence", "notes.md"], True)
    # fault injection: run the first half of close (receipt + frontmatter + board + move)
    # but skip the work item / event steps, then re-run close to recover.
    stem = Path(handoff).stem
    work_id = f"w-{stem}"
    session_id = f"sess-{stem}-accept"
    run_command(tmp, ".orbitos/scripts/work-control.py", ["create", "--id", work_id, "--title", "accept", "--project", "flow-test", "--source-type", "handoff", "--source-ref", handoff, "--next-action", "accept"], True)
    run_command(tmp, ".orbitos/scripts/handoff-control.py", ["begin", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "1", "--agent-id", "agent_a", "--role", "coordinator", "--session-id", session_id, "--next-action", "accept", "--date", "2026-01-01"], True)
    run_command(tmp, ".orbitos/scripts/collab-session.py", ["update", "--session-id", session_id, "--agent-id", "agent_a", "--expected-revision", "1", "--status", "closed", "--evidence", "acceptance|runtime_receipt|current_snapshot|reproduced"], True)
    # simulate a crash after the archive move but before work/event: do it by hand
    import shutil as _sh
    src = tmp / "00-系统/agents/handoff/recover.md"
    dst = tmp / "00-系统/agents/handoff/archive/recover.md"
    _sh.move(str(src), str(dst))
    # board entry removal + frontmatter closed were NOT performed -> the retry must recover
    result = run_command(tmp, ".orbitos/scripts/handoff-control.py", ["close", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "2", "--agent-id", "agent_a", "--session-id", session_id, "--summary", "accepted", "--reason", "recovery", "--slug", "flow_close_recover", "--output", f"project_file|{handoff}|updated", "--date", "2026-01-01"], True)
    check((tmp / "00-系统/agents/handoff/archive/recover.md").is_file(), "recovery keeps the archive")
    work = json.loads((tmp / ".orbitos/state/work-items.json").read_text(encoding="utf-8"))["items"][work_id]
    check(work["status"] == "done", "recovery closes the work item")
    record = queue_record(tmp, handoff)
    check(record["close"]["accepted_by"] == "agent_a", "recovery records the receipt")
    events = list((tmp / ".orbitos/logs/events").glob("*flow_close_recover*.yaml"))
    check(len(events) >= 1, "recovery writes the close event")
    validate_clone(tmp)
    # fully closed now: re-running close must succeed idempotently
    result2 = run_command(tmp, ".orbitos/scripts/handoff-control.py", ["close", "--handoff", handoff, "--work-id", work_id, "--expected-work-revision", "2", "--agent-id", "agent_a", "--session-id", session_id, "--summary", "accepted", "--reason", "recovery", "--slug", "flow_close_recover", "--output", f"project_file|{handoff}|updated", "--date", "2026-01-01"], True)
    check("already_closed" in (result2.stdout or ""), "second close returns already_closed")


def main():
    tmp = mini_runtime()
    print(f"mini runtime: {tmp}")
    try:
        test_relay_three_agent(tmp)
        test_launch_card_full(tmp)
        test_replan_structured_and_latest(tmp)
        test_mark_close_removed(tmp)
        test_queue_record_lost_fail_closed(tmp)
        test_builder_editor_gates(tmp)
        test_replan_failure_escalation(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    clone = clone_runtime()
    print(f"fresh runtime: {clone}")
    try:
        validate_clone(clone)
        test_full_close_two_agent(clone)
        test_full_close_multi_agent(clone)
        test_full_editor_approve(clone)
        test_full_editor_reject_rework(clone)
        test_close_recovery(clone)
    finally:
        shutil.rmtree(clone, ignore_errors=True)
    print("")
    print(f"flow test: {PASSED} assertions passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
