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
            source_map.setdefault(target, []).append(file_path)
    for target, file_paths in sorted(source_map.items(), key=lambda item: str(item[0])):
        if len(file_paths) > 1:
            add_error(
                errors,
                str(target.relative_to(ROOT)),
                "same source is referenced by multiple active knowledge files; possible omitted conflict",
            )
    return errors


def handoff_structure_errors():
    errors = []
    required_paths = [
        ROOT / "00-系统/agents/BOARD.md",
        ROOT / ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/agent-handoff.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md",
        ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md",
        ROOT / "00-系统/agents/handoff/archive/.gitkeep",
    ]
    for path in required_paths:
        if not path.is_file():
            add_error(errors, str(path.relative_to(ROOT)), "handoff structure file is missing")

    board_path = ROOT / "00-系统/agents/BOARD.md"
    if board_path.is_file():
        board = board_path.read_text(encoding="utf-8")
        for term in ["Agent 交接板", "不记录用户确认事项", "不记录项目总状态", "最近完成的 handoff", "handoff/archive/", "handoff/"]:
            if term not in board:
                add_error(errors, "00-系统/agents/BOARD.md", f"handoff board is missing required term: {term}")

    template_path = ROOT / ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md"
    if template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
        for term in [
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
            "[ ] 我已阅读并确认这个 hand-off，准备接手。",
        ]:
            if term not in template:
                add_error(errors, ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md", f"handoff template is missing required term: {term}")

    workflow_path = ROOT / ".orbitos/module-packages/collaboration/workflows/agent-handoff.md"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        for term in ["execution_mode=delegated", "00-系统/agents/handoff/", "STATUS.md", "validation"]:
            if term not in workflow:
                add_error(errors, str(workflow_path.relative_to(ROOT)), f"handoff workflow is missing required term: {term}")

    pickup_path = ROOT / ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md"
    if pickup_path.is_file():
        pickup = pickup_path.read_text(encoding="utf-8")
        for term in ["获取交接工作", "00-系统/agents/BOARD.md", "交给谁", "接手动作", "不得要求用户提供 handoff 路径"]:
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
print_case("actual.event-writer", True, event_writer_errors)


if failure_count > 0:
    print("")
    print(f"Validation eval failed: {failure_count} case(s).")
    sys.exit(1)

print("")
print(f"Validation eval passed: {case_count} case(s).")
