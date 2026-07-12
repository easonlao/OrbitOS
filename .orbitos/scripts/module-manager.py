import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / ".orbitos/module-catalog.json"
STATE_PATH = ROOT / ".orbitos/state/modules.json"
LIVE_MODULES_ROOT = ROOT / ".orbitos/modules"


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_catalog():
    return read_json(CATALOG_PATH)["modules"]


def load_state():
    if not STATE_PATH.exists():
        return {"version": 1, "modules": {}}
    return read_json(STATE_PATH)


def module_entry(catalog, module_id):
    if module_id not in catalog:
        available = ", ".join(sorted(catalog))
        raise ValueError(f"unknown module '{module_id}'; available: {available}")
    return catalog[module_id]


def package_path(entry):
    return ROOT / entry["package_path"]


def copy_missing_tree(source, target):
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def install(module_id):
    catalog = load_catalog()
    entry = module_entry(catalog, module_id)
    source = package_path(entry)
    if not source.is_dir():
        raise ValueError(f"module package is unavailable: {entry['package_path']}")

    destination = LIVE_MODULES_ROOT / module_id
    if destination.exists():
        raise ValueError(f"module files already exist: .orbitos/modules/{module_id}")
    copy_missing_tree(source, destination)

    state = load_state()
    state["modules"][module_id] = {"state": "installed_disabled"}
    write_json(STATE_PATH, state)
    print(f"installed: {module_id}")


def enable(module_id):
    catalog = load_catalog()
    entry = module_entry(catalog, module_id)
    state = load_state()
    record = state["modules"].get(module_id)
    if not record or record["state"] not in {"installed_disabled", "disabled"}:
        raise ValueError(f"module '{module_id}' must be installed and disabled before enable")
    if not (LIVE_MODULES_ROOT / module_id).is_dir():
        raise ValueError(f"module files are missing: .orbitos/modules/{module_id}")

    for relative_path in entry.get("visible_paths", []):
        (ROOT / relative_path).mkdir(parents=True, exist_ok=True)

    templates = LIVE_MODULES_ROOT / module_id / "templates"
    if templates.is_dir():
        copy_missing_tree(templates, ROOT)

    record["state"] = "ready" if entry["readiness"] == "immediate" else "enabled_unconfigured"
    record.pop("blockers", None)
    state["modules"][module_id] = record
    write_json(STATE_PATH, state)
    print(f"enabled: {module_id} ({record['state']})")


def configure(module_id, note):
    catalog = load_catalog()
    entry = module_entry(catalog, module_id)
    state = load_state()
    record = state["modules"].get(module_id)
    if not record or record["state"] not in {"enabled_unconfigured", "blocked"}:
        raise ValueError(f"module '{module_id}' must be enabled and unconfigured or blocked before configure")
    if entry["readiness"] == "persona_source" and not (ROOT / "00-系统/09-人物档案.md").is_file():
        raise ValueError("persona requires 00-系统/09-人物档案.md before it can become ready")
    record["state"] = "ready"
    record["configured_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    record.pop("blockers", None)
    state["modules"][module_id] = record
    write_json(STATE_PATH, state)
    print(f"configured: {module_id}: {note}")


def disable(module_id):
    catalog = load_catalog()
    module_entry(catalog, module_id)
    state = load_state()
    record = state["modules"].get(module_id)
    if not record:
        raise ValueError(f"module '{module_id}' is not installed")
    record["state"] = "disabled"
    record.pop("blockers", None)
    state["modules"][module_id] = record
    write_json(STATE_PATH, state)
    print(f"disabled: {module_id}; user data was preserved")


def status():
    catalog = load_catalog()
    state = load_state()["modules"]
    for module_id in sorted(catalog):
        record = state.get(module_id)
        module_state = record["state"] if record else "available"
        print(f"{module_id}: {module_state}")


def main():
    parser = argparse.ArgumentParser(description="Install and manage optional OrbitOS modules.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "enable", "disable"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("module_id")
    configure_parser = subparsers.add_parser("configure")
    configure_parser.add_argument("module_id")
    configure_parser.add_argument("--note", required=True)
    subparsers.add_parser("status")
    args = parser.parse_args()

    try:
        if args.command == "install":
            install(args.module_id)
        elif args.command == "enable":
            enable(args.module_id)
        elif args.command == "configure":
            configure(args.module_id, args.note)
        elif args.command == "disable":
            disable(args.module_id)
        else:
            status()
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
