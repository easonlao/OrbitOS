"""Report open handoffs assigned to one registered Agent without changing state."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF_ROOT = ROOT / "00-系统" / "agents" / "handoff"
OPEN_STATUSES = {"delegated", "working", "returned"}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    return {
        key: value.strip().strip('"')
        for key, value in re.findall(r"^([a-z_]+):\s*(.*?)\s*$", match.group(1), re.MULTILINE)
    }


def registry_status(root, agent_id):
    registry_path = root / ".orbitos" / "agents" / "registry.yaml"
    if not registry_path.is_file():
        return None
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    for item in registry.get("agents", []) if isinstance(registry, dict) else []:
        if isinstance(item, dict) and item.get("agent_id") == agent_id:
            return item.get("status") or "active"
    return None


def main():
    parser = argparse.ArgumentParser(description="Report open OrbitOS handoffs for one Agent.")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else ROOT
    handoff_root = root / "00-系统" / "agents" / "handoff"
    if registry_status(root, args.agent_id) in {"offboarding", "offboarded"}:
        # Archived agents must not receive any claimable handoff context.
        print("handoff: none")
        return
    pending = []
    if handoff_root.is_dir():
        for path in sorted(handoff_root.glob("*.md")):
            data = frontmatter(path)
            if data.get("handoff_status") in OPEN_STATUSES and data.get("current_owner") == args.agent_id:
                pending.append((data["handoff_status"], data.get("next_action", ""), path.name))
    if not pending:
        print("handoff: none")
        return
    for status, next_action, name in pending:
        print(f"handoff: {status} | {name} | next: {next_action}")


if __name__ == "__main__":
    main()
