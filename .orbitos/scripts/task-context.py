"""Build a read-only, task-scoped context for one OrbitOS Agent."""

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OPEN_MAINTENANCE = {"detected", "classified", "assigned", "repairing", "verifying", "blocked"}
OPEN_HANDOFF = {"delegated", "working", "returned"}
OPEN_WORK = {"active", "waiting", "blocked"}
OPEN_COLLABORATION = {"open", "claimed", "working", "review_required", "returned", "blocked"}


def read_json(path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path):
    if not path.is_file():
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", path.read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        return {}
    return {
        key: value.strip().strip('"')
        for key, value in re.findall(r"^([a-z_]+):\s*(.*?)\s*$", match.group(1), re.MULTILINE)
    }


def inside(root, path):
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        raise ValueError("path must stay inside OrbitOS root")
    return resolved


def markdown_sections(path, wanted=None):
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current and line.strip():
            sections[current].append(line.rstrip())
    if wanted is None:
        return sections
    return {key: sections[key] for key in wanted if key in sections}


def resolve_inside(root, raw_path):
    candidate = Path(raw_path)
    return inside(root, candidate if candidate.is_absolute() else root / candidate)


def ancestor_dirs(root, target):
    anchor = target if target.is_dir() else target.parent
    if anchor == root:
        return [root]
    relative = anchor.relative_to(root)
    directories = [root]
    current = root
    for part in relative.parts:
        current = current / part
        directories.append(current)
    return directories


def project_context(root, raw_path):
    if not raw_path:
        return None
    target = resolve_inside(root, raw_path)
    agents_files = []
    for directory in ancestor_dirs(root, target):
        candidate = directory / "AGENTS.md"
        if candidate.is_file():
            agents_files.append(str(candidate.relative_to(root)))
    status_dir = target if target.is_dir() else target.parent
    status_path = status_dir / "STATUS.md"
    return {
        "requested_path": raw_path,
        "resolved_path": str(target.relative_to(root)),
        "agents_files": agents_files,
        "status": {
            "path": str(status_path.relative_to(root)),
            "exists": status_path.is_file(),
            "sections": markdown_sections(status_path, ("当前阶段", "当前重点", "关键待确认", "下一步入口")),
        },
    }


def profile_context(root, profile_ref):
    profile_path = resolve_inside(root, profile_ref)
    if not profile_path.is_file():
        return {
            "path": str(profile_path.relative_to(root)),
            "status": "missing",
            "frontmatter": {},
            "sections": {},
        }
    return {
        "path": str(profile_path.relative_to(root)),
        "status": "ok",
        "frontmatter": frontmatter(profile_path),
        "sections": markdown_sections(
            profile_path,
            ("基本信息", "部署信息", "当前定位", "最近工作", "启动关注", "运行记录", "待改进"),
        ),
    }


def environment_context(root, agent_id):
    env_path = root / ".orbitos" / "state" / "env" / f"{agent_id}.json"
    if not env_path.is_file():
        return {"path": str(env_path.relative_to(root)), "status": "missing"}
    return {
        "path": str(env_path.relative_to(root)),
        "status": "ok",
        "data": read_json(env_path),
    }


def maintenance_context(root):
    path = root / ".orbitos" / "state" / "maintenance.json"
    data = read_json(path)
    if data is None:
        return {"path": str(path.relative_to(root)), "status": "missing", "open_items": []}
    items = data.get("items", {}) if isinstance(data, dict) else {}
    open_items = []
    for maintenance_id in sorted(items):
        item = items[maintenance_id]
        if not isinstance(item, dict) or item.get("status") not in OPEN_MAINTENANCE:
            continue
        open_items.append(
            {
                "maintenance_id": item.get("maintenance_id", maintenance_id),
                "subject": item.get("subject"),
                "status": item.get("status"),
                "owner_agent": item.get("owner_agent"),
                "executor": item.get("executor"),
                "lease_owner": item.get("lease_owner"),
                "lease_until": item.get("lease_until"),
                "next_action": item.get("next_action"),
                "revision": item.get("revision"),
                "updated_at": item.get("updated_at"),
            }
        )
    return {"path": str(path.relative_to(root)), "status": "ok", "open_items": open_items}


def handoff_context(root, agent_id):
    handoff_root = root / "00-系统" / "agents" / "handoff"
    open_items = []
    if handoff_root.is_dir():
        for path in sorted(handoff_root.glob("*.md")):
            data = frontmatter(path)
            if data.get("current_owner") != agent_id or data.get("handoff_status") not in OPEN_HANDOFF:
                continue
            open_items.append(
                {
                    "path": str(path.relative_to(root)),
                    "title": data.get("title"),
                    "handoff_status": data.get("handoff_status"),
                    "current_owner": data.get("current_owner"),
                    "return_owner": data.get("return_owner"),
                    "next_action": data.get("next_action"),
                }
            )
    return {
        "path": str(handoff_root.relative_to(root)),
        "open_items": open_items,
    }


def work_context(root, agent_id):
    path = root / ".orbitos/state/work-items.json"
    if not path.is_file():
        return {"path": str(path.relative_to(root)), "status": "missing", "open_items": []}
    data = read_json(path)
    items = [
        item for item in data.get("items", {}).values()
        if item.get("status") in OPEN_WORK and item.get("agent_id") == agent_id
    ]
    items.sort(key=lambda item: (item.get("project", ""), item.get("work_id", "")))
    if any(item.get("status") == "active" for item in items):
        agent_status = "busy"
    elif any(item.get("requires_user") or item.get("status") == "blocked" for item in items):
        agent_status = "needs_user"
    elif items:
        agent_status = "waiting"
    else:
        agent_status = "available"
    return {"path": str(path.relative_to(root)), "status": "ok", "agent_status": agent_status, "open_items": items}


def collaboration_context(root, agent_id):
    path = root / ".orbitos" / "state" / "collaboration-sessions.json"
    data = read_json(path)
    if data is None:
        return {"path": str(path.relative_to(root)), "status": "missing", "open_sessions": []}
    sessions = [
        session
        for session in data.get("sessions", {}).values()
        if session.get("status") in OPEN_COLLABORATION and session.get("agent_id") == agent_id
    ]
    sessions.sort(key=lambda session: (session.get("project", ""), session.get("session_id", "")))
    return {"path": str(path.relative_to(root)), "status": "ok", "open_sessions": sessions}


def main():
    parser = argparse.ArgumentParser(description="Build a read-only Agent task context.")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--path")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        registry_path = root / ".orbitos" / "agents" / "registry.yaml"
        registry = read_json(registry_path)
        if not isinstance(registry, dict):
            raise ValueError(f"agent registry is missing or invalid: {registry_path}")
        agents = registry.get("agents", [])
        if not isinstance(agents, list):
            raise ValueError("agent registry has invalid agents list")
        agent = next((item for item in agents if isinstance(item, dict) and item.get("agent_id") == args.agent_id), None)
        if agent is None:
            raise ValueError(f"agent is not registered: {args.agent_id}")

        status = agent.get("status") or "active"
        if status in {"offboarding", "offboarded"}:
            # Archived/archiving agents must not aggregate any context: profile,
            # env, work, collab and handoff sources were archived or unbound.
            result = {
                "ok": True,
                "agent_id": args.agent_id,
                "status": status,
                "offboarded_at": agent.get("offboarded_at"),
                "offboard_reason": agent.get("offboard_reason"),
                "registry": {
                    "path": str(registry_path.relative_to(root)),
                    "entry": agent,
                },
                "claimable": [],
                "notice": (
                    "agent 已注销，不聚合任务上下文"
                    if status == "offboarded"
                    else "agent 注销中，不聚合任务上下文"
                ),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        profile_ref = agent.get("profile_ref")
        if not isinstance(profile_ref, str) or not profile_ref.strip():
            raise ValueError(f"agent registry entry is missing profile_ref: {args.agent_id}")

        result = {
            "ok": True,
            "agent_id": args.agent_id,
            "registry": {
                "path": str(registry_path.relative_to(root)),
                "entry": agent,
            },
            "profile": profile_context(root, profile_ref),
            "environment": environment_context(root, args.agent_id),
            "maintenance": maintenance_context(root),
            "work": work_context(root, args.agent_id),
            "collaboration": collaboration_context(root, args.agent_id),
            "handoffs": handoff_context(root, args.agent_id),
            "project": project_context(root, args.path) if args.path else None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
