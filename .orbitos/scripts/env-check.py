import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def command_version(command, args):
    executable = shutil.which(command)
    if executable is None:
        return {"available": False, "path": None, "version": None}
    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = (result.stdout or result.stderr).strip().splitlines()
        version = output[0] if output else None
        return {
            "available": result.returncode == 0,
            "path": executable,
            "version": version,
        }
    except Exception as exc:
        return {
            "available": False,
            "path": executable,
            "version": None,
            "error": str(exc),
        }


def root_valid(root):
    required = [
        root / "AGENTS.md",
        root / ".orbitos" / "scripts" / "run-validation.py",
    ]
    return all(path.exists() for path in required)


def registry_status(root, agent_id):
    """Return the registry lifecycle status for agent_id, or None if absent."""
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
    parser = argparse.ArgumentParser(description="Check the OrbitOS runtime environment.")
    parser.add_argument("--agent-id", default="unknown", help="Stable OrbitOS agent_id.")
    parser.add_argument("--root", default=None, help="OrbitOS root path. Defaults to repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    status = registry_status(root, args.agent_id)
    if status in {"offboarding", "offboarded"}:
        # Archived agents must not have their env report recreated (offboard
        # moved the file into 99-归档/agents-{id}-{date}/env-{id}.json).
        report = {
            "ok": False,
            "agent_id": args.agent_id,
            "checked_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "orbitos_path": str(root),
            "status": status,
            "error": f"agent is {status}",
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    python_info = {
        "available": True,
        "path": sys.executable,
        "version": sys.version.split()[0],
    }
    node_info = command_version("node", ["--version"])
    git_info = command_version("git", ["--version"])
    pwsh_info = command_version("pwsh", ["--version"])

    valid_root = root_valid(root)
    optional_missing = not node_info["available"] or not git_info["available"] or not pwsh_info["available"]
    if not valid_root:
        status = "blocked"
    elif optional_missing:
        status = "degraded"
    else:
        status = "ok"

    report = {
        "agent_id": args.agent_id,
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "orbitos_path": str(root),
        "root_valid": valid_root,
        "python": python_info,
        "node": node_info,
        "git": git_info,
        "pwsh": pwsh_info,
        "validation_command": "python .orbitos/scripts/run-validation.py",
        "status": status,
    }

    report_dir = root / ".orbitos" / "state" / "env"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{args.agent_id}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
