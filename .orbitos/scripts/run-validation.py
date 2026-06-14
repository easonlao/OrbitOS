import json
import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]


def read_json_like(relative_path):
    with (ROOT / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def has_own(value, key):
    return isinstance(value, dict) and key in value


def allowed_types(schema):
    if "type" not in schema:
        return []
    schema_type = schema["type"]
    return schema_type if isinstance(schema_type, list) else [schema_type]


def test_type(value, types):
    if not types:
        return True
    for schema_type in types:
        if schema_type == "null" and value is None:
            return True
        if schema_type == "array" and isinstance(value, list):
            return True
        if schema_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if schema_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if schema_type == "object" and isinstance(value, dict):
            return True
        if schema_type == "string" and isinstance(value, str):
            return True
        if schema_type == "boolean" and isinstance(value, bool):
            return True
    return False


def add_error(errors, path_text, message):
    errors.append({"path": path_text, "message": message})


def validate_value(value, schema, path_text, errors):
    types = allowed_types(schema)
    if not test_type(value, types):
        add_error(errors, path_text, f"type mismatch; expected {'|'.join(types)}")
        return

    if "enum" in schema and value not in schema["enum"]:
        add_error(errors, path_text, "value is not in enum")

    if "object" in types and isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name in required:
            if name not in value:
                add_error(errors, f"{path_text}.{name}", "missing required field")

        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    add_error(errors, f"{path_text}.{name}", "additional property is not allowed")

        for name, prop_schema in properties.items():
            if name in value:
                validate_value(value[name], prop_schema, f"{path_text}.{name}", errors)

    if "array" in types and isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_value(item, schema["items"], f"{path_text}[{index}]", errors)


def validate_lifecycle(value, errors):
    from_status = value.get("previous_status") or ""
    to_status = value.get("status")
    pair = f"{from_status}|{to_status}"
    allowed_pairs = {
        "|raw",
        "raw|triaged",
        "triaged|confirmed",
        "confirmed|processed",
        "processed|archived",
        "raw|archived",
    }
    if pair not in allowed_pairs:
        add_error(errors, "$.status", f"illegal lifecycle transition: {from_status or None} -> {to_status}")


INTERNAL_WIKILINK_PATTERN = re.compile(r"\[\[[^\]]*(?:^|/|\\|\.\.)\.orbitos(?:/|\\)[^\]]*\]\]")


def markdown_internal_wikilink_errors(full_path):
    content = full_path.read_text(encoding="utf-8")
    errors = []
    for match in INTERNAL_WIKILINK_PATTERN.finditer(content):
        line = content[: match.start()].count("\n") + 1
        add_error(errors, f"line {line}", "Obsidian wikilink must not point to .orbitos/")
    return errors


def walk_markdown(full_path):
    if not full_path.exists():
        return []
    if full_path.is_dir():
        return [path for path in full_path.rglob("*.md") if path.is_file()]
    return [full_path] if full_path.suffix == ".md" else []


SCHEMAS = {
    "event": read_json_like(".orbitos/schemas/event.schema.yaml"),
    "inbox-triage": read_json_like(".orbitos/schemas/inbox-triage.schema.yaml"),
    "ingest-batch": read_json_like(".orbitos/schemas/ingest-batch.schema.yaml"),
    "lifecycle": read_json_like(".orbitos/schemas/lifecycle.schema.yaml"),
    "core-change": read_json_like(".orbitos/schemas/core-change.schema.yaml"),
    "agent-registry": read_json_like(".orbitos/schemas/agent-registry.schema.yaml"),
}

failure_count = 0
case_count = 0


def print_case(name, expected_valid, errors):
    global failure_count
    actual_valid = len(errors) == 0
    if actual_valid != expected_valid:
        failure_count += 1
    status = "PASS" if actual_valid == expected_valid else "FAIL"
    print(f"{status} {name}")
    for error in errors:
        print(f"  - {error['path']}: {error['message']}")


def schema_name_for_case(name):
    if name.startswith("ingest-batch."):
        return "ingest-batch"
    if name.startswith("inbox-triage."):
        return "inbox-triage"
    if name.startswith("agent-registry."):
        return "agent-registry"
    if name.startswith("core-change."):
        return "core-change"
    if name.startswith("event."):
        return "event"
    if name.startswith("lifecycle."):
        return "lifecycle"
    raise ValueError(f"Cannot infer schema for case: {name}")


case_root = ROOT / ".orbitos/evals/cases"
for case_path in sorted(case_root.glob("*.yaml")):
    case_count += 1
    schema_name = schema_name_for_case(case_path.name)
    data = read_json_like(f".orbitos/evals/cases/{case_path.name}")
    errors = []
    validate_value(data, SCHEMAS[schema_name], "$", errors)
    if schema_name == "lifecycle":
        validate_lifecycle(data, errors)
    print_case(case_path.name, ".valid." in case_path.name, errors)


markdown_case_root = ROOT / ".orbitos/evals/markdown-link-boundary"
for case_path in sorted(markdown_case_root.glob("*.md")):
    case_count += 1
    errors = markdown_internal_wikilink_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


case_count += 1
visible_files = [
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "README.zh-CN.md",
    *walk_markdown(ROOT / "00-系统"),
    *walk_markdown(ROOT / "02-时间线"),
]
visible_errors = []
for file_path in visible_files:
    for error in markdown_internal_wikilink_errors(file_path):
        add_error(
            visible_errors,
            f"{file_path.relative_to(ROOT)} {error['path']}",
            error["message"],
        )
print_case("visible-markdown.no-internal-wikilinks", True, visible_errors)


case_count += 1
registry_errors = []
validate_value(read_json_like(".orbitos/agents/registry.yaml"), SCHEMAS["agent-registry"], "$", registry_errors)
print_case("actual.agent-registry", True, registry_errors)


case_count += 1
ingest_errors = []
ingest_dir = ROOT / ".orbitos/ingest/batches"
ingested_dir = ROOT / "01-收件箱/已入库"
recorded_files = set()
if ingest_dir.exists():
    for batch_path in sorted(ingest_dir.glob("*.yaml")):
        batch = read_json_like(f".orbitos/ingest/batches/{batch_path.name}")
        validate_value(batch, SCHEMAS["ingest-batch"], f"$[{batch_path.name}]", ingest_errors)
        if isinstance(batch.get("items"), list):
            for item in batch["items"]:
                file_name = item.get("file") if isinstance(item, dict) else None
                if isinstance(file_name, str):
                    recorded_files.add(file_name)
                    stored_path = ingested_dir / file_name
                    if not stored_path.exists():
                        add_error(
                            ingest_errors,
                            f".orbitos/ingest/batches/{batch_path.name}:{file_name}",
                            "batch item file does not exist in 01-收件箱/已入库/",
                        )

if ingested_dir.exists():
    for file_path in ingested_dir.iterdir():
        if file_path.is_file() and file_path.name not in recorded_files:
            add_error(
                ingest_errors,
                f"01-收件箱/已入库/{file_path.name}",
                "ingested file is missing an ingest batch record",
            )
print_case("actual.ingest-batches", True, ingest_errors)


if failure_count > 0:
    print("")
    print(f"Validation eval failed: {failure_count} case(s).")
    sys.exit(1)

print("")
print(f"Validation eval passed: {case_count} case(s).")
