"""Report open handoffs assigned to one registered Agent without changing state."""

import argparse
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


def main():
    parser = argparse.ArgumentParser(description="Report open OrbitOS handoffs for one Agent.")
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()
    pending = []
    if HANDOFF_ROOT.is_dir():
        for path in sorted(HANDOFF_ROOT.glob("*.md")):
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
