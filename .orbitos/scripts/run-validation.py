import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_doc_consistency import (
    check_broken_wikilinks,
    check_forbidden_statements,
    check_legacy_paths,
    find_visible_markdown,
    resolve_wikilink_target,
)


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

    if "maxItems" in schema and isinstance(value, list) and len(value) > schema["maxItems"]:
        add_error(errors, path_text, f"array exceeds maxItems={schema['maxItems']}")

    if "string" in types and isinstance(value, str) and "pattern" in schema:
        if not re.match(schema["pattern"], value):
            add_error(errors, path_text, "value does not match pattern")

    if "object" in types and isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name in required:
            if name not in value:
                add_error(errors, f"{path_text}.{name}", "missing required field")

        additional_properties = schema.get("additionalProperties", True)
        if additional_properties is False:
            for name in value:
                if name not in properties:
                    add_error(errors, f"{path_text}.{name}", "additional property is not allowed")

        for name, prop_schema in properties.items():
            if name in value:
                validate_value(value[name], prop_schema, f"{path_text}.{name}", errors)

        if isinstance(additional_properties, dict):
            for name, item in value.items():
                if name not in properties:
                    validate_value(item, additional_properties, f"{path_text}.{name}", errors)

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


def validate_knowledge_event(value, errors, path_text="$" ):
    if not isinstance(value, dict) or value.get("event_type") != "knowledge_use":
        return
    knowledge = value.get("knowledge")
    if not isinstance(knowledge, dict):
        add_error(errors, f"{path_text}.knowledge", "knowledge_use requires a knowledge object")
        return
    sources = knowledge.get("sources", [])
    input_refs = [
        item.get("ref")
        for item in value.get("inputs", [])
        if isinstance(item, dict) and item.get("kind") == "file"
    ]
    if sources != input_refs:
        add_error(errors, f"{path_text}.knowledge.sources", "knowledge sources must match file input refs in order")
    if knowledge.get("fit") == "no_match" and sources:
        add_error(errors, f"{path_text}.knowledge.sources", "no_match knowledge_use must not list sources")
    if knowledge.get("fit") != "no_match" and not sources:
        add_error(errors, f"{path_text}.knowledge.sources", "non-no_match knowledge_use requires 1-3 sources")
    route = knowledge.get("feedback_route")
    feedback_ref = knowledge.get("feedback_ref")
    if route == "none" and feedback_ref is not None:
        add_error(errors, f"{path_text}.knowledge.feedback_ref", "feedback route none must not have feedback_ref")
    if route != "none" and not feedback_ref:
        add_error(errors, f"{path_text}.knowledge.feedback_ref", "non-none feedback route requires feedback_ref")


def knowledge_flow_errors():
    errors = []
    required_terms = {
        ".orbitos/workflows/knowledge-flow.md": ["默认分流", "批量确认", "1—3", "适用性", "knowledge_use", "反馈"],
        ".orbitos/rules/core/knowledge-use.md": ["已有知识", "当前事实", "本次推断", "适用性检查", "不自动升级"],
        ".orbitos/workflows/inbox-triage.md": ["确认批次", "默认分流优先级", "MAP 同步"],
        ".orbitos/workflows/inbox-ingest.md": ["批次清单", "不对同一批次内的每个文件重复询问"],
        ".orbitos/workflows/knowledge-draft.md": ["不重复询问同一授权"],
        "AGENTS.md": ["知识流转与调用", "knowledge-use.md"],
        "00-系统/02-日常协作.md": ["已有依据", "当前事实", "本次推断"],
        "00-系统/03-内容生命周期.md": ["默认分流", "批量确认", "使用反馈回写", "适用"],
    }
    for relative_path, terms in required_terms.items():
        full_path = ROOT / relative_path
        if not full_path.is_file():
            add_error(errors, relative_path, "knowledge flow asset is missing")
            continue
        content = full_path.read_text(encoding="utf-8")
        for term in terms:
            if term not in content:
                add_error(errors, relative_path, f"knowledge flow asset is missing required term: {term}")

    knowledge_root = ROOT / "04-知识"
    map_path = knowledge_root / "MAP.md"
    if knowledge_root.is_dir() and not map_path.is_file():
        add_error(errors, "04-知识/MAP.md", "knowledge directory requires a MAP.md index")
    if knowledge_root.is_dir() and map_path.is_file():
        map_text = map_path.read_text(encoding="utf-8")
        mapped = set()
        for match in WIKILINK_TARGET_PATTERN.finditer(map_text):
            target = match.group(1).replace("\\", "/")
            if target.startswith("04-知识/"):
                target = target[len("04-知识/"):]
            if not target.endswith(".md"):
                target += ".md"
            mapped.add(target)
            target_path = knowledge_root / target
            if not target_path.is_file():
                add_error(errors, f"04-知识/MAP.md:{target}", "MAP target does not exist")
        for file_path in sorted(knowledge_root.rglob("*.md")):
            if file_path == map_path or markdown_lifecycle(file_path) != "active":
                continue
            relative = file_path.relative_to(knowledge_root).as_posix()
            if relative not in mapped:
                add_error(errors, f"04-知识/{relative}", "knowledge file is missing from MAP.md")
    return errors


INTERNAL_WIKILINK_PATTERN = re.compile(r"\[\[[^\]]*(?:^|/|\\|\.\.)\.orbitos(?:/|\\)[^\]]*\]\]")
WIKILINK_TARGET_PATTERN = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")
SOURCE_HEADING_PATTERN = re.compile(r"^##\s*(?:来源|Source)\s*$", re.IGNORECASE)
SOURCE_LINK_PATTERN = re.compile(r"\[\[[^\]]+\]\]|\[[^\]]+\]\([^)]+\)")
DRAFT_LIFECYCLE_PATTERN = re.compile(r"^lifecycle:\s*draft\s*$", re.IGNORECASE | re.MULTILINE)
ACTIVE_LIFECYCLE_PATTERN = re.compile(r"^lifecycle:\s*active\s*$", re.IGNORECASE | re.MULTILINE)


def markdown_internal_wikilink_errors(full_path):
    content = full_path.read_text(encoding="utf-8")
    errors = []
    for match in INTERNAL_WIKILINK_PATTERN.finditer(content):
        line = content[: match.start()].count("\n") + 1
        add_error(errors, f"line {line}", "Obsidian wikilink must not point to .orbitos/")
    return errors


def knowledge_source_errors(full_path):
    if not full_path.is_file():
        return []
    if full_path.name == "MAP.md":
        return []

    content = full_path.read_text(encoding="utf-8")
    lines = []
    in_code_block = False
    for line_num, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            lines.append((line_num, line))

    source_start = None
    for index, (_line_num, line) in enumerate(lines):
        if SOURCE_HEADING_PATTERN.match(line.strip()):
            source_start = index
            break

    errors = []
    rel = full_path.relative_to(ROOT)
    if source_start is None:
        add_error(errors, str(rel), "knowledge file is missing a 来源 section")
        return errors

    source_lines = []
    for line_num, line in lines[source_start + 1:]:
        if line.strip().startswith("## "):
            break
        source_lines.append((line_num, line))

    source_text = "\n".join(line for _line_num, line in source_lines)
    if not SOURCE_LINK_PATTERN.search(source_text):
        add_error(errors, str(rel), "knowledge 来源 section must contain at least one traceable link")

    if markdown_lifecycle(full_path) == "active":
        inbox_root = (ROOT / "01-收件箱").resolve()
        ingested_root = (ROOT / "01-收件箱/已入库").resolve()
        for match in WIKILINK_TARGET_PATTERN.finditer(source_text):
            raw_target = match.group(1).replace("\\", "/")
            if raw_target.startswith("01-收件箱/"):
                target = (ROOT / raw_target).resolve()
            else:
                target = (full_path.parent / raw_target).resolve()
            try:
                target.relative_to(inbox_root)
            except ValueError:
                continue
            try:
                target.relative_to(ingested_root)
            except ValueError:
                add_error(
                    errors,
                    str(rel),
                    "active knowledge must not cite raw inbox files outside 01-收件箱/已入库/",
                )
                break

    return errors


def source_targets(full_path):
    if not full_path.is_file():
        return set()
    content = full_path.read_text(encoding="utf-8")
    lines = []
    in_code_block = False
    for _line_num, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            lines.append(line)

    source_start = None
    for index, line in enumerate(lines):
        if SOURCE_HEADING_PATTERN.match(line.strip()):
            source_start = index
            break
    if source_start is None:
        return set()

    targets = set()
    for line in lines[source_start + 1:]:
        if line.strip().startswith("## "):
            break
        for match in WIKILINK_TARGET_PATTERN.finditer(line):
            resolved = resolve_wikilink_target(full_path, match.group(1), ROOT)
            if resolved is not None:
                targets.add(resolved.resolve())
    return targets


def is_knowledge_conflict_source(target):
    """Return whether a source target is evidence that can imply a knowledge conflict."""
    parts = target.resolve().parts
    return not any(
        parts[index : index + 2] == ("00-系统", "agents")
        for index in range(len(parts) - 1)
    )


def markdown_lifecycle(full_path):
    if not full_path.is_file():
        return None
    content = full_path.read_text(encoding="utf-8")
    if DRAFT_LIFECYCLE_PATTERN.search(content):
        return "draft"
    if ACTIVE_LIFECYCLE_PATTERN.search(content):
        return "active"
    return None


def is_markdown_linked_from(target_file, candidate_files):
    target_file = target_file.resolve()
    for candidate in candidate_files:
        if candidate.resolve() == target_file:
            continue
        if not candidate.is_file():
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        in_code_block = False
        for line in content.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for match in WIKILINK_TARGET_PATTERN.finditer(line):
                resolved = resolve_wikilink_target(candidate, match.group(1), ROOT)
                if resolved is not None and resolved.resolve() == target_file:
                    return True
    return False


def orphan_draft_errors(draft_files, projection_files):
    errors = []
    for draft in draft_files:
        if markdown_lifecycle(draft) != "draft":
            continue
        if not is_markdown_linked_from(draft, projection_files):
            add_error(
                errors,
                str(draft.relative_to(ROOT)),
                "draft knowledge file is not projected from a user-visible entry",
            )
    return errors


def omitted_conflict_errors(knowledge_files):
    errors = []
    active_files = [path for path in knowledge_files if markdown_lifecycle(path) == "active"]
    source_map = {}
    for file_path in active_files:
        for target in source_targets(file_path):
            if not is_knowledge_conflict_source(target):
                continue
            source_map.setdefault(target, []).append(file_path)
    for target, file_paths in sorted(source_map.items(), key=lambda item: str(item[0])):
        if len(file_paths) > 1:
            add_error(
                errors,
                str(target.relative_to(ROOT)),
                "same source is referenced by multiple active knowledge files; possible omitted conflict",
            )
    return errors


CAPTURE_KIND_PATTERN = re.compile(r"^capture_kind:\s*([a-z_]+)\s*$", re.IGNORECASE | re.MULTILINE)
PURPOSE_STATUS_PATTERN = re.compile(r"^purpose_status:\s*([a-z_]+)\s*$", re.IGNORECASE | re.MULTILINE)
EXIT_PATTERN = re.compile(r"^exit:\s*([a-z_]+)\s*$", re.IGNORECASE | re.MULTILINE)
CONFIRMED_BY_PATTERN = re.compile(r"^confirmed_by:\s*(\S+)\s*$", re.MULTILINE)
REFINED_TO_PATTERN = re.compile(r"^refined_to:\s*\S+\s*$", re.MULTILINE)
REPLACED_BY_PATTERN = re.compile(r"^replaced_by:\s*\S+\s*$", re.MULTILINE)
IRREVERSIBLE_EXITS = {"archive", "discard", "superseded"}
CHAOS_CAPTURE_KINDS = {"chaos", "dialog_purpose", "mixed"}


def frontmatter_value(content, pattern):
    match = pattern.search(content)
    return match.group(1).strip().lower() if match else None


def frontmatter_has(content, pattern):
    return pattern.search(content) is not None


def chaos_purpose_errors(full_path):
    if not full_path.is_file():
        return []
    content = full_path.read_text(encoding="utf-8")
    if frontmatter_value(content, CAPTURE_KIND_PATTERN) not in CHAOS_CAPTURE_KINDS:
        return []
    errors = []
    purpose_status = frontmatter_value(content, PURPOSE_STATUS_PATTERN)
    exit_value = frontmatter_value(content, EXIT_PATTERN)
    rel = full_path.relative_to(ROOT)
    if purpose_status == "unclear":
        if markdown_lifecycle(full_path) in {"draft", "active"}:
            add_error(errors, str(rel), "purpose-unclear chaos record must not be promoted to knowledge draft or active knowledge")
        if frontmatter_has(content, REFINED_TO_PATTERN):
            add_error(errors, str(rel), "purpose-unclear chaos record must not be refined to a knowledge draft")
    if exit_value in IRREVERSIBLE_EXITS and frontmatter_value(content, CONFIRMED_BY_PATTERN) != "user":
        add_error(errors, str(rel), f"exit {exit_value} requires confirmed_by user confirmation")
    if exit_value == "draft" and not frontmatter_has(content, REFINED_TO_PATTERN):
        add_error(errors, str(rel), "exit draft requires refined_to target")
    if exit_value == "superseded" and not frontmatter_has(content, REPLACED_BY_PATTERN):
        add_error(errors, str(rel), "exit superseded requires replaced_by target")
    return errors


DRAFT_GATE_SECTIONS = ["核心结论", "事实与依据", "因果链", "适用条件与边界", "复用方式", "来源", "不确定性"]
DRAFT_GATE_PATTERN = re.compile(r"^##\s*(核心结论|事实与依据|因果链|适用条件与边界|复用方式|来源|不确定性)\s*$", re.MULTILINE)


def knowledge_draft_gate_errors(full_path):
    if not full_path.is_file():
        return []
    content = full_path.read_text(encoding="utf-8")
    errors = []
    present = set(DRAFT_GATE_PATTERN.findall(content))
    missing = [section for section in DRAFT_GATE_SECTIONS if section not in present]
    if missing:
        add_error(
            errors,
            str(full_path.relative_to(ROOT)),
            "knowledge draft is missing refinement gates: " + ", ".join(missing),
        )
    return errors


def chaos_flow_errors():
    errors = []
    required_terms = {
        ".orbitos/workflows/chaos-capture.md": ["混沌记录", "讨论目的", "用户原话", "未定型思考", "purpose_status", "待铸卡", "退出", "knowledge-refinement.md"],
        ".orbitos/rules/core/knowledge-refinement.md": ["核心判断", "事实", "因果链", "适用条件", "复用方式", "来源", "不确定性"],
        ".orbitos/workflows/knowledge-flow.md": ["退出", "混沌", "待铸卡"],
        ".orbitos/workflows/inbox-triage.md": ["chaos_candidate", "待铸卡"],
        ".orbitos/rules/core/knowledge-use.md": ["chaos_record"],
        "AGENTS.md": ["chaos-capture.md", "knowledge-refinement.md"],
        "00-系统/02-日常协作.md": ["混沌", "待铸卡"],
        "00-系统/03-内容生命周期.md": ["混沌记录", "退出"],
    }
    for relative_path, terms in required_terms.items():
        full_path = ROOT / relative_path
        if not full_path.is_file():
            add_error(errors, relative_path, "chaos flow asset is missing")
            continue
        content = full_path.read_text(encoding="utf-8")
        for term in terms:
            if term not in content:
                add_error(errors, relative_path, f"chaos flow asset is missing required term: {term}")
    template = ROOT / ".orbitos/templates/01-收件箱/待铸卡/00-混沌记录模板.md"
    if not template.is_file():
        add_error(errors, ".orbitos/templates/01-收件箱/待铸卡/00-混沌记录模板.md", "chaos record template is missing")
    if (ROOT / "01-收件箱").is_dir() and not (ROOT / "01-收件箱/待铸卡").is_dir():
        add_error(errors, "01-收件箱/待铸卡", "pending-card zone is missing from the inbox")
    return errors


CLOSED_LOOP_STEPS = {"dialog_purpose", "chaos_capture", "draft", "knowledge_use", "exit"}
KNOWLEDGE_FIT_VALUES = {"applicable", "partially_applicable", "not_applicable", "no_match"}
FEEDBACK_ROUTE_VALUES = {"none", "experience", "project_lesson", "knowledge_draft", "knowledge_conflict", "chaos_record"}
EXIT_VALUES = {"keep_raw", "pending_card", "draft", "archive", "discard", "superseded"}


def closed_loop_scenario_errors(data, name):
    errors = []
    if not isinstance(data, dict) or data.get("scenario") != "closed_loop":
        add_error(errors, "$", "closed-loop scenario requires scenario=closed_loop")
        return errors
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        add_error(errors, "$.steps", "closed-loop scenario requires a non-empty steps list")
        return errors
    order = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            add_error(errors, f"$.steps[{index}]", "step must be an object")
            order.append(None)
            continue
        step_name = step.get("step")
        order.append(step_name)
        if step_name not in CLOSED_LOOP_STEPS:
            add_error(errors, f"$.steps[{index}].step", f"unknown closed-loop step: {step_name}")
    index_map = {}
    for index, step_name in enumerate(order):
        index_map.setdefault(step_name, index)
    if "dialog_purpose" in index_map and "draft" in index_map and index_map["dialog_purpose"] > index_map["draft"]:
        add_error(errors, "$.steps", "dialog_purpose must precede draft")
    if "chaos_capture" in index_map and "draft" in index_map and index_map["chaos_capture"] > index_map["draft"]:
        add_error(errors, "$.steps", "chaos_capture must precede draft")
    if "draft" in index_map and "knowledge_use" in index_map and index_map["draft"] > index_map["knowledge_use"]:
        add_error(errors, "$.steps", "draft must precede knowledge_use")
    if "exit" in index_map and index_map["exit"] != len(order) - 1:
        add_error(errors, "$.steps", "exit must be the final step")
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        step_name = step.get("step")
        if step_name == "dialog_purpose":
            if step.get("purpose_status") not in {"clear", "unclear", "pending"}:
                add_error(errors, f"$.steps[{index}].purpose_status", "invalid purpose_status")
        elif step_name == "draft":
            gates = step.get("gates")
            if gates not in {"complete", "incomplete"}:
                add_error(errors, f"$.steps[{index}].gates", "draft gates must be complete or incomplete")
            if gates == "complete":
                dialog = next((s for s in steps if isinstance(s, dict) and s.get("step") == "dialog_purpose"), None)
                if isinstance(dialog, dict) and dialog.get("purpose_status") == "unclear":
                    add_error(errors, f"$.steps[{index}]", "purpose-unclear content must not be forced into a knowledge draft")
        elif step_name == "knowledge_use":
            sources = step.get("sources")
            fit = step.get("fit")
            route = step.get("feedback_route")
            ref = step.get("feedback_ref")
            if not isinstance(sources, list):
                add_error(errors, f"$.steps[{index}].sources", "knowledge_use requires sources")
            elif fit == "no_match":
                if sources:
                    add_error(errors, f"$.steps[{index}].sources", "no_match knowledge_use must not list sources")
            elif not sources:
                add_error(errors, f"$.steps[{index}].sources", "non-no_match knowledge_use requires 1-3 sources")
            if fit not in KNOWLEDGE_FIT_VALUES:
                add_error(errors, f"$.steps[{index}].fit", "invalid knowledge fit")
            if route not in FEEDBACK_ROUTE_VALUES:
                add_error(errors, f"$.steps[{index}].feedback_route", "invalid feedback route")
            if route != "none" and not ref:
                add_error(errors, f"$.steps[{index}].feedback_ref", "non-none feedback route requires feedback_ref")
        elif step_name == "exit":
            exit_name = step.get("exit")
            if exit_name not in EXIT_VALUES:
                add_error(errors, f"$.steps[{index}].exit", "invalid exit")
            if exit_name in IRREVERSIBLE_EXITS and step.get("confirmed_by") != "user":
                add_error(errors, f"$.steps[{index}].confirmed_by", "irreversible exit requires confirmed_by user")
    return errors


QUEUE_ROLE_VALUES = {"coordinator", "researcher", "writer", "builder", "editor"}
QUEUE_STEP_VALUES = {"launch", "confirm", "advance", "replan", "close"}
QUEUE_TRIGGER_VALUES = {"unavailable", "scope", "failure"}


def collaboration_queue_scenario_errors(data, name):
    errors = []
    if not isinstance(data, dict) or data.get("scenario") != "collaboration_queue":
        add_error(errors, "$", "collaboration-queue scenario requires scenario=collaboration_queue")
        return errors
    queue = data.get("queue")
    if not isinstance(queue, list) or len(queue) < 2:
        add_error(errors, "$.queue", "queue requires at least two ordered stages")
        queue = []
    stage_ids = []
    for index, spec in enumerate(queue):
        if not isinstance(spec, dict) or not spec.get("stage_id") or not spec.get("tool") or spec.get("role") not in QUEUE_ROLE_VALUES:
            add_error(errors, f"$.queue[{index}]", "stage must declare stage_id, tool and a registered role")
            continue
        stage_ids.append(spec["stage_id"])
    if len(stage_ids) != len(set(stage_ids)):
        add_error(errors, "$.queue", "stage ids must be unique")
    chain = {}
    for spec in queue:
        if isinstance(spec, dict) and spec.get("stage_id"):
            chain[spec["stage_id"]] = spec.get("next_stage")
    for stage_id, next_stage in chain.items():
        if next_stage and next_stage not in chain:
            add_error(errors, f"$.queue:{stage_id}", "next_stage must point to a planned stage")
    for index, spec in enumerate(queue):
        if index < len(queue) - 1 and isinstance(spec, dict) and spec.get("next_stage") != queue[index + 1].get("stage_id"):
            add_error(errors, f"$.queue:{spec.get('stage_id')}", "stage chain must be ordered")
    tools = {spec.get("role"): spec.get("tool") for spec in queue if isinstance(spec, dict)}
    if tools.get("builder") and tools.get("editor") and tools["builder"] == tools["editor"]:
        add_error(errors, "$.queue", "Editor tool identity must differ from the Builder tool identity")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        add_error(errors, "$.steps", "scenario requires a non-empty steps list")
        return errors
    return_owner = data.get("return_owner")
    tool_by_stage = {spec.get("stage_id"): spec.get("tool") for spec in queue if isinstance(spec, dict)}
    state = {
        "plan_status": "none",
        "plan_revision": 0,
        "current_stage": None,
        "current_owner": None,
        "stage_order": [],
        "stages": {stage_id: {"status": "pending", "failures": 0} for stage_id in stage_ids},
        "pending_replan": False,
        "closed": False,
    }

    def stage_record(record, index):
        if record is None:
            return
        if record.get("stage_id") != state["current_stage"]:
            add_error(errors, f"$.steps[{index}]", f"only the current stage can advance: {state['current_stage']}")
            return
        if record.get("by") != state["current_owner"]:
            add_error(errors, f"$.steps[{index}]", f"only the current owner can advance: {state['current_owner']}")
            return
        stage = state["stages"].setdefault(record["stage_id"], {"status": "pending", "failures": 0})
        if stage["status"] == "complete":
            add_error(errors, f"$.steps[{index}]", "a completed stage cannot advance again")
            return
        if stage["failures"] >= 2:
            add_error(errors, f"$.steps[{index}]", "a stage that failed twice requires a user-confirmed re-plan")
            return
        if record.get("outcome") == "blocked":
            stage["failures"] += 1
            stage["status"] = "blocked"
            state["current_owner"] = record.get("by")
            return
        stage["status"] = "complete"
        next_stage = chain.get(record["stage_id"])
        if next_stage:
            state["current_stage"] = next_stage
            state["current_owner"] = tool_by_stage.get(next_stage)
        else:
            state["current_stage"] = record["stage_id"]
            state["current_owner"] = return_owner

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            add_error(errors, f"$.steps[{index}]", "step must be an object")
            continue
        step_name = step.get("step")
        actor = step.get("by")
        if step_name not in QUEUE_STEP_VALUES:
            add_error(errors, f"$.steps[{index}].step", f"unknown collaboration-queue step: {step_name}")
            continue
        if step_name == "launch":
            if index != 0:
                add_error(errors, f"$.steps[{index}]", "launch must be the first step")
            state["plan_status"] = "proposed"
            state["plan_revision"] = 0
            state["stage_order"] = list(stage_ids)
            state["current_stage"] = stage_ids[0] if stage_ids else None
            state["current_owner"] = tool_by_stage.get(stage_ids[0]) if stage_ids else None
        elif step_name == "confirm":
            if state["plan_status"] != "proposed":
                add_error(errors, f"$.steps[{index}]", "confirm requires a proposed plan")
            if step.get("plan_revision", state["plan_revision"]) != state["plan_revision"]:
                add_error(errors, f"$.steps[{index}]", "stale plan revision on confirm")
            state["plan_status"] = "confirmed"
            state["pending_replan"] = False
            order = state["stage_order"]
            current = next((stage_id for stage_id in order if state["stages"][stage_id]["status"] != "complete"), order[0] if order else None)
            state["current_stage"] = current
            state["current_owner"] = tool_by_stage.get(current)
        elif step_name == "advance":
            if state["plan_status"] != "confirmed":
                add_error(errors, f"$.steps[{index}]", "advance requires a user-confirmed plan")
            if state["pending_replan"]:
                add_error(errors, f"$.steps[{index}]", "advance is blocked while a re-plan waits for confirmation")
            stage_record(step, index)
        elif step_name == "replan":
            if actor != state["current_owner"]:
                add_error(errors, f"$.steps[{index}]", f"only the current owner can re-plan: {state['current_owner']}")
            if state["pending_replan"]:
                add_error(errors, f"$.steps[{index}]", "a previous re-plan is still waiting for confirmation")
            if step.get("trigger") not in QUEUE_TRIGGER_VALUES:
                add_error(errors, f"$.steps[{index}].trigger", "invalid re-plan trigger")
            if step.get("trigger") == "failure":
                affected = state["stages"].get(step.get("affected_stage")) or {}
                if affected.get("failures", 0) < 1:
                    add_error(errors, f"$.steps[{index}]", "failure trigger requires a stage that already failed once")
            revised = step.get("revised_queue")
            if isinstance(revised, list) and len(revised) >= 2:
                completed = [sid for sid, s in state["stages"].items() if s["status"] == "complete"]
                if len(revised) < len(completed):
                    add_error(errors, f"$.steps[{index}].revised_queue", "revised queue must keep completed stages")
                else:
                    for pos, stage_id in enumerate(completed):
                        new_spec = revised[pos]
                        old = state["stages"][stage_id]
                        if not isinstance(new_spec, dict) or new_spec.get("stage_id") != stage_id:
                            add_error(errors, f"$.steps[{index}].revised_queue", "revised queue must keep completed stages in place")
                            break
                        if new_spec.get("tool") != tool_by_stage.get(stage_id) or new_spec.get("next_stage") != chain.get(stage_id):
                            add_error(errors, f"$.steps[{index}].revised_queue", "revised queue must keep completed stages unmodified")
                            break
                new_order = [spec.get("stage_id") for spec in revised if isinstance(spec, dict)]
                state["stage_order"] = new_order
                for stage_id in new_order:
                    state["stages"].setdefault(stage_id, {"status": "pending", "failures": 0})
                for spec in revised:
                    if isinstance(spec, dict) and spec.get("stage_id"):
                        tool_by_stage[spec["stage_id"]] = spec.get("tool")
                        chain[spec["stage_id"]] = spec.get("next_stage")
            elif step.get("replacement_tool"):
                replacement = step.get("replacement_tool")
                affected = step.get("affected_stage")
                if affected in state["stages"]:
                    state["stages"][affected] = {"status": "pending", "failures": 0}
                    tool_by_stage[affected] = replacement
                    if state["current_stage"] == affected:
                        state["current_owner"] = replacement
            state["plan_revision"] += 1
            state["plan_status"] = "proposed"
            state["pending_replan"] = True
        elif step_name == "close":
            if state["closed"]:
                add_error(errors, f"$.steps[{index}]", "close can only happen once")
            if actor != return_owner:
                add_error(errors, f"$.steps[{index}]", "only the return owner can close the handoff")
            if tools.get("builder") == actor or tools.get("editor") == actor:
                add_error(errors, f"$.steps[{index}]", "the Builder or Editor cannot close the whole handoff")
            incomplete = [stage_id for stage_id, s in state["stages"].items() if s["status"] != "complete"]
            if incomplete:
                add_error(errors, f"$.steps[{index}]", f"close requires all stages complete; pending: {incomplete}")
            if state["pending_replan"]:
                add_error(errors, f"$.steps[{index}]", "close is blocked while a re-plan waits for confirmation")
            if index != len(steps) - 1:
                add_error(errors, f"$.steps[{index}]", "close must be the final step")
            state["closed"] = True
    return errors


def collaboration_queue_asset_errors():
    errors = []
    required_paths = [
        ROOT / ".orbitos/schemas/handoff-queue.schema.yaml",
        ROOT / ".orbitos/templates/.orbitos/state/handoff-queues.json",
        ROOT / ".orbitos/scripts/handoff-queue.py",
    ]
    for path in required_paths:
        if not path.is_file():
            add_error(errors, str(path.relative_to(ROOT)), "collaboration queue asset is missing")

    template_path = ROOT / ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md"
    if template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
        for term in ["plan_status:", "plan_revision:", "current_stage:", "## 队列计划（可选）"]:
            if term not in template:
                add_error(errors, ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md", f"handoff template is missing queue field: {term}")

    workflow_path = ROOT / ".orbitos/module-packages/collaboration/workflows/agent-handoff.md"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        for term in ["launch", "阶段队列", "plan_revision", "current_stage", "advance", "re-plan", "return_owner"]:
            if term not in workflow:
                add_error(errors, str(workflow_path.relative_to(ROOT)), f"handoff workflow is missing queue term: {term}")

    pickup_path = ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md"
    if pickup_path.is_file():
        pickup = pickup_path.read_text(encoding="utf-8")
        for term in ["current_stage", "current_owner", "获取交接工作"]:
            if term not in pickup:
                add_error(errors, str(pickup_path.relative_to(ROOT)), f"handoff pickup is missing queue term: {term}")

    rule_path = ROOT / ".orbitos/module-packages/collaboration/rules/collaboration-governance.md"
    if rule_path.is_file():
        rule = rule_path.read_text(encoding="utf-8")
        for term in ["return_owner", "plan_revision", "不可变", "当前负责人"]:
            if term not in rule:
                add_error(errors, str(rule_path.relative_to(ROOT)), f"collaboration governance rule is missing queue term: {term}")

    guide_path = ROOT / "00-系统/07-Agent协作.md"
    if guide_path.is_file():
        guide = guide_path.read_text(encoding="utf-8")
        for term in ["确认", "阶段队列", "获取交接工作", "验收"]:
            if term not in guide:
                add_error(errors, "00-系统/07-Agent协作.md", f"agent collaboration guide is missing queue term: {term}")

    script_path = ROOT / ".orbitos/scripts/handoff-queue.py"
    if script_path.is_file():
        script = script_path.read_text(encoding="utf-8")
        for term in ["def launch", "def confirm", "def advance", "def replan", "def mark_close", "stage_order", "replans"]:
            if term not in script:
                add_error(errors, str(script_path.relative_to(ROOT)), f"handoff queue script is missing required term: {term}")

    if (ROOT / ".orbitos/templates/.orbitos/state/handoff-queues.json").is_file():
        validate_value(
            read_json_like(".orbitos/templates/.orbitos/state/handoff-queues.json"),
            SCHEMAS["handoff-queue"],
            "$",
            errors,
        )
    return errors


def collaboration_queue_state_errors():
    errors = []
    state_path = ROOT / ".orbitos/state/handoff-queues.json"
    if not state_path.is_file():
        return errors
    state = read_json_like(".orbitos/state/handoff-queues.json")
    validate_value(state, SCHEMAS["handoff-queue"], "$", errors)
    queues = state.get("queues", {})
    if not isinstance(queues, dict):
        return errors
    active_root = ROOT / "00-" + chr(0x7CFB) + chr(0x7EDF) / "agents/handoff"
    for relative, queue in queues.items():
        if not isinstance(queue, dict):
            continue
        handoff_path = ROOT / relative
        if not handoff_path.is_file():
            add_error(errors, f".orbitos/state/handoff-queues.json:{relative}", "queue handoff file does not exist")
        if queue.get("close") and not (ROOT / str(queue["close"].get("archived_ref", ""))).is_file():
            add_error(errors, f".orbitos/state/handoff-queues.json:{relative}", "closed queue must reference an archived handoff")
        if handoff_path.is_file():
            text = handoff_path.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            metadata = dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", parts[1] if len(parts) >= 3 else "", re.MULTILINE))
            if queue.get("current_owner") and metadata.get("current_owner") != queue["current_owner"]:
                add_error(errors, f".orbitos/state/handoff-queues.json:{relative}", "queue current_owner must match the handoff frontmatter")
            if queue.get("plan_status") != "none" and metadata.get("plan_status") != queue.get("plan_status"):
                add_error(errors, f".orbitos/state/handoff-queues.json:{relative}", "queue plan_status must match the handoff frontmatter")
            if metadata.get("handoff_status") == "closed" and not queue.get("close"):
                add_error(errors, f".orbitos/state/handoff-queues.json:{relative}", "closed queued handoff must record acceptance in the projection")
    return errors


def handoff_structure_errors():
    errors = []
    required_paths = [
        ROOT / "00-系统/agents/BOARD.md",
        ROOT / ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/agent-handoff.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md",
        ROOT / ".orbitos/scripts/handoff-status.py",
        ROOT / ".orbitos/scripts/handoff-control.py",
        ROOT / "00-系统/agents/handoff/archive/.gitkeep",
    ]
    for path in required_paths:
        if not path.is_file():
            add_error(errors, str(path.relative_to(ROOT)), "handoff structure file is missing")

    board_path = ROOT / "00-系统/agents/BOARD.md"
    if board_path.is_file():
        board = board_path.read_text(encoding="utf-8")
        for term in ["Agent 交接板", "不记录用户确认事项", "不记录项目总状态", "当前交接", "handoff/archive/", "handoff/"]:
            if term not in board:
                add_error(errors, "00-系统/agents/BOARD.md", f"handoff board is missing required term: {term}")

    template_path = ROOT / ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md"
    if template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
        for term in [
            "handoff_status:",
            "current_owner:",
            "return_owner:",
            "next_action:",
            "governance_required:",
            "collaboration_session_id:",
            "## 任务",
            "## 当前阶段",
            "## 交给谁",
            "## 已完成",
            "## 未完成",
            "## 风险与阻塞",
            "## 审核结论",
            "## 接手方异议",
            "## 需要继续做什么",
            "## Suggested skills",
            "## 最后确认",
        ]:
            if term not in template:
                add_error(errors, ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md", f"handoff template is missing required term: {term}")

    workflow_path = ROOT / ".orbitos/module-packages/collaboration/workflows/agent-handoff.md"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        for term in ["execution_mode=delegated", "handoff_status", "current_owner", "closed", "STATUS.md", "validation", "handoff-control.py begin", "handoff-control.py close"]:
            if term not in workflow:
                add_error(errors, str(workflow_path.relative_to(ROOT)), f"handoff workflow is missing required term: {term}")

    pickup_path = ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md"
    if pickup_path.is_file():
        pickup = pickup_path.read_text(encoding="utf-8")
        for term in ["获取交接工作", "00-系统/agents/BOARD.md", "current_owner", "next_action", "不得要求用户提供路径"]:
            if term not in pickup:
                add_error(errors, str(pickup_path.relative_to(ROOT)), f"handoff pickup workflow is missing required term: {term}")

    adapter_path = ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md"
    if adapter_path.is_file():
        adapter = adapter_path.read_text(encoding="utf-8")
        for term in ["$handoff", "操作系统临时目录", "agent-handoff.md", "handoff-pickup.md", "不得扫描系统临时目录"]:
            if term not in adapter:
                add_error(errors, str(adapter_path.relative_to(ROOT)), f"handoff adapter is missing required term: {term}")

    root_agent_path = ROOT / "AGENTS.md"
    if root_agent_path.is_file():
        root_agent = root_agent_path.read_text(encoding="utf-8")
        for term in [
            "交给另一位 Agent 继续",
            "$handoff",
            ".orbitos/modules/collaboration/workflows/handoff-adapter.md",
            "获取交接工作",
            ".orbitos/modules/collaboration/workflows/handoff-pickup.md",
        ]:
            if term not in root_agent:
                add_error(errors, "AGENTS.md", f"handoff route is missing required term: {term}")

    active_root = ROOT / "00-系统/agents/handoff"
    archive_root = active_root / "archive"
    open_statuses = {"delegated", "working", "returned"}
    active_names = set()
    for path in sorted(active_root.glob("*.md")) if active_root.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        metadata = dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", parts[1] if len(parts) >= 3 else "", re.MULTILINE))
        active_names.add(path.stem)
        if metadata.get("handoff_status") not in open_statuses:
            add_error(errors, str(path.relative_to(ROOT)), "active handoff must use delegated, working, or returned status")
        if not metadata.get("current_owner"):
            add_error(errors, str(path.relative_to(ROOT)), "active handoff is missing current_owner")
        if not metadata.get("return_owner"):
            add_error(errors, str(path.relative_to(ROOT)), "active handoff is missing return_owner")
        if not metadata.get("next_action"):
            add_error(errors, str(path.relative_to(ROOT)), "active handoff is missing next_action")
    for path in sorted(archive_root.glob("*.md")) if archive_root.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        metadata = dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", parts[1] if len(parts) >= 3 else "", re.MULTILINE))
        if metadata.get("handoff_status") != "closed":
            add_error(errors, str(path.relative_to(ROOT)), "archived handoff must use closed status")
    if board_path.is_file():
        board = board_path.read_text(encoding="utf-8")
        board_names = set(re.findall(r"\[\[handoff/([^|\]]+)", board))
        if active_names != board_names:
            add_error(errors, "00-系统/agents/BOARD.md", "current handoff links must match active handoff files")
        if active_names and ("状态：" not in board or "当前负责人：" not in board or "下一步：" not in board):
            add_error(errors, "00-系统/agents/BOARD.md", "current handoff entries must include status, owner, and next action")

    return errors


def collaboration_consistency_errors():
    """Check that governed handoffs, work items, sessions, and receipts agree."""
    errors = []
    work_path = ROOT / ".orbitos/state/work-items.json"
    session_path = ROOT / ".orbitos/state/collaboration-sessions.json"
    if not work_path.is_file() or not session_path.is_file():
        return errors

    work_items = read_json_like(".orbitos/state/work-items.json")
    sessions_state = read_json_like(".orbitos/state/collaboration-sessions.json")
    works = work_items.get("items", {}) if isinstance(work_items, dict) else {}
    sessions = sessions_state.get("sessions", {}) if isinstance(sessions_state, dict) else {}
    if not isinstance(works, dict) or not isinstance(sessions, dict):
        return errors

    system_dir = "00-" + chr(0x7CFB) + chr(0x7EDF)
    handoff_root = ROOT / system_dir / "agents/handoff"
    archive_root = handoff_root / "archive"

    def metadata_for(path):
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        return dict(re.findall(r"^([a-z_]+):\s*(.*?)\s*$", parts[1] if len(parts) >= 3 else "", re.MULTILINE))

    def governed(metadata):
        return str(metadata.get("governance_required", "")).lower() == "true"

    def check_handoff(path, archived):
        metadata = metadata_for(path)
        if not governed(metadata):
            return
        relative = path.relative_to(ROOT).as_posix()
        session_id = metadata.get("collaboration_session_id")
        session = sessions.get(session_id)
        if not isinstance(session, dict):
            add_error(errors, relative, "governed handoff must reference an existing collaboration session")
            return
        expected_task_ref = relative.replace("/handoff/archive/", "/handoff/") if archived else relative
        if session.get("task_ref") != expected_task_ref:
            add_error(errors, relative, "governed handoff session task_ref must point to this handoff")
        if archived:
            if session.get("status") != "closed" or not session.get("gate_state", {}).get("hard_gate_passed"):
                add_error(errors, relative, "closed governed handoff requires a closed hard-gate-passed session")
        elif metadata.get("handoff_status") in {"working", "returned"} and session.get("status") == "closed":
            add_error(errors, relative, "open governed handoff cannot point to a closed session")

    for path in sorted(handoff_root.glob("*.md")) if handoff_root.is_dir() else []:
        check_handoff(path, archived=False)
    for path in sorted(archive_root.glob("*.md")) if archive_root.is_dir() else []:
        check_handoff(path, archived=True)

    for work_id, work in works.items():
        if not isinstance(work, dict):
            continue
        source_ref = work.get("source_ref")
        if work.get("source_type") == "handoff" and isinstance(source_ref, str) and source_ref:
            source_path = ROOT / source_ref.split("#", 1)[0]
            if not source_path.is_file():
                add_error(errors, f".orbitos/state/work-items.json#{work_id}", "work item source_ref does not exist")
        if work.get("status") == "done" and not work.get("evidence_refs"):
            add_error(errors, f".orbitos/state/work-items.json#{work_id}", "done work item requires evidence_refs")

    events_root = ROOT / ".orbitos/logs/events"
    for event_path in sorted(events_root.glob("*.yaml")) if events_root.is_dir() else []:
        content = event_path.read_text(encoding="utf-8").lstrip()
        if not content.startswith("{"):
            continue
        try:
            event = json.loads(content)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or "collaboration" not in event:
            continue
        collaboration = event.get("collaboration")
        actor = event.get("actor", {})
        outputs = event.get("outputs", [])
        if not isinstance(collaboration, dict):
            add_error(errors, str(event_path.relative_to(ROOT)), "collaboration receipt is invalid")
            continue
        session = sessions.get(collaboration.get("session_id"))
        if not isinstance(session, dict):
            add_error(errors, str(event_path.relative_to(ROOT)), "collaboration receipt references a missing session")
            continue
        if not isinstance(actor, dict) or actor.get("role") != session.get("role"):
            add_error(errors, str(event_path.relative_to(ROOT)), "collaboration receipt actor role must match the session role")
        if not isinstance(outputs, list) or not outputs:
            add_error(errors, str(event_path.relative_to(ROOT)), "collaboration receipt requires at least one output")
        review = session.get("review", {})
        if collaboration.get("review_status") != review.get("status"):
            add_error(errors, str(event_path.relative_to(ROOT)), "collaboration receipt review status must match the session")
        if collaboration.get("review_status") == "approved":
            if collaboration.get("reviewer_session_id") != review.get("reviewer_session_id") or collaboration.get("reviewer_agent_id") != review.get("reviewer_agent_id"):
                add_error(errors, str(event_path.relative_to(ROOT)), "approved collaboration receipt must retain its independent reviewer")

    return errors


def registered_agent_ids(agents):
    ids = []
    for agent in agents if isinstance(agents, list) else []:
        if isinstance(agent, dict):
            agent_id = agent.get("agent_id")
            if isinstance(agent_id, str) and agent_id.strip():
                ids.append(agent_id.strip())
    return ids


def agent_collaboration_evidence_errors():
    errors = []
    registry_path = ROOT / ".orbitos/agents/registry.yaml"
    if not registry_path.is_file():
        return errors

    registry = read_json_like(".orbitos/agents/registry.yaml")
    agents = registry.get("agents", []) if isinstance(registry, dict) else []
    if not agents:
        return errors

    for agent in agents if isinstance(agents, list) else []:
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            add_error(errors, ".orbitos/agents/registry.yaml", "registry entry is missing agent_id")
            continue

        deployment = agent.get("deployment", {})
        if not isinstance(deployment, dict):
            add_error(errors, ".orbitos/agents/registry.yaml", f"{agent_id} deployment is invalid")
            continue
        orbitos_path = deployment.get("orbitos_path")
        if not isinstance(orbitos_path, str) or not orbitos_path.strip():
            add_error(errors, ".orbitos/agents/registry.yaml", f"{agent_id} deployment is missing orbitos_path")

        profile_ref = agent.get("profile_ref")
        if not isinstance(profile_ref, str) or not profile_ref.strip():
            add_error(errors, ".orbitos/agents/registry.yaml", f"{agent_id} profile_ref is missing")
            continue
        profile_path = ROOT / profile_ref
        if not profile_path.is_file():
            add_error(errors, profile_ref, "agent profile is missing")
            continue
        profile_text = profile_path.read_text(encoding="utf-8")
        for term in ["## 经验入口", "## 启动关注"]:
            if term not in profile_text:
                add_error(errors, profile_ref, f"agent profile is missing required section: {term}")

    return errors


def agent_event_evidence_errors():
    errors = []
    registry_path = ROOT / ".orbitos/agents/registry.yaml"
    if not registry_path.is_file():
        return errors

    registry = read_json_like(".orbitos/agents/registry.yaml")
    agents = registry.get("agents", []) if isinstance(registry, dict) else []
    agent_ids = registered_agent_ids(agents)
    if len(agent_ids) <= 1:
        return errors

    events_root = ROOT / ".orbitos/logs/events"
    if not events_root.exists():
        return errors

    event_texts = []
    for event_path in sorted(events_root.glob("*.yaml")):
        try:
            event_texts.append((event_path.name, event_path.read_text(encoding="utf-8")))
        except OSError:
            continue

    for agent_id in agent_ids:
        if not any(
            f"agent_id: {agent_id}" in text or f'"agent_id": "{agent_id}"' in text
            for _name, text in event_texts
        ):
            add_error(errors, agent_id, "no event evidence found for registered agent")

    return errors


def walk_markdown(full_path):
    if not full_path.exists():
        return []
    if full_path.is_dir():
        return [path for path in full_path.rglob("*.md") if path.is_file()]
    return [full_path] if full_path.suffix == ".md" else []


SCHEMAS = {
    "event": read_json_like(".orbitos/schemas/event.schema.yaml"),
    "ingest-batch": read_json_like(".orbitos/schemas/ingest-batch.schema.yaml"),
    "lifecycle": read_json_like(".orbitos/schemas/lifecycle.schema.yaml"),
    "agent-registry": read_json_like(".orbitos/schemas/agent-registry.schema.yaml"),
    "module-catalog": read_json_like(".orbitos/schemas/module-catalog.schema.yaml"),
    "module-state": read_json_like(".orbitos/schemas/module-state.schema.yaml"),
    "maintenance-state": read_json_like(".orbitos/schemas/maintenance-state.schema.yaml"),
    "work-items": read_json_like(".orbitos/schemas/work-items.schema.yaml"),
    "role-catalog": read_json_like(".orbitos/schemas/role-catalog.schema.yaml"),
    "collaboration-sessions": read_json_like(".orbitos/schemas/collaboration-sessions.schema.yaml"),
    "handoff-queue": read_json_like(".orbitos/schemas/handoff-queue.schema.yaml"),
    "chaos-record": read_json_like(".orbitos/schemas/chaos-record.schema.yaml"),
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
    if name.startswith("agent-registry."):
        return "agent-registry"
    if name.startswith("event."):
        return "event"
    if name.startswith("lifecycle."):
        return "lifecycle"
    if name.startswith("maintenance-state."):
        return "maintenance-state"
    if name.startswith("work-items."):
        return "work-items"
    if name.startswith("chaos-record."):
        return "chaos-record"
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
    if schema_name == "event":
        validate_knowledge_event(data, errors)
    print_case(case_path.name, ".valid." in case_path.name, errors)


markdown_case_root = ROOT / ".orbitos/evals/markdown-link-boundary"
for case_path in sorted(markdown_case_root.glob("*.md")):
    case_count += 1
    errors = markdown_internal_wikilink_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


doc_consistency_case_root = ROOT / ".orbitos/evals/doc-consistency"
for case_path in sorted(doc_consistency_case_root.glob("*.md")):
    case_count += 1
    errors = []
    for issue in check_broken_wikilinks([case_path], ROOT):
        add_error(errors, f"{issue.file}:{issue.line}", issue.detail)
    for issue in check_legacy_paths([case_path], ROOT):
        add_error(errors, f"{issue.file}:{issue.line}", issue.detail)
    for issue in check_forbidden_statements([case_path], ROOT):
        add_error(errors, f"{issue.file}:{issue.line}", issue.detail)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_source_case_root = ROOT / ".orbitos/evals/knowledge-source"
for case_path in sorted(knowledge_source_case_root.glob("*.md")):
    case_count += 1
    errors = knowledge_source_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_orphan_case_root = ROOT / ".orbitos/evals/knowledge-orphan-draft"
for case_path in sorted(knowledge_orphan_case_root.glob("*.md")):
    case_count += 1
    projection_files = [path for path in knowledge_orphan_case_root.glob("*.md") if path != case_path]
    errors = orphan_draft_errors([case_path], projection_files)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_omitted_conflict_case_root = ROOT / ".orbitos/evals/knowledge-omitted-conflict"
for case_path in sorted(knowledge_omitted_conflict_case_root.glob("*.md")):
    case_count += 1
    errors = omitted_conflict_errors(list(knowledge_omitted_conflict_case_root.glob("*.md")))
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_omitted_conflict_valid_root = ROOT / ".orbitos/evals/knowledge-omitted-conflict-valid"
for case_path in sorted(knowledge_omitted_conflict_valid_root.glob("*.md")):
    case_count += 1
    errors = omitted_conflict_errors(list(knowledge_omitted_conflict_valid_root.glob("*.md")))
    print_case(case_path.name, ".valid." in case_path.name, errors)


chaos_record_case_root = ROOT / ".orbitos/evals/chaos-record"
for case_path in sorted(chaos_record_case_root.glob("*.yaml")):
    case_count += 1
    data = read_json_like(f".orbitos/evals/chaos-record/{case_path.name}")
    errors = []
    validate_value(data, SCHEMAS["chaos-record"], "$", errors)
    print_case(case_path.name, ".valid." in case_path.name, errors)


chaos_purpose_case_root = ROOT / ".orbitos/evals/chaos-purpose"
for case_path in sorted(chaos_purpose_case_root.glob("*.md")):
    case_count += 1
    errors = chaos_purpose_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_exit_case_root = ROOT / ".orbitos/evals/knowledge-exit"
for case_path in sorted(knowledge_exit_case_root.glob("*.md")):
    case_count += 1
    errors = chaos_purpose_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_gate_case_root = ROOT / ".orbitos/evals/knowledge-draft-gates"
for case_path in sorted(knowledge_gate_case_root.glob("*.md")):
    case_count += 1
    errors = knowledge_draft_gate_errors(case_path)
    print_case(case_path.name, ".valid." in case_path.name, errors)


knowledge_closed_loop_case_root = ROOT / ".orbitos/evals/knowledge-closed-loop"
for case_path in sorted(knowledge_closed_loop_case_root.glob("*.yaml")):
    case_count += 1
    data = read_json_like(f".orbitos/evals/knowledge-closed-loop/{case_path.name}")
    errors = closed_loop_scenario_errors(data, case_path.name)
    print_case(case_path.name, ".valid." in case_path.name, errors)


collaboration_queue_case_root = ROOT / ".orbitos/evals/collaboration-queue"
for case_path in sorted(collaboration_queue_case_root.glob("*.yaml")):
    case_count += 1
    data = read_json_like(f".orbitos/evals/collaboration-queue/{case_path.name}")
    errors = collaboration_queue_scenario_errors(data, case_path.name)
    print_case(case_path.name, ".valid." in case_path.name, errors)


case_count += 1
visible_files = [
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "README.zh-CN.md",
    *walk_markdown(ROOT / "00-系统"),
    *walk_markdown(ROOT / "02-时间线"),
]
visible_files = [path for path in visible_files if path.is_file()]
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
doc_consistency_errors = []
visible_files = find_visible_markdown(ROOT)
for issue in check_broken_wikilinks(visible_files, ROOT):
    add_error(doc_consistency_errors, f"{issue.file}:{issue.line}", issue.detail)
for issue in check_legacy_paths(visible_files, ROOT):
    add_error(doc_consistency_errors, f"{issue.file}:{issue.line}", issue.detail)
for issue in check_forbidden_statements(visible_files, ROOT):
    add_error(doc_consistency_errors, f"{issue.file}:{issue.line}", issue.detail)
print_case("visible-markdown.doc-consistency", True, doc_consistency_errors)


case_count += 1
knowledge_source_errors_list = []
knowledge_files = [
    path
    for path in (ROOT / "04-知识").rglob("*.md")
    if path.is_file() and path.name != "MAP.md"
]
for file_path in knowledge_files:
    for error in knowledge_source_errors(file_path):
        add_error(
            knowledge_source_errors_list,
            error["path"],
            error["message"],
        )
print_case("actual.knowledge-sources", True, knowledge_source_errors_list)


case_count += 1
knowledge_orphan_errors_list = []
draft_dir = ROOT / "04-知识/00-草稿箱"
projection_files = []
for candidate in [ROOT / "02-时间线/今日.md", ROOT / "03-项目/OrbitOS/STATUS.md"]:
    if candidate.is_file():
        projection_files.append(candidate)
if draft_dir.exists():
    draft_files = [path for path in draft_dir.glob("*.md") if path.is_file() and path.name != ".gitkeep"]
    knowledge_orphan_errors_list.extend(orphan_draft_errors(draft_files, projection_files))
print_case("actual.knowledge-orphan-drafts", True, knowledge_orphan_errors_list)


case_count += 1
knowledge_omitted_conflict_errors_list = omitted_conflict_errors(knowledge_files)
print_case("actual.knowledge-omitted-conflicts", True, knowledge_omitted_conflict_errors_list)


case_count += 1
handoff_structure_errors_list = handoff_structure_errors()
print_case("actual.agent-handoff-structure", True, handoff_structure_errors_list)


case_count += 1
agent_collaboration_evidence_errors_list = agent_collaboration_evidence_errors()
print_case("actual.agent-collaboration-evidence", True, agent_collaboration_evidence_errors_list)


case_count += 1
agent_event_evidence_errors_list = agent_event_evidence_errors()
print_case("actual.agent-event-evidence", True, agent_event_evidence_errors_list)


case_count += 1
document_semantics_errors = []
document_semantics_path = ROOT / ".orbitos/rules/core/document-semantics.md"
if not document_semantics_path.is_file():
    add_error(document_semantics_errors, ".orbitos/rules/core/document-semantics.md", "global document semantics rule is missing")
else:
    document_semantics = document_semantics_path.read_text(encoding="utf-8")
    for role in ["MAP.md", "README.md", "AGENTS.md", "STATUS.md", "ROADMAP.md", "CHANGELOG.md", "ADR"]:
        if role not in document_semantics:
            add_error(document_semantics_errors, role, "fixed document role is missing from document semantics rule")
    for creation_gate_term in ["Markdown 创建门", "现有文件为什么不能承载", "路径、受众和生命周期", "等待用户确认"]:
        if creation_gate_term not in document_semantics:
            add_error(document_semantics_errors, creation_gate_term, "generic Markdown creation gate is incomplete")
    if "内部项目管理目录默认不创建" not in document_semantics:
        add_error(document_semantics_errors, "README.md", "internal project directories must not require a README by default")
    for map_boundary_term in ["直属子目录", "一句话说明它是什么", "不下钻"]:
        if map_boundary_term not in document_semantics:
            add_error(document_semantics_errors, map_boundary_term, "MAP navigation boundary is incomplete")
    for roadmap_boundary_term in ["总体状态", "其他跨会话小任务标注“临时事项”", "validation 和 event 证据", "CHANGELOG.md"]:
        if roadmap_boundary_term not in document_semantics:
            add_error(document_semantics_errors, roadmap_boundary_term, "roadmap/status/changelog data flow is incomplete")
root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
if "document-semantics.md" not in root_agents:
    add_error(document_semantics_errors, "AGENTS.md", "root Agent router does not expose document semantics rule")
project_management_path = ROOT / ".orbitos/rules/core/project-management.md"
if not project_management_path.is_file():
    add_error(document_semantics_errors, ".orbitos/rules/core/project-management.md", "shared project management rule is missing")
else:
    project_management = project_management_path.read_text(encoding="utf-8")
    for project_term in ["用户只需自然提出任务", "当场完成且不需要下次继续的小修改", "需要跨会话继续的工作", "只有用户决定现在推进后", "禁止自动流转", "否则标注“临时事项”", "已验证项使用 `[x]`", "STATUS 与 ROADMAP 必须在同一次 Progress Sync 中保持一致", "`repo/` 保存实际产品或发布仓库"]:
        if project_term not in project_management:
            add_error(document_semantics_errors, project_term, "shared project management rule is incomplete")
progress_sync_path = ROOT / ".orbitos/workflows/progress-sync.md"
progress_sync = progress_sync_path.read_text(encoding="utf-8") if progress_sync_path.is_file() else ""
for sync_term in ["用户不需要主动说出同步命令", "project-management.md", "不把 STATUS 自动提升为 ROADMAP"]:
    if sync_term not in progress_sync:
        add_error(document_semantics_errors, sync_term, "Progress Sync does not enforce project task flow")
if "project-management.md" not in root_agents:
    add_error(document_semantics_errors, "AGENTS.md", "root Agent router does not expose project management rule")
thinking_rule_path = ROOT / ".orbitos/rules/core/thinking.md"
thinking_reference_path = ROOT / ".orbitos/rules/core/thinking-modes.md"
if not thinking_rule_path.is_file():
    add_error(document_semantics_errors, ".orbitos/rules/core/thinking.md", "core thinking rule is missing")
else:
    thinking_rule = thinking_rule_path.read_text(encoding="utf-8")
    for term in ["thinking-modes.md", "思考模式启动选择", "回复 1 / 2 / 3", "直接做"]:
        if term not in thinking_rule:
            add_error(document_semantics_errors, ".orbitos/rules/core/thinking.md", f"core thinking rule is missing: {term}")
if "思考模式启动选择" not in root_agents:
    add_error(document_semantics_errors, "AGENTS.md", "root Agent router does not require thinking selection")
if not thinking_reference_path.is_file():
    add_error(document_semantics_errors, ".orbitos/rules/core/thinking-modes.md", "core thinking modes reference is missing")
else:
    thinking_reference = thinking_reference_path.read_text(encoding="utf-8")
    for mode in ["5W1H", "苏格拉底提问", "SWOT", "第一性原理", "反向推导", "金字塔原理", "六顶思考帽", "批判性思维"]:
        if mode not in thinking_reference:
            add_error(document_semantics_errors, mode, "thinking modes reference is incomplete")
print_case("actual.document-semantics", True, document_semantics_errors)


case_count += 1
event_filename_errors = []
event_filename_pattern = re.compile(r"^20[0-9]{6}_[0-9]{6}_[a-z0-9]+(?:_[a-z0-9]+)*\.yaml$")
event_cutoff = "20260615"
events_root = ROOT / ".orbitos/logs/events"
for child in sorted(events_root.iterdir() if events_root.exists() else []):
    if child.is_dir():
        add_error(
            event_filename_errors,
            f".orbitos/logs/events/{child.name}",
            "event directory must stay flat; date subdirectories are not allowed",
        )
for event_path in sorted(events_root.glob("*.yaml")):
    name = event_path.name
    date_text = name[:8]
    if date_text.isdigit() and date_text >= event_cutoff and not event_filename_pattern.match(name):
        add_error(
            event_filename_errors,
            f".orbitos/logs/events/{name}",
            "event file name must match YYYYMMDD_HHMMSS_slug.yaml with lowercase snake_case",
        )
    if name.startswith("evt_"):
        embedded_date = name[4:12]
        if embedded_date.isdigit() and embedded_date >= event_cutoff:
            add_error(
                event_filename_errors,
                f".orbitos/logs/events/{name}",
                "event file name must not include evt_ prefix",
            )
print_case("actual.event-filenames", True, event_filename_errors)


case_count += 1
event_record_errors = []
for event_path in sorted(events_root.glob("*.yaml")):
    content = event_path.read_text(encoding="utf-8").lstrip()
    if not content.startswith("{"):
        continue
    try:
        event_data = json.loads(content)
        validate_value(
            event_data,
            SCHEMAS["event"],
            f"$[{event_path.name}]",
            event_record_errors,
        )
        validate_knowledge_event(event_data, event_record_errors, f"$[{event_path.name}]")
        thinking = event_data.get("thinking")
        if isinstance(thinking, dict):
            modes = thinking.get("modes", [])
            outcome = thinking.get("outcome")
            if outcome == "selected" and not modes:
                add_error(event_record_errors, f"$[{event_path.name}].thinking", "selected thinking must include at least one mode")
            if outcome == "bypassed" and modes:
                add_error(event_record_errors, f"$[{event_path.name}].thinking", "bypassed thinking must not include modes")
            if event_data.get("thinking_modes", []) != [item.get("mode") for item in modes]:
                add_error(event_record_errors, f"$[{event_path.name}].thinking_modes", "thinking modes summary must match thinking details")
    except json.JSONDecodeError as error:
        add_error(
            event_record_errors,
            f".orbitos/logs/events/{event_path.name}",
            f"invalid JSON-compatible event: {error}",
        )
print_case("actual.event-records", True, event_record_errors)


case_count += 1
print_case("actual.knowledge-flow", True, knowledge_flow_errors())


case_count += 1
chaos_purpose_actual_errors = []
chaos_pending_dir = ROOT / "01-收件箱/待铸卡"
if chaos_pending_dir.exists():
    for file_path in sorted(chaos_pending_dir.glob("*.md")):
        if "模板" in file_path.name:
            continue
        chaos_purpose_actual_errors.extend(chaos_purpose_errors(file_path))
print_case("actual.chaos-records", True, chaos_purpose_actual_errors)


case_count += 1
print_case("actual.chaos-flow", True, chaos_flow_errors())


case_count += 1
module_errors = []
catalog_path = ROOT / ".orbitos/module-catalog.json"
module_state_path = ROOT / ".orbitos/state/modules.json"
module_catalog = {"modules": {}}
module_state = {"modules": {}}
if not catalog_path.is_file():
    add_error(module_errors, ".orbitos/module-catalog.json", "module catalog is missing")
else:
    module_catalog = read_json_like(".orbitos/module-catalog.json")
    validate_value(module_catalog, SCHEMAS["module-catalog"], "$", module_errors)
if not module_state_path.is_file():
    add_error(module_errors, ".orbitos/state/modules.json", "module state registry is missing")
else:
    module_state = read_json_like(".orbitos/state/modules.json")
    validate_value(module_state, SCHEMAS["module-state"], "$", module_errors)

catalog_modules = module_catalog.get("modules", {})
state_modules = module_state.get("modules", {})
legacy_visible_domains = {
    item.get("path")
    for item in module_state.get("legacy_visible_domains", [])
    if isinstance(item, dict)
}
for module_id, record in state_modules.items():
    if module_id not in catalog_modules:
        add_error(module_errors, f".orbitos/state/modules.json:{module_id}", "state references an unknown module")
        continue
    state_name = record.get("state") if isinstance(record, dict) else None
    live_root = ROOT / ".orbitos/modules" / module_id
    if state_name in {"installed_disabled", "enabled_unconfigured", "ready", "blocked", "disabled"} and not live_root.is_dir():
        add_error(module_errors, f".orbitos/modules/{module_id}", "installed module files are missing")
    if state_name == "ready":
        for required_path in catalog_modules[module_id].get("required_paths", []):
            if not (live_root / required_path).is_file():
                add_error(module_errors, f".orbitos/modules/{module_id}/{required_path}", "ready module is missing a required file")
        for visible_path in catalog_modules[module_id].get("visible_paths", []):
            if not (ROOT / visible_path).is_dir():
                add_error(module_errors, visible_path, "ready module is missing its visible domain")

live_modules_root = ROOT / ".orbitos/modules"
if live_modules_root.is_dir():
    for path in live_modules_root.iterdir():
        if path.is_dir() and path.name not in state_modules:
            add_error(module_errors, f".orbitos/modules/{path.name}", "module files exist without a state entry")
print_case("actual.module-state", True, module_errors)


case_count += 1
maintenance_errors = []
maintenance_state_path = ROOT / ".orbitos/state/maintenance.json"
if not maintenance_state_path.is_file():
    # The Product Repo ships the template; init-runtime creates the ignored runtime state.
    pass
else:
    maintenance_state = read_json_like(".orbitos/state/maintenance.json")
    validate_value(maintenance_state, SCHEMAS["maintenance-state"], "$", maintenance_errors)
print_case("actual.maintenance-state", True, maintenance_errors)

case_count += 1
work_item_errors = []
work_item_state_path = ROOT / ".orbitos/state/work-items.json"
if work_item_state_path.is_file():
    work_items = read_json_like(".orbitos/state/work-items.json")
    validate_value(work_items, SCHEMAS["work-items"], "$", work_item_errors)
print_case("actual.work-items-state", True, work_item_errors)


case_count += 1
collaboration_asset_errors = []
role_catalog_path = ROOT / ".orbitos/module-packages/collaboration/roles.json"
role_schema_path = ROOT / ".orbitos/schemas/role-catalog.schema.yaml"
session_schema_path = ROOT / ".orbitos/schemas/collaboration-sessions.schema.yaml"
session_script_path = ROOT / ".orbitos/scripts/collab-session.py"
session_workflow_path = ROOT / ".orbitos/module-packages/collaboration/workflows/governance-session.md"
session_rule_path = ROOT / ".orbitos/module-packages/collaboration/rules/collaboration-governance.md"
session_template_path = ROOT / ".orbitos/templates/.orbitos/state/collaboration-sessions.json"
for required_path in [
    role_catalog_path,
    role_schema_path,
    session_schema_path,
    session_script_path,
    session_workflow_path,
    session_rule_path,
    session_template_path,
]:
    if not required_path.is_file():
        add_error(collaboration_asset_errors, str(required_path.relative_to(ROOT)), "collaboration governance asset is missing")
if role_catalog_path.is_file():
    role_catalog = read_json_like(".orbitos/module-packages/collaboration/roles.json")
    validate_value(role_catalog, SCHEMAS["role-catalog"], "$", collaboration_asset_errors)
    required_roles = {"coordinator", "researcher", "writer", "builder", "editor"}
    actual_roles = set(role_catalog.get("roles", {}))
    if actual_roles != required_roles:
        add_error(collaboration_asset_errors, ".orbitos/module-packages/collaboration/roles.json", f"role catalog must contain exactly {sorted(required_roles)}, got {sorted(actual_roles)}")
if session_template_path.is_file():
    session_template = read_json_like(".orbitos/templates/.orbitos/state/collaboration-sessions.json")
    validate_value(session_template, SCHEMAS["collaboration-sessions"], "$", collaboration_asset_errors)
for path, terms in {
    session_script_path: ["def main", "open", "claim", "heartbeat", "submit-research", "review", "review_target_session_id", "confidence_tier", "evidence_kind", "independently_reviewed", "review_required", "revision"],
    session_workflow_path: ["collaboration-sessions.json", "single_agent_subsession", "multi_agent_claim", "review_target_session_id", "independently_reviewed", "task_ref", "yellow", "green"],
    session_rule_path: ["未注册 Agent", "租约", "审核自己的产出", "independently_reviewed", "confidence", "回流"],
}.items():
    if path.is_file():
        content = path.read_text(encoding="utf-8")
        for term in terms:
            if term not in content:
                add_error(collaboration_asset_errors, str(path.relative_to(ROOT)), f"collaboration governance asset is missing required term: {term}")
print_case("actual.collaboration-governance-assets", True, collaboration_asset_errors)


case_count += 1
collaboration_state_errors = []
collaboration_state_path = ROOT / ".orbitos/state/collaboration-sessions.json"
if collaboration_state_path.is_file():
    collaboration_state = read_json_like(".orbitos/state/collaboration-sessions.json")
    validate_value(collaboration_state, SCHEMAS["collaboration-sessions"], "$", collaboration_state_errors)
print_case("actual.collaboration-sessions-state", True, collaboration_state_errors)


case_count += 1
collaboration_consistency_errors_list = collaboration_consistency_errors()
print_case("actual.collaboration-state-consistency", True, collaboration_consistency_errors_list)


case_count += 1
collaboration_queue_asset_errors_list = collaboration_queue_asset_errors()
print_case("actual.collaboration-queue-assets", True, collaboration_queue_asset_errors_list)


case_count += 1
collaboration_queue_state_errors_list = collaboration_queue_state_errors()
print_case("actual.collaboration-queue-state", True, collaboration_queue_state_errors_list)


case_count += 1
root_directory_errors = []
required_core_root_dirs = [
    "00-系统",
    "01-收件箱",
    "02-时间线",
    "03-项目",
    "04-知识",
]
allowed_root_dirs = required_core_root_dirs + [
    "05-阅读",
    "06-资源",
    "07-输出",
    "99-归档",
]
root_numbered_pattern = re.compile(r"^[0-9]{2}-")
root_numbered_dirs = [
    path.name for path in ROOT.iterdir() if path.is_dir() and root_numbered_pattern.match(path.name)
]
for expected_name in required_core_root_dirs:
    if not (ROOT / expected_name).is_dir():
        add_error(
            root_directory_errors,
            expected_name,
            "required root numbered directory is missing",
        )
for name in root_numbered_dirs:
    if name not in allowed_root_dirs:
        add_error(
            root_directory_errors,
            name,
            "unexpected root numbered directory; discuss lifecycle role before adding",
        )
prefixes = [name[:2] for name in root_numbered_dirs]
for prefix in sorted(set(prefixes)):
    if prefixes.count(prefix) > 1:
        add_error(
            root_directory_errors,
            prefix,
            "duplicate root directory numeric prefix",
        )
if (ROOT / "05-阅读").exists() and state_modules.get("reading", {}).get("state") not in {"ready", "disabled"}:
    add_error(root_directory_errors, "05-阅读", "reading domain exists but the reading module is not ready")
for reserved_name in ("06-资源", "07-输出"):
    if (ROOT / reserved_name).exists() and reserved_name not in legacy_visible_domains:
        add_error(root_directory_errors, reserved_name, "reserved domain has no installable module package")
for legacy_name in legacy_visible_domains:
    if not (ROOT / legacy_name).is_dir():
        add_error(root_directory_errors, legacy_name, "legacy visible-domain entry must be removed after its directory is gone")
print_case("actual.root-directories", True, root_directory_errors)


case_count += 1
system_manual_errors = []
required_system_manual = [
    "00-开始使用.md",
    "01-目录说明.md",
    "02-日常协作.md",
    "03-内容生命周期.md",
    "04-安全与边界.md",
    "05-思考方法.md",
    "06-模块与扩展.md",
    "07-Agent协作.md",
    "08-术语表.md",
    "99-系统变更.md",
]
legacy_system_manual = [
    "MAP.md",
    "CONTEXT.md",
    "PRINCIPLES.md",
    "DATA-LIFECYCLE.md",
    "CHANGELOG.md",
]
system_dir = ROOT / "00-系统"
for name in required_system_manual:
    if not (system_dir / name).is_file():
        add_error(system_manual_errors, f"00-系统/{name}", "required numbered system manual page is missing")
for name in legacy_system_manual:
    if (system_dir / name).exists():
        add_error(system_manual_errors, f"00-系统/{name}", "legacy system manual filename must not be restored")
print_case("actual.system-manual", True, system_manual_errors)


case_count += 1
knowledge_directory_errors = []
knowledge_dir = ROOT / "04-知识"
knowledge_subdir_pattern = re.compile(r"^[0-9]{2}-")
if knowledge_dir.exists():
    for path in sorted(knowledge_dir.iterdir()):
        if path.is_dir() and not knowledge_subdir_pattern.match(path.name):
            add_error(
                knowledge_directory_errors,
                f"04-知识/{path.name}",
                "knowledge first-level directory must use NN-name stable order",
            )
print_case("actual.knowledge-directories", True, knowledge_directory_errors)


case_count += 1
machine_layer_errors = []
if (ROOT / ".orbitos/docs").exists():
    add_error(machine_layer_errors, ".orbitos/docs", "runtime machine layer must not contain human-readable design docs")
print_case("actual.machine-layer-boundary", True, machine_layer_errors)


case_count += 1
runtime_template_errors = []
required_runtime_templates = [
    ".orbitos/templates/.orbitos/agents/registry.yaml",
    ".orbitos/templates/.orbitos/state/modules.json",
    ".orbitos/templates/.orbitos/state/maintenance.json",
    ".orbitos/templates/.orbitos/state/work-items.json",
    ".orbitos/templates/01-收件箱/00-粘贴.md",
    ".orbitos/templates/02-时间线/今日.md",
    ".orbitos/templates/02-时间线/本周.md",
    ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md",
]
for relative_path in required_runtime_templates:
    if not (ROOT / relative_path).is_file():
        add_error(runtime_template_errors, relative_path, "required runtime template is missing")
registry_template_path = ROOT / ".orbitos/templates/.orbitos/agents/registry.yaml"
if registry_template_path.is_file():
    validate_value(read_json_like(".orbitos/templates/.orbitos/agents/registry.yaml"), SCHEMAS["agent-registry"], "$", runtime_template_errors)
print_case("actual.runtime-templates", True, runtime_template_errors)


case_count += 1
clipboard_flow_errors = []
clipboard_workflow_path = ROOT / ".orbitos/workflows/clipboard-flush.md"
if not clipboard_workflow_path.is_file():
    add_error(clipboard_flow_errors, ".orbitos/workflows/clipboard-flush.md", "clipboard flush workflow is missing")
else:
    clipboard_workflow = clipboard_workflow_path.read_text(encoding="utf-8")
    for term in ["00-粘贴.md", "物化", "删除", "确认", "inbox-triage.md", "inbox-ingest.md"]:
        if term not in clipboard_workflow:
            add_error(clipboard_flow_errors, ".orbitos/workflows/clipboard-flush.md", f"clipboard workflow is missing required term: {term}")
root_agent_path = ROOT / "AGENTS.md"
if root_agent_path.is_file() and "处理粘贴内容" not in root_agent_path.read_text(encoding="utf-8"):
    add_error(clipboard_flow_errors, "AGENTS.md", "clipboard workflow route is missing")
clipboard_template_path = ROOT / ".orbitos/templates/01-收件箱/00-粘贴.md"
if clipboard_template_path.is_file() and "整理粘贴内容" not in clipboard_template_path.read_text(encoding="utf-8"):
    add_error(clipboard_flow_errors, ".orbitos/templates/01-收件箱/00-粘贴.md", "clipboard template is missing its processing entry")
print_case("actual.clipboard-flow", True, clipboard_flow_errors)


case_count += 1
inbox_workflow_errors = []
for relative_path, terms in {
    ".orbitos/workflows/inbox-triage.md": ["single_source", "source_collection", "不按 PDF、图片、Markdown"],
    ".orbitos/workflows/inbox-ingest.md": ["single_source", "source_collection", "不创建全局", "00-粘贴.md"],
}.items():
    path = ROOT / relative_path
    if not path.is_file():
        add_error(inbox_workflow_errors, relative_path, "inbox workflow is missing")
        continue
    text = path.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            add_error(inbox_workflow_errors, relative_path, f"inbox workflow is missing required term: {term}")
print_case("actual.inbox-storage-boundary", True, inbox_workflow_errors)


case_count += 1
reading_domain_errors = []
reading_health_script = ROOT / ".orbitos/scripts/reading-health-check.py"
reading_ready = state_modules.get("reading", {}).get("state") == "ready"
if reading_ready and not reading_health_script.is_file():
    add_error(reading_domain_errors, ".orbitos/scripts/reading-health-check.py", "reading health check is missing")
elif reading_ready:
    result = subprocess.run(
        [sys.executable, str(reading_health_script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        health_report = json.loads(result.stdout)
    except json.JSONDecodeError:
        add_error(reading_domain_errors, ".orbitos/scripts/reading-health-check.py", "reading health check did not return JSON")
    else:
        for issue in health_report.get("issues", []):
            add_error(reading_domain_errors, issue.get("path", "05-阅读"), issue.get("message", "reading health check failed"))
        if result.returncode and not health_report.get("issues"):
            add_error(reading_domain_errors, ".orbitos/scripts/reading-health-check.py", "reading health check failed without reporting issues")
if reading_ready and (ROOT / "05-阅读/.claude").exists():
    add_error(reading_domain_errors, "05-阅读/.claude", "reading domain must not contain Agent-specific Claude configuration")
print_case("actual.reading-domain", True, reading_domain_errors)


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

if ingest_dir.exists():
    for batch_path in sorted(ingest_dir.glob("*.yaml")):
        batch = read_json_like(f".orbitos/ingest/batches/{batch_path.name}")
        if isinstance(batch.get("items"), list):
            for item in batch["items"]:
                file_name = item.get("file") if isinstance(item, dict) else None
                if file_name == "00-粘贴.md":
                    add_error(
                        ingest_errors,
                        f".orbitos/ingest/batches/{batch_path.name}:00-粘贴.md",
                        "00-粘贴.md is a fixed clipboard entry and must not be registered as an ingest item",
                    )

if ingested_dir.exists():
    for file_path in ingested_dir.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(ingested_dir).as_posix()
        if relative_path == "00-粘贴.md":
            add_error(
                ingest_errors,
                "01-收件箱/已入库/00-粘贴.md",
                "00-粘贴.md must remain in the inbox root clipboard slot, not inside 已入库/",
            )
        elif relative_path not in recorded_files:
            add_error(
                ingest_errors,
                f"01-收件箱/已入库/{relative_path}",
                "ingested file is missing an ingest batch record",
            )
print_case("actual.ingest-batches", True, ingest_errors)


case_count += 1
event_writer_errors = []
writer_path = ROOT / ".orbitos/scripts/write_event.py"
if not writer_path.is_file():
    add_error(event_writer_errors, ".orbitos/scripts/write_event.py", "event writer is missing")
else:
    command = [
        sys.executable,
        str(writer_path),
        "--agent-id",
        "codex",
        "--slug",
        "validation_probe",
        "--summary",
        "Validate the generated completion receipt.",
        "--reason",
        "Ensure the event writer still matches event.schema.yaml.",
        "--validation",
        "passed",
        "--dry-run",
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        add_error(event_writer_errors, ".orbitos/scripts/write_event.py", result.stderr.strip())
    else:
        try:
            generated_event = json.loads(result.stdout)
            validate_value(generated_event, SCHEMAS["event"], "$", event_writer_errors)
        except json.JSONDecodeError as error:
            add_error(event_writer_errors, ".orbitos/scripts/write_event.py", f"invalid JSON output: {error}")
    knowledge_command = command + [
        "--event-type",
        "knowledge_use",
        "--knowledge-source",
        "04-知识/MAP.md",
        "--knowledge-fit",
        "applicable",
        "--knowledge-outcome",
        "pending",
        "--knowledge-feedback-route",
        "none",
    ]
    knowledge_result = subprocess.run(knowledge_command, capture_output=True, text=True, encoding="utf-8")
    if knowledge_result.returncode != 0:
        add_error(event_writer_errors, ".orbitos/scripts/write_event.py", knowledge_result.stderr.strip())
    else:
        try:
            generated_knowledge_event = json.loads(knowledge_result.stdout)
            validate_value(generated_knowledge_event, SCHEMAS["event"], "$", event_writer_errors)
            validate_knowledge_event(generated_knowledge_event, event_writer_errors)
        except json.JSONDecodeError as error:
            add_error(event_writer_errors, ".orbitos/scripts/write_event.py", f"invalid knowledge_use JSON output: {error}")
print_case("actual.event-writer", True, event_writer_errors)


if failure_count > 0:
    print("")
    print(f"Validation eval failed: {failure_count} case(s).")
    sys.exit(1)

print("")
print(f"Validation eval passed: {case_count} case(s).")
