"""Refresh only the managed date and attention projection blocks."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DATE_START = "<!-- orbitos:today-date:start -->"
DATE_END = "<!-- orbitos:today-date:end -->"
PROJECTION_START = "<!-- orbitos:today-projection:start -->"
PROJECTION_END = "<!-- orbitos:today-projection:end -->"
HEALTH_START = "<!-- orbitos:system-health:start -->"
HEALTH_END = "<!-- orbitos:system-health:end -->"
OPEN_STATUSES = {"detected", "classified", "assigned", "repairing", "verifying", "blocked"}


class RefreshError(Exception):
    pass


def read_preserving_newlines(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_preserving_newlines(path, content):
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def replace_marker(content, start, end, body):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{body}\n{end}"
    updated, count = pattern.subn(replacement, content, count=1)
    if count != 1:
        raise RefreshError(f"managed marker pair is missing: {start}")
    return updated


def load_state(root):
    path = root / ".orbitos/state/maintenance.json"
    if not path.is_file():
        raise RefreshError(f"maintenance state is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RefreshError(f"maintenance state is invalid JSON: {error}") from error


def run_system_check(root, executor):
    script = root / ".orbitos/scripts/automation-health.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--executor", executor],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RefreshError(result.stderr.strip() or "System Check preflight failed")
    return result.returncode


def reconcile_stale_state(root, executor, max_age_seconds):
    script = root / ".orbitos/scripts/maintenance-control.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(root),
            "reconcile",
            "--executor",
            executor,
            "--max-age-seconds",
            str(max_age_seconds),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RefreshError(result.stderr.strip() or "maintenance reconciliation failed")


def offboarded_agent_ids(root):
    """Registry agent_ids whose lifecycle status is offboarded."""
    registry_path = root / ".orbitos" / "agents" / "registry.yaml"
    if not registry_path.is_file():
        return set()
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return set()
    return {
        item.get("agent_id")
        for item in (registry.get("agents", []) if isinstance(registry, dict) else [])
        if isinstance(item, dict) and (item.get("status") or "active") == "offboarded"
    }


def offboard_summary(root, limit=5):
    """Scan event files for agent_offboarding events, newest last."""
    events_root = root / ".orbitos" / "logs" / "events"
    if not events_root.is_dir():
        return []
    entries = []
    for event_path in sorted(events_root.glob("*.yaml")):
        try:
            event = json.loads(event_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(event, dict) or event.get("event_type") != "agent_offboarding":
            continue
        actor = event.get("actor") if isinstance(event.get("actor"), dict) else {}
        archive_ref = None
        outputs = event.get("outputs")
        if isinstance(outputs, list):
            for output in outputs:
                if isinstance(output, dict) and output.get("kind") == "artifact" and output.get("ref"):
                    archive_ref = output["ref"]
                    break
        entries.append(
            {
                "agent_id": actor.get("agent_id") or actor.get("name") or "unknown",
                "timestamp": event.get("timestamp"),
                "reason": event.get("reason"),
                "archive_dir": archive_ref,
            }
        )
    return entries[-limit:]


def item_line(item, offboarded_ids=frozenset()):
    subject = item.get("subject", item.get("maintenance_id"))
    action = item.get("next_action") or "继续检查"
    owner = item.get("owner_agent") or "待分配"
    marker = "（负责人已注销，待人工重新分配）" if owner in offboarded_ids else ""
    return f"- **{subject}**：责任 Agent `{owner}`{marker}；下一步：{action}。"


def project_focus(root):
    focus = []
    project_root = root / "03-项目"
    if project_root.is_dir():
        for project_dir in sorted(path for path in project_root.iterdir() if path.is_dir()):
            status_path = project_dir / "STATUS.md"
            if not status_path.is_file():
                continue
            text = status_path.read_text(encoding="utf-8")
            match = re.search(r"^## 当前重点\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
            if not match:
                continue
            for line in match.group(1).splitlines():
                if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
                    summary = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip()
                    focus.append(f"- [[../03-项目/{project_dir.name}/STATUS|{project_dir.name}]]：{summary}")
                    if len(focus) >= 5:
                        return focus
    return focus or ["- 暂无新的业务重点。"]


def project_draft_decisions(root):
    draft_root = root / "04-知识/00-草稿箱"
    if not draft_root.is_dir():
        return []
    decisions = []
    for draft in sorted(draft_root.glob("*.md")):
        if draft.name.upper() in {"MAP.MD", "README.MD", "AGENTS.MD"}:
            continue
        relative = draft.relative_to(root).with_suffix("").as_posix()
        decisions.append(
            f"- [[../{relative}|{draft.stem}]]：候选知识待确认；Agent 不会自动提升为正式知识。"
        )
    return decisions


def render_projection(root, state):
    items = list(state.get("items", {}).values())
    active = [item for item in items if item.get("status") in OPEN_STATUSES]
    offboarded_ids = offboarded_agent_ids(root)
    decisions = [item for item in active if item.get("status") == "blocked" or item.get("requires_user")]
    draft_decisions = project_draft_decisions(root)
    processing = [
        item
        for item in active
        if item not in decisions
        and item.get("owner_agent")
        and item.get("next_action")
        and item.get("last_observed_at")
        and item.get("evidence_refs")
    ]
    unassigned = [item for item in active if item not in decisions and item not in processing]
    latest_receipt = state.get("receipts", [])[-1] if state.get("receipts") else None
    if latest_receipt:
        system_receipt = f"{latest_receipt.get('status')} / {latest_receipt.get('executor')}"
    else:
        system_receipt = "暂无运行凭证"

    focus = project_focus(root)
    lines = ["## 1. 业务重点", "", *focus, "", "## 2. 需要用户决定", ""]
    if decisions:
        lines.extend(item_line(item, offboarded_ids) for item in decisions)
    if draft_decisions:
        lines.extend(draft_decisions)
    if not decisions and not draft_decisions:
        lines.append("- 暂无。")
    lines.extend(["", "## 3. Agent 正在处理", ""])
    if processing:
        lines.extend(item_line(item, offboarded_ids) for item in processing)
    else:
        lines.append("- 暂无。")
    lines.extend(
        [
            "",
            "## 4. 简洁系统状态",
            "",
            f"- 最近运行凭证：{system_receipt}。",
            f"- 当前维护事项：开放 {len(active)} 项；未归责 {len(unassigned)} 项。",
        ]
    )
    offboarded = offboard_summary(root)
    if offboarded:
        lines.extend(["", "## 5. 已注销 Agent", ""])
        for entry in offboarded:
            when = (entry["timestamp"] or "")[:10] or "日期未知"
            lines.append(
                f"- `{entry['agent_id']}`：{when} 注销。原因：{entry['reason']}。归档：{entry['archive_dir']}。"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Refresh the managed Today projection.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--executor", default="automation-health")
    parser.add_argument("--max-item-age-seconds", type=int, default=86400)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    today_path = root / "02-时间线/今日.md"
    try:
        validation_code = run_system_check(root, args.executor)
        reconcile_stale_state(root, args.executor, args.max_item_age_seconds)
        content = read_preserving_newlines(today_path)
        state = load_state(root)
        projection = render_projection(root, state)
        content = replace_marker(content, DATE_START, DATE_END, f"> 日期：{datetime.now().strftime('%Y-%m-%d')}")
        content = replace_marker(content, PROJECTION_START, PROJECTION_END, projection)
        write_preserving_newlines(today_path, content)
        validation_code = run_system_check(root, args.executor)
        content = read_preserving_newlines(today_path)
        state = load_state(root)
        projection = render_projection(root, state)
        content = replace_marker(content, PROJECTION_START, PROJECTION_END, projection)
        write_preserving_newlines(today_path, content)
    except (OSError, RefreshError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "validation_returncode": validation_code}, ensure_ascii=False))
    return validation_code


if __name__ == "__main__":
    raise SystemExit(main())
