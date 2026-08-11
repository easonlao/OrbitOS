"""Formal Handoff queue control: launch card, confirmation, stage relay, and re-plan.

The queue projection lives in .orbitos/state/handoff-queues.json keyed by the
handoff relative path. Completed stages are immutable; only the unfinished
portion of the queue can be revised through a user-confirmed re-plan.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE_STATE = ".orbitos/state/handoff-queues.json"
QUEUE_SCHEMA = ".orbitos/schemas/handoff-queue.schema.yaml"
ROLES = {"coordinator", "researcher", "writer", "builder", "editor"}
REPLAN_TRIGGERS = {"unavailable", "scope", "failure"}
BOARD = "00-" + "\u7cfb\u7edf/agents/BOARD.md"


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
    active_root = (root / ("00-" + "\u7cfb\u7edf/agents/handoff")).resolve()
    if active_root not in path.parents or path.suffix != ".md" or not path.is_file():
        raise ValueError("handoff must be an existing Markdown file under the active handoff directory")
    return path


def relative_path(root, path):
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_state(root):
    path = root / QUEUE_STATE
    if not path.is_file():
        return {"version": 1, "updated_at": now(), "queues": {}}
    data = read_json(path)
    if data.get("version") != 1 or not isinstance(data.get("queues"), dict):
        raise ValueError("handoff queue state must have version=1 and object queues")
    return data


def save_state(root, data):
    data["updated_at"] = now()
    write_json(root / QUEUE_STATE, data)


def registered_agents(root):
    candidates = [
        root / ".orbitos/agents/registry.yaml",
        root / ".orbitos/templates/.orbitos/agents/registry.yaml",
    ]
    for path in candidates:
        if path.is_file():
            registry = read_json(path)
            return {item.get("agent_id") for item in registry.get("agents", []) if isinstance(item, dict)}
    raise ValueError("agent registry is missing")


def queue_for(root, relative):
    return load_state(root)["queues"].get(relative)


def parse_stage(raw):
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 7 or not all(parts[:6]):
        raise ValueError("stage spec must use stage_id|tool|role|deliverable|scope|acceptance|next_stage")
    stage_id, tool, role, deliverable, scope, acceptance, next_stage = parts
    if role not in ROLES:
        raise ValueError(f"unknown stage role: {role}")
    return {
        "stage_id": stage_id,
        "tool": tool,
        "role": role,
        "deliverable": deliverable,
        "scope": scope,
        "acceptance": acceptance,
        "next_stage": next_stage or None,
    }


def validate_queue(specs, root, existing=None):
    if len(specs) < 2:
        raise ValueError("a confirmed queue needs at least two ordered stages")
    ids = [spec["stage_id"] for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("stage ids must be unique")
    registered = registered_agents(root)
    for spec in specs:
        if spec["tool"] not in registered:
            raise ValueError(f"stage tool is not a registered agent tool: {spec['tool']}")
        if spec["next_stage"] and spec["next_stage"] not in ids:
            raise ValueError(f"stage next_stage points to an unknown stage: {spec['next_stage']}")
    for index, spec in enumerate(specs):
        if index < len(specs) - 1 and spec["next_stage"] != specs[index + 1]["stage_id"]:
            raise ValueError(f"stage chain is broken at {spec['stage_id']}")
    builder_tool = next((spec["tool"] for spec in specs if spec["role"] == "builder"), None)
    editor_tool = next((spec["tool"] for spec in specs if spec["role"] == "editor"), None)
    if builder_tool and editor_tool and builder_tool == editor_tool:
        raise ValueError("the Editor tool identity must differ from the Builder tool identity")
    if existing:
        completed = [
            stage_id
            for stage_id in existing["stage_order"]
            if existing["stages"][stage_id].get("status") == "complete"
        ]
        if len(specs) < len(completed):
            raise ValueError("re-plan must keep completed stages in place and unmodified")
        for index, stage_id in enumerate(completed):
            new_spec = specs[index]
            old = existing["stages"][stage_id]
            if (
                new_spec["stage_id"] != stage_id
                or new_spec["tool"] != old["tool"]
                or new_spec["role"] != old["role"]
                or new_spec["deliverable"] != old["deliverable"]
                or new_spec["scope"] != old["scope"]
                or new_spec["acceptance"] != old["acceptance"]
                or new_spec["next_stage"] != old.get("next_stage")
            ):
                raise ValueError("re-plan must keep completed stages in place and unmodified")
    return specs


def append_section(path, heading, lines):
    """Append a section; if the heading already exists, extend it instead of failing."""
    text = path.read_text(encoding="utf-8")
    section = "\n".join(lines) + "\n"
    marker = f"## {heading}\n"
    index = text.find(marker)
    if index == -1:
        path.write_text(text.rstrip() + "\n## " + heading + "\n\n" + section, encoding="utf-8", newline="\n")
        return
    head = text[:index]
    rest = text[index + len(marker):]
    match = re.search(r"\n## ", rest)
    body, tail = (rest[:match.start()], rest[match.start():]) if match else (rest, "")
    path.write_text(head + marker + body.rstrip("\n") + "\n" + section + tail, encoding="utf-8", newline="\n")


def launch(args, root):
    handoff = active_handoff(root, args.handoff)
    text, _match, metadata = frontmatter(handoff)
    if metadata.get("handoff_status") != "delegated":
        raise ValueError("launch requires a delegated handoff that has not started")
    declared_return_owner = (metadata.get("return_owner") or "").strip()
    if declared_return_owner and declared_return_owner != args.return_owner:
        raise ValueError(f"return owner mismatch: handoff frontmatter holds {declared_return_owner}, launch passed {args.return_owner}")
    relative = relative_path(root, handoff)
    state = load_state(root)
    if relative in state["queues"]:
        raise ValueError("this handoff already has a confirmed or proposed queue")
    specs = validate_queue([parse_stage(raw) for raw in args.queue], root)
    if args.agent_id not in registered_agents(root):
        raise ValueError(f"agent is not registered: {args.agent_id}")
    if args.return_owner not in registered_agents(root):
        raise ValueError(f"return owner is not a registered agent tool: {args.return_owner}")
    if args.role not in ROLES:
        raise ValueError(f"unknown launch role: {args.role}")
    timestamp = now()
    stages = {
        spec["stage_id"]: {
            **spec,
            "status": "pending",
            "result": None,
            "evidence": [],
            "unresolved": None,
            "outcome": None,
            "failures": 0,
            "output_revision": 0,
            "reviewed_revision": None,
            "completed_by": None,
            "completed_at": None,
        }
        for spec in specs
    }
    first = specs[0]
    second = specs[1] if len(specs) > 1 else None
    record = {
        "handoff": relative,
        "return_owner": args.return_owner,
        "prohibited": args.prohibited,
        "return_format": args.return_format,
        "plan_revision": 0,
        "plan_status": "proposed",
        "confirmed_by": None,
        "confirmed_receipt": None,
        "current_stage": "none",
        "current_owner": first["tool"],
        "current_role": first["role"],
        "next_owner": second["tool"] if second else args.return_owner,
        "next_action": args.next_action,
        "stage_order": [spec["stage_id"] for spec in specs],
        "stages": stages,
        "replans": [],
        "close": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    rows = ["| 阶段 | 工具 | 角色 | 交付物 | 范围 | 验收条件 | 下一阶段 |", "|---|---|---|---|---|---|---|"]
    for spec in specs:
        rows.append(f"| {spec['stage_id']} | {spec['tool']} | {spec['role']} | {spec['deliverable']} | {spec['scope']} | {spec['acceptance']} | {spec['next_stage'] or '(回验收方)'} |")
    rows.append("")
    rows.append(f"- 禁止事项：{args.prohibited or '未声明'}")
    rows.append(f"- 返回格式：{args.return_format or '未声明'}")
    rows.append(f"- 验收方：{args.return_owner}")
    # write Markdown first so content failures never leave a half-persisted queue
    append_section(handoff, "阶段队列", rows)
    state["queues"][relative] = record
    save_state(root, state)
    update_frontmatter(handoff, {"updated": args.date, "plan_status": "proposed", "plan_revision": "0", "current_stage": "none", "next_owner": record["next_owner"], "current_role": first["role"]})
    print(json.dumps({
        "ok": True,
        "handoff": args.handoff,
        "plan_status": "proposed",
        "plan_revision": 0,
        "stages": [spec["stage_id"] for spec in specs],
        "return_owner": args.return_owner,
        "prohibited": args.prohibited,
        "return_format": args.return_format,
        "confirm_instruction": "请用户确认该队列后执行 confirm --plan-revision 0 --receipt <确认回执>",
    }, ensure_ascii=False))


def _confirm_guard(root, relative, agent_id, expected_revision):
    state = load_state(root)
    record = state["queues"].get(relative)
    if not record:
        raise ValueError("handoff has no queue plan; run launch first")
    if record["plan_status"] != "proposed":
        raise ValueError("only a proposed plan can be confirmed")
    if record["plan_revision"] != expected_revision:
        raise ValueError(f"stale plan revision: expected {record['plan_revision']}, got {expected_revision}")
    if agent_id not in registered_agents(root):
        raise ValueError(f"agent is not registered: {agent_id}")
    return state, record


def confirm(args, root):
    handoff = active_handoff(root, args.handoff)
    relative = relative_path(root, handoff)
    state, record = _confirm_guard(root, relative, args.agent_id, args.plan_revision)
    if not args.receipt:
        raise ValueError("confirm requires a --receipt (the user confirmation reference)")
    # The authoritative return owner is the one persisted at launch, not the caller's argument.
    return_owner = record["return_owner"]
    if args.return_owner and args.return_owner != return_owner:
        raise ValueError(f"return owner mismatch: plan holds {return_owner}, caller passed {args.return_owner}")
    # The user confirms in the launching conversation; require the initiator tool or the return owner.
    first_tool = record["stages"][record["stage_order"][0]]["tool"]
    if args.agent_id not in {first_tool, return_owner}:
        raise ValueError("confirm must be executed by the first stage tool or the return owner")
    current = next((stage_id for stage_id in record["stage_order"] if record["stages"][stage_id]["status"] != "complete"), record["stage_order"][0])
    stage = record["stages"][current]
    record["plan_status"] = "confirmed"
    record["confirmed_by"] = "user"
    record["confirmed_receipt"] = args.receipt
    # Only the latest pending re-plan revision is confirmed by this receipt; older
    # superseded revisions stay unconfirmed so the history stays truthful.
    if record["replans"]:
        latest = record["replans"][-1]
        if not latest.get("confirmed_at"):
            latest["confirmed_at"] = now()
    record["current_stage"] = current
    record["current_owner"] = stage["tool"]
    record["current_role"] = stage["role"]
    record["next_owner"] = stage["next_stage"] and record["stages"][stage["next_stage"]]["tool"] or return_owner
    record["next_action"] = stage["deliverable"] + "；说：获取交接工作"
    record["updated_at"] = now()
    save_state(root, state)
    update_frontmatter(handoff, {
        "updated": args.date,
        "plan_status": "confirmed",
        "plan_revision": str(record["plan_revision"]),
        "current_stage": current,
        "current_owner": stage["tool"],
        "current_role": stage["role"],
        "next_owner": record["next_owner"],
        "next_action": record["next_action"],
    })
    _board_replace(root, handoff.stem, "delegated", stage["tool"], record["next_action"])
    print(json.dumps({
        "ok": True,
        "plan_status": "confirmed",
        "plan_revision": record["plan_revision"],
        "confirmed_receipt": args.receipt,
        "current_stage": current,
        "current_owner": stage["tool"],
        "current_role": stage["role"],
        "pickup_instruction": f"在 {stage['tool']} 中说：获取交接工作",
    }, ensure_ascii=False))


def _pending_replan(record):
    """Only the latest re-plan revision gates progress; superseded ones stay historical."""
    if not record.get("replans"):
        return None
    latest = record["replans"][-1]
    return latest if not latest.get("confirmed_at") else None


def advance(args, root):
    handoff = active_handoff(root, args.handoff)
    relative = relative_path(root, handoff)
    state = load_state(root)
    record = state["queues"].get(relative)
    if not record:
        raise ValueError("handoff has no queue plan; run launch first")
    return_owner = record["return_owner"]
    if args.return_owner and args.return_owner != return_owner:
        raise ValueError(f"return owner mismatch: plan holds {return_owner}, caller passed {args.return_owner}")
    if record["plan_status"] != "confirmed":
        raise ValueError("the queue must be confirmed by the user before any stage advances")
    if _pending_replan(record):
        raise ValueError("a re-plan is waiting for user confirmation; no stage can advance")
    if record["current_stage"] != args.stage_id:
        raise ValueError(f"only the current stage can advance: {record['current_stage']}")
    if record["current_owner"] != args.agent_id:
        raise ValueError(f"only the current owner can advance this stage: {record['current_owner']}")
    if record["current_role"] != args.role:
        raise ValueError(f"stage role mismatch: expected {record['current_role']}, got {args.role}")
    stage = record["stages"][args.stage_id]
    if stage["status"] == "complete":
        raise ValueError("a completed stage is immutable and cannot advance again")
    if stage["failures"] >= 2:
        raise ValueError("this stage failed twice; a user-confirmed re-plan is required")
    if stage["role"] == "editor":
        order = record["stage_order"]
        index = order.index(args.stage_id)
        if index == 0:
            raise ValueError("an editor stage cannot be the first stage")
        producer = record["stages"][order[index - 1]]
        if producer["role"] not in {"builder", "writer"} or producer["status"] != "complete":
            raise ValueError("an editor stage must follow a completed builder/writer stage")
        if args.outcome == "done":
            if not any(order[index - 1] in (item or "") for item in (args.evidence or [])):
                raise ValueError(f"editor evidence must reference the reviewed stage output ({order[index - 1]})")
            if args.reviewed_revision is None:
                raise ValueError("editor approval requires --reviewed-revision bound to the reviewed stage output")
            if args.reviewed_revision != producer.get("output_revision"):
                raise ValueError(f"editor reviewed_revision {args.reviewed_revision} does not match the reviewed stage output revision {producer.get('output_revision')}")
    if args.outcome == "done":
        if not args.result or not args.evidence:
            raise ValueError("a done stage requires --result and at least one --evidence")
    else:
        if not args.unresolved:
            raise ValueError("a blocked stage requires --unresolved")
        stage["failures"] += 1
        stage["status"] = "blocked"
        stage["unresolved"] = args.unresolved
        record["next_action"] = args.next_action or "同阶段重试或请求 re-plan"
        record["updated_at"] = now()
        append_section(handoff, "阶段记录", [f"- {args.stage_id} 由 {args.agent_id} 阻塞（{stage['role']}）：{args.unresolved}（failures={stage['failures']}）"])
        save_state(root, state)
        update_frontmatter(handoff, {"updated": args.date, "handoff_status": "delegated", "current_role": stage["role"], "next_owner": record["next_owner"], "next_action": record["next_action"]})
        _board_replace(root, handoff.stem, "delegated", record["current_owner"], record["next_action"])
        print(json.dumps({"ok": True, "stage": args.stage_id, "status": "blocked", "failures": stage["failures"], "replan_required": stage["failures"] >= 2}, ensure_ascii=False))
        return
    stage.update({
        "status": "complete",
        "result": args.result,
        "evidence": list(args.evidence),
        "unresolved": args.unresolved,
        "outcome": "done",
        "output_revision": (stage.get("output_revision") or 0) + 1,
        "reviewed_revision": args.reviewed_revision,
        "completed_by": args.agent_id,
        "completed_at": now(),
    })
    next_stage = stage["next_stage"]
    if next_stage:
        target = record["stages"][next_stage]
        record["current_stage"] = next_stage
        record["current_owner"] = target["tool"]
        record["current_role"] = target["role"]
        record["next_owner"] = target["next_stage"] and record["stages"][target["next_stage"]]["tool"] or return_owner
        record["next_action"] = target["deliverable"] + "；说：获取交接工作"
        handoff_status, next_action = "delegated", record["next_action"]
    else:
        record["current_stage"] = args.stage_id
        record["current_owner"] = return_owner
        record["current_role"] = None
        record["next_owner"] = return_owner
        record["next_action"] = "验收：核对全部阶段产出后关闭交接"
        handoff_status, next_action = "returned", record["next_action"]
    record["updated_at"] = now()
    evidence = "；".join(args.evidence or [])
    unresolved = args.unresolved or "无"
    append_section(handoff, "阶段记录", [f"- {args.stage_id} 由 {args.agent_id} 完成（{stage['role']}）：{args.result}；证据：{evidence}；未决：{unresolved}"])
    save_state(root, state)
    update_frontmatter(handoff, {
        "updated": args.date,
        "handoff_status": handoff_status,
        "current_stage": record["current_stage"],
        "current_owner": record["current_owner"],
        "current_role": record["current_role"],
        "next_owner": record["next_owner"],
        "next_action": next_action,
    })
    _board_replace(root, handoff.stem, handoff_status, record["current_owner"], next_action)
    if next_stage:
        target = record["stages"][next_stage]
        print(json.dumps({
            "ok": True,
            "stage": args.stage_id,
            "next_tool": target["tool"],
            "next_role": target["role"],
            "next_action": record["next_action"],
            "pickup_instruction": f"在 {target['tool']} 中说：获取交接工作",
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "ok": True,
            "stage": args.stage_id,
            "all_stages_complete": True,
            "return_owner": return_owner,
            "acceptance_instruction": f"在 {return_owner} 中验收并关闭交接",
        }, ensure_ascii=False))


def replan(args, root):
    handoff = active_handoff(root, args.handoff)
    relative = relative_path(root, handoff)
    state = load_state(root)
    record = state["queues"].get(relative)
    if not record:
        raise ValueError("handoff has no queue plan; run launch first")
    if record["current_owner"] != args.agent_id:
        raise ValueError(f"only the current owner can trigger a re-plan: {record['current_owner']}")
    if args.trigger == "failure":
        affected = record["stages"].get(args.affected_stage)
        if not affected or affected.get("failures", 0) < 2:
            raise ValueError("failure trigger requires a stage that already failed twice")
    if args.trigger != "failure" and args.affected_stage not in record["stages"]:
        raise ValueError(f"unknown affected stage: {args.affected_stage}")
    specs = validate_queue([parse_stage(raw) for raw in args.proposed_queue], root, existing=record)
    new_order = [spec["stage_id"] for spec in specs]
    old_stages = record["stages"]
    stages = {}
    for stage_id, old in old_stages.items():
        if old["status"] == "complete":
            stages[stage_id] = old
    for spec in specs:
        stage_id = spec["stage_id"]
        if stage_id in stages:
            continue
        stages[stage_id] = {
            **spec,
            "status": "pending",
            "result": None,
            "evidence": [],
            "unresolved": None,
            "outcome": None,
            "failures": 0,
            "output_revision": 0,
            "reviewed_revision": None,
            "completed_by": None,
            "completed_at": None,
        }
    revision = record["plan_revision"] + 1
    record["plan_revision"] = revision
    record["plan_status"] = "proposed"
    record["stage_order"] = new_order
    record["stages"] = stages
    record["replans"].append({
        "revision": revision,
        "trigger": args.trigger,
        "affected_stage": args.affected_stage,
        "reason": args.reason,
        "valid_results": args.valid_results,
        "invalidated_assumptions": args.invalidated_assumptions,
        "replacement_role": args.replacement_role,
        "proposed_by": args.agent_id,
        "proposed_at": now(),
        "confirmed_at": None,
    })
    record["next_action"] = f"等待用户确认修订队列（plan_revision={revision}）"
    record["updated_at"] = now()
    rows = ["| 阶段 | 工具 | 角色 | 交付物 | 范围 | 验收条件 | 下一阶段 |", "|---|---|---|---|---|---|---|"]
    for spec in specs:
        rows.append(f"| {spec['stage_id']} | {spec['tool']} | {spec['role']} | {spec['deliverable']} | {spec['scope']} | {spec['acceptance']} | {spec['next_stage'] or '(回验收方)'} |")
    lines = [f"- 触发：{args.trigger}", f"- 受影响阶段：{args.affected_stage}", f"- 原因：{args.reason}", f"- 修订 plan_revision：{revision}", f"- 提议者：{args.agent_id}", ""] + rows
    # write Markdown first: a failed append must not leave revision advanced in the projection
    append_section(handoff, "计划修订", lines)
    save_state(root, state)
    update_frontmatter(handoff, {"updated": args.date, "plan_status": "proposed", "plan_revision": str(revision), "next_action": record["next_action"]})
    print(json.dumps({
        "ok": True,
        "plan_revision": revision,
        "plan_status": "proposed",
        "stages": new_order,
        "confirm_instruction": f"请用户确认后执行 confirm --plan-revision {revision}",
    }, ensure_ascii=False))


def status(args, root):
    handoff = active_handoff(root, args.handoff)
    relative = relative_path(root, handoff)
    record = queue_for(root, relative)
    print(json.dumps({"ok": True, "queue": record}, ensure_ascii=False))


def mark_close(args, root):
    relative = args.handoff.replace("\\", "/")
    if not relative.startswith("00-" + "\u7cfb\u7edf/agents/handoff/") or not relative.endswith(".md"):
        raise ValueError("handoff must be under the active handoff directory")
    state = load_state(root)
    record = state["queues"].get(relative)
    if not record:
        raise ValueError("handoff has no queue plan")
    if record.get("close"):
        raise ValueError("this handoff is already closed")
    # mark-close is the acceptance receipt: it must satisfy the same gates as close.
    if record["plan_status"] != "confirmed":
        raise ValueError("close receipt requires a user-confirmed queue plan")
    if _pending_replan(record):
        raise ValueError("a re-plan is still waiting for user confirmation")
    incomplete = [
        stage_id
        for stage_id in record.get("stage_order", [])
        if record.get("stages", {}).get(stage_id, {}).get("status") != "complete"
    ]
    if incomplete:
        raise ValueError(f"close receipt requires all planned stages complete; pending: {incomplete}")
    if record.get("current_owner") != args.accepted_by:
        raise ValueError("close receipt requires the return owner to hold the baton")
    if record.get("return_owner") != args.accepted_by:
        raise ValueError("close receipt must be issued by the authoritative return owner")
    if not args.archived_ref.startswith("00-" + "\u7cfb\u7edf/agents/handoff/archive/"):
        raise ValueError("close receipt archive reference must live under the archive directory")
    record["close"] = {
        "accepted_by": args.accepted_by,
        "accepted_at": now(),
        "archived_ref": args.archived_ref,
    }
    record["updated_at"] = now()
    save_state(root, state)
    print(json.dumps({"ok": True, "handoff": relative, "close": record["close"]}, ensure_ascii=False))


def _board_replace(root, stem, status, owner, next_action):
    path = root / BOARD
    text = path.read_text(encoding="utf-8")
    pattern = rf"^- \[\[handoff/{re.escape(stem)}\|([^\]]+)\]\].*$"
    replacement = rf"- [[handoff/{stem}|\1]] | 状态：{status} | 当前负责人：{owner} | 下一步：{next_action}"
    updated, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count == 0:
        text = text.rstrip() + f"\n- [[handoff/{stem}|{stem}]] | 状态：{status} | 当前负责人：{owner} | 下一步：{next_action}\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        return
    if count != 1:
        raise ValueError("handoff board entry is ambiguous")
    path.write_text(updated, encoding="utf-8", newline="\n")


def parser():
    root = argparse.ArgumentParser(description="Control the Formal Handoff queue: launch, confirm, advance, re-plan.")
    root.add_argument("--root")
    commands = root.add_subparsers(dest="command", required=True)
    launching = commands.add_parser("launch")
    launching.add_argument("--handoff", required=True)
    launching.add_argument("--agent-id", required=True)
    launching.add_argument("--role", choices=sorted(ROLES), required=True)
    launching.add_argument("--return-owner", required=True)
    launching.add_argument("--prohibited")
    launching.add_argument("--return-format")
    launching.add_argument("--next-action", required=True)
    launching.add_argument("--queue", action="append", required=True)
    launching.add_argument("--date", required=True)
    confirming = commands.add_parser("confirm")
    confirming.add_argument("--handoff", required=True)
    confirming.add_argument("--agent-id", required=True)
    confirming.add_argument("--plan-revision", type=int, required=True)
    confirming.add_argument("--return-owner", required=True)
    confirming.add_argument("--receipt", required=True)
    confirming.add_argument("--date", required=True)
    advancing = commands.add_parser("advance")
    advancing.add_argument("--handoff", required=True)
    advancing.add_argument("--agent-id", required=True)
    advancing.add_argument("--role", choices=sorted(ROLES), required=True)
    advancing.add_argument("--stage-id", required=True)
    advancing.add_argument("--return-owner", required=True)
    advancing.add_argument("--date", required=True)
    advancing.add_argument("--next-action")
    advancing.add_argument("--result")
    advancing.add_argument("--evidence", action="append")
    advancing.add_argument("--reviewed-revision", type=int)
    advancing.add_argument("--unresolved")
    advancing.add_argument("--outcome", choices=("done", "blocked"), required=True)
    replanning = commands.add_parser("replan")
    replanning.add_argument("--handoff", required=True)
    replanning.add_argument("--agent-id", required=True)
    replanning.add_argument("--trigger", choices=sorted(REPLAN_TRIGGERS), required=True)
    replanning.add_argument("--affected-stage", required=True)
    replanning.add_argument("--reason", required=True)
    replanning.add_argument("--valid-results")
    replanning.add_argument("--invalidated-assumptions")
    replanning.add_argument("--replacement-role")
    replanning.add_argument("--proposed-queue", action="append", required=True)
    replanning.add_argument("--date", required=True)
    statusing = commands.add_parser("status")
    statusing.add_argument("--handoff", required=True)
    closing = commands.add_parser("mark-close")
    closing.add_argument("--handoff", required=True)
    closing.add_argument("--accepted-by", required=True)
    closing.add_argument("--archived-ref", required=True)
    closing.add_argument("--date", required=True)
    return root


def main():
    args = parser().parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        if args.command == "launch":
            launch(args, root)
        elif args.command == "confirm":
            confirm(args, root)
        elif args.command == "advance":
            advance(args, root)
        elif args.command == "replan":
            replan(args, root)
        elif args.command == "mark-close":
            mark_close(args, root)
        else:
            status(args, root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
