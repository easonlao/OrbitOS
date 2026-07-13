import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(import.meta.dirname, "../..");

function readJsonLike(relativePath) {
  const fullPath = path.join(root, relativePath);
  return JSON.parse(fs.readFileSync(fullPath, "utf8"));
}

function hasOwn(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function allowedTypes(schema) {
  if (!hasOwn(schema, "type")) return [];
  return Array.isArray(schema.type) ? schema.type : [schema.type];
}

function testType(value, types) {
  if (types.length === 0) return true;
  return types.some((type) => {
    if (type === "null") return value === null;
    if (type === "array") return Array.isArray(value);
    if (type === "integer") return Number.isInteger(value);
    if (type === "number") return typeof value === "number";
    if (type === "object") return value !== null && typeof value === "object" && !Array.isArray(value);
    return typeof value === type;
  });
}

function addError(errors, pathText, message) {
  errors.push({ path: pathText, message });
}

function validateValue(value, schema, pathText, errors) {
  const types = allowedTypes(schema);
  if (!testType(value, types)) {
    addError(errors, pathText, `type mismatch; expected ${types.join("|")}`);
    return;
  }

  if (hasOwn(schema, "enum") && !schema.enum.some((item) => item === value)) {
    addError(errors, pathText, "value is not in enum");
  }
  if (hasOwn(schema, "maxItems") && Array.isArray(value) && value.length > schema.maxItems) {
    addError(errors, pathText, `array exceeds maxItems=${schema.maxItems}`);
  }

  if (types.includes("object") && value !== null && typeof value === "object" && !Array.isArray(value)) {
    const properties = schema.properties ?? {};
    const required = schema.required ?? [];

    for (const name of required) {
      if (!hasOwn(value, name)) addError(errors, `${pathText}.${name}`, "missing required field");
    }

    const additionalProperties = schema.additionalProperties ?? true;
    if (additionalProperties === false) {
      for (const name of Object.keys(value)) {
        if (!hasOwn(properties, name)) addError(errors, `${pathText}.${name}`, "additional property is not allowed");
      }
    }

    for (const name of Object.keys(properties)) {
      if (hasOwn(value, name)) validateValue(value[name], properties[name], `${pathText}.${name}`, errors);
    }
    if (additionalProperties !== null && typeof additionalProperties === "object") {
      for (const [name, item] of Object.entries(value)) {
        if (!hasOwn(properties, name)) validateValue(item, additionalProperties, `${pathText}.${name}`, errors);
      }
    }
  }

  if (types.includes("array") && Array.isArray(value) && schema.items) {
    value.forEach((item, index) => validateValue(item, schema.items, `${pathText}[${index}]`, errors));
  }
}

function validateLifecycle(value, errors) {
  const from = value.previous_status ?? "";
  const to = value.status;
  const pair = `${from}|${to}`;
  const allowedPairs = new Set([
    "|raw",
    "raw|triaged",
    "triaged|confirmed",
    "confirmed|processed",
    "processed|archived",
    "raw|archived",
  ]);
  if (!allowedPairs.has(pair)) addError(errors, "$.status", `illegal lifecycle transition: ${from || null} -> ${to}`);
}

function markdownInternalWikilinkErrors(fullPath) {
  const content = fs.readFileSync(fullPath, "utf8");
  const pattern = /\[\[[^\]]*(?:^|\/|\\|\.\.)\.orbitos(?:\/|\\)[^\]]*\]\]/g;
  const errors = [];
  for (const match of content.matchAll(pattern)) {
    const line = content.slice(0, match.index).split("\n").length;
    addError(errors, `line ${line}`, "Obsidian wikilink must not point to .orbitos/");
  }
  return errors;
}

function walkMarkdown(fullPath, out = []) {
  if (!fs.existsSync(fullPath)) return out;
  const stat = fs.statSync(fullPath);
  if (stat.isDirectory()) {
    for (const item of fs.readdirSync(fullPath)) walkMarkdown(path.join(fullPath, item), out);
  } else if (fullPath.endsWith(".md")) {
    out.push(fullPath);
  }
  return out;
}

const wikilinkPattern = /\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]/g;
const sourceHeadingPattern = /^##\s*(?:来源|Source)\s*$/i;
const sourceLinkPattern = /\[\[[^\]]+\]\]|\[[^\]]+\]\([^)]+\)/;
const draftLifecyclePattern = /^lifecycle:\s*draft\s*$/im;
const activeLifecyclePattern = /^lifecycle:\s*active\s*$/im;
const legacyPatterns = [
  [/(?<!\w)\.orbit[\\/]/, "legacy .orbit/ path"],
  [/(?<![\w-])02-日记[\\/]/, "legacy 02-日记/ directory"],
  [/(?<![\w-])03-知识[\\/]/, "legacy 03-知识/ directory"],
  [/(?<![\w-])04-项目[\\/]/, "legacy 04-项目/ directory"],
];
const forbiddenStatements = [
  [/Hindsight\s+是\s+OrbitOS(?:\s*的)?(?:\s*运行)?\s*(?:必需项|必需依赖|事实底座)/i, "Hindsight is optional and must not be described as an OrbitOS dependency or fact base"],
  [/(?:`?02-时间线\/今日\.md`?|`?今日\.md`?)\s*是\s*项目(?:的)?(?:唯一)?状态源/i, "project STATUS.md, not 今日.md, is the project state source"],
  [/(?:`?\.orbitos\/logs\/events\/`?|Event)\s+是\s+(?:OrbitOS(?:\s*的)?\s*)?唯一事实底座/i, "events are operation evidence, not the only fact base"],
  [/Active knowledge\s*(?:可以|可)\s*直接(?:进行)?语义修改/i, "active knowledge must return to draft before semantic changes"],
];
const docConsistencyExcludePatterns = ["00-系统/agents/*.md", "AGENTS.md"];

function isDocConsistencyExcluded(filePath) {
  const rel = path.relative(root, filePath).replace(/\\/g, "/");
  return docConsistencyExcludePatterns.some((pattern) => {
    const regex = new RegExp(`^${pattern.replace(/\*/g, ".*")}$`);
    return regex.test(rel);
  });
}

function resolveWikilinkTarget(sourceFile, linkTarget) {
  const candidates = [
    path.join(path.dirname(sourceFile), linkTarget),
    path.join(path.dirname(sourceFile), `${linkTarget}.md`),
    path.join(root, linkTarget),
    path.join(root, `${linkTarget}.md`),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate) && fs.statSync(candidate).isFile()) ?? null;
}

function markdownLifecycle(fullPath) {
  if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) return null;
  const content = fs.readFileSync(fullPath, "utf8");
  if (draftLifecyclePattern.test(content)) return "draft";
  if (activeLifecyclePattern.test(content)) return "active";
  return null;
}

function knowledgeSourceErrors(fullPath) {
  if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) return [];
  if (path.basename(fullPath) === "MAP.md") return [];

  const content = fs.readFileSync(fullPath, "utf8");
  const lines = [];
  let inCodeBlock = false;
  for (const line of content.split("\n")) {
    if (line.trim().startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (!inCodeBlock) lines.push(line);
  }

  let sourceStart = null;
  for (const [index, line] of lines.entries()) {
    if (sourceHeadingPattern.test(line.trim())) {
      sourceStart = index;
      break;
    }
  }

  const errors = [];
  const rel = path.relative(root, fullPath);
  if (sourceStart === null) {
    addError(errors, rel, "knowledge file is missing a 来源 section");
    return errors;
  }

  const sourceLines = [];
  for (const line of lines.slice(sourceStart + 1)) {
    if (line.trim().startsWith("## ")) break;
    sourceLines.push(line);
  }

  const sourceText = sourceLines.join("\n");
  if (!sourceLinkPattern.test(sourceText)) {
    addError(errors, rel, "knowledge 来源 section must contain at least one traceable link");
  }

  if (markdownLifecycle(fullPath) === "active") {
    const inboxRoot = path.resolve(root, "01-收件箱");
    const ingestedRoot = path.resolve(root, "01-收件箱/已入库");
    for (const match of sourceText.matchAll(wikilinkPattern)) {
      const rawTarget = match[1].replace(/\\/g, "/");
      const target = rawTarget.startsWith("01-收件箱/")
        ? path.resolve(root, rawTarget)
        : path.resolve(path.dirname(fullPath), rawTarget);
      const targetWithinInbox = target === inboxRoot || target.startsWith(`${inboxRoot}${path.sep}`);
      const targetWithinIngested = target === ingestedRoot || target.startsWith(`${ingestedRoot}${path.sep}`);
      if (targetWithinInbox && !targetWithinIngested) {
        addError(errors, rel, "active knowledge must not cite raw inbox files outside 01-收件箱/已入库/");
        break;
      }
    }
  }

  return errors;
}

function checkDocumentConsistency(files) {
  const errors = [];
  for (const file of files) {
    if (isDocConsistencyExcluded(file)) continue;
    const content = fs.readFileSync(file, "utf8");
    let inCodeBlock = false;
    for (const [lineIdx, line] of content.split("\n").entries()) {
      if (line.trim().startsWith("```")) {
        inCodeBlock = !inCodeBlock;
        continue;
      }
      if (inCodeBlock) continue;
      for (const match of line.matchAll(wikilinkPattern)) {
        const linkTarget = match[1];
        if (linkTarget.startsWith(".orbitos/") || linkTarget.startsWith(".orbit/")) continue;
        if (resolveWikilinkTarget(file, linkTarget) === null) {
          addError(errors, `${path.relative(root, file)}:${lineIdx + 1}`, `target '${linkTarget}' not found`);
        }
      }
      for (const [pattern, detail] of legacyPatterns) {
        if (pattern.test(line)) addError(errors, `${path.relative(root, file)}:${lineIdx + 1}`, detail);
      }
      for (const [pattern, detail] of forbiddenStatements) {
        if (pattern.test(line)) addError(errors, `${path.relative(root, file)}:${lineIdx + 1}`, detail);
      }
    }
  }
  return errors;
}

const schemas = {
  event: readJsonLike(".orbitos/schemas/event.schema.yaml"),
  "ingest-batch": readJsonLike(".orbitos/schemas/ingest-batch.schema.yaml"),
  lifecycle: readJsonLike(".orbitos/schemas/lifecycle.schema.yaml"),
  "agent-registry": readJsonLike(".orbitos/schemas/agent-registry.schema.yaml"),
  "module-catalog": readJsonLike(".orbitos/schemas/module-catalog.schema.yaml"),
  "module-state": readJsonLike(".orbitos/schemas/module-state.schema.yaml"),
};

let failureCount = 0;
let caseCount = 0;

function printCase(name, expectedValid, errors) {
  const actualValid = errors.length === 0;
  if (actualValid !== expectedValid) failureCount += 1;
  const status = actualValid === expectedValid ? "PASS" : "FAIL";
  console.log(`${status} ${name}`);
  for (const error of errors) console.log(`  - ${error.path}: ${error.message}`);
}

function schemaNameForCase(name) {
  if (name.startsWith("ingest-batch.")) return "ingest-batch";
  if (name.startsWith("agent-registry.")) return "agent-registry";
  if (name.startsWith("event.")) return "event";
  if (name.startsWith("lifecycle.")) return "lifecycle";
  throw new Error(`Cannot infer schema for case: ${name}`);
}

const caseRoot = path.join(root, ".orbitos/evals/cases");
for (const name of fs.readdirSync(caseRoot).filter((item) => item.endsWith(".yaml")).sort()) {
  caseCount += 1;
  const schemaName = schemaNameForCase(name);
  const data = readJsonLike(`.orbitos/evals/cases/${name}`);
  const errors = [];
  validateValue(data, schemas[schemaName], "$", errors);
  if (schemaName === "lifecycle") validateLifecycle(data, errors);
  printCase(name, name.includes(".valid."), errors);
}

const markdownCaseRoot = path.join(root, ".orbitos/evals/markdown-link-boundary");
for (const name of fs.readdirSync(markdownCaseRoot).filter((item) => item.endsWith(".md")).sort()) {
  caseCount += 1;
  const errors = markdownInternalWikilinkErrors(path.join(markdownCaseRoot, name));
  printCase(name, name.includes(".valid."), errors);
}

const docConsistencyCaseRoot = path.join(root, ".orbitos/evals/doc-consistency");
for (const name of fs.readdirSync(docConsistencyCaseRoot).filter((item) => item.endsWith(".md")).sort()) {
  caseCount += 1;
  const errors = checkDocumentConsistency([path.join(docConsistencyCaseRoot, name)]);
  printCase(name, name.includes(".valid."), errors);
}

const knowledgeSourceCaseRoot = path.join(root, ".orbitos/evals/knowledge-source");
for (const name of fs.readdirSync(knowledgeSourceCaseRoot).filter((item) => item.endsWith(".md")).sort()) {
  caseCount += 1;
  const errors = knowledgeSourceErrors(path.join(knowledgeSourceCaseRoot, name));
  printCase(name, name.includes(".valid."), errors);
}

caseCount += 1;
const visibleFiles = [
  path.join(root, "AGENTS.md"),
  path.join(root, "README.md"),
  path.join(root, "README.zh-CN.md"),
  ...walkMarkdown(path.join(root, "00-系统")),
  ...walkMarkdown(path.join(root, "02-时间线")),
].filter((file) => fs.existsSync(file) && fs.statSync(file).isFile());
const visibleErrors = [];
for (const file of visibleFiles) {
  for (const error of markdownInternalWikilinkErrors(file)) {
    addError(visibleErrors, `${path.relative(root, file)} ${error.path}`, error.message);
  }
}
printCase("visible-markdown.no-internal-wikilinks", true, visibleErrors);

caseCount += 1;
const docConsistencyErrors = checkDocumentConsistency(visibleFiles);
printCase("visible-markdown.doc-consistency", true, docConsistencyErrors);

caseCount += 1;
const knowledgeSourceErrorsList = [];
const knowledgeRoot = path.join(root, "04-知识");
if (fs.existsSync(knowledgeRoot)) {
  for (const file of walkMarkdown(knowledgeRoot).filter((item) => path.basename(item) !== "MAP.md")) {
    for (const error of knowledgeSourceErrors(file)) {
      addError(knowledgeSourceErrorsList, error.path, error.message);
    }
  }
}
printCase("actual.knowledge-sources", true, knowledgeSourceErrorsList);

caseCount += 1;
const documentSemanticsErrors = [];
const documentSemanticsPath = path.join(root, ".orbitos/rules/core/document-semantics.md");
if (!fs.existsSync(documentSemanticsPath)) {
  addError(documentSemanticsErrors, ".orbitos/rules/core/document-semantics.md", "global document semantics rule is missing");
} else {
  const documentSemantics = fs.readFileSync(documentSemanticsPath, "utf8");
  for (const role of ["MAP.md", "README.md", "AGENTS.md", "STATUS.md", "ROADMAP.md", "CHANGELOG.md", "ADR"]) {
    if (!documentSemantics.includes(role)) {
      addError(documentSemanticsErrors, role, "fixed document role is missing from document semantics rule");
    }
  }
  for (const creationGateTerm of ["Markdown 创建门", "现有文件为什么不能承载", "路径、受众和生命周期", "等待用户确认"]) {
    if (!documentSemantics.includes(creationGateTerm)) {
      addError(documentSemanticsErrors, creationGateTerm, "generic Markdown creation gate is incomplete");
    }
  }
  if (!documentSemantics.includes("内部项目管理目录默认不创建")) {
    addError(documentSemanticsErrors, "README.md", "internal project directories must not require a README by default");
  }
  for (const mapBoundaryTerm of ["直属子目录", "一句话说明它是什么", "不下钻"]) {
    if (!documentSemantics.includes(mapBoundaryTerm)) {
      addError(documentSemanticsErrors, mapBoundaryTerm, "MAP navigation boundary is incomplete");
    }
  }
  for (const roadmapBoundaryTerm of ["总体状态", "其他跨会话小任务标注“临时事项”", "validation 和 event 证据", "CHANGELOG.md"]) {
    if (!documentSemantics.includes(roadmapBoundaryTerm)) {
      addError(documentSemanticsErrors, roadmapBoundaryTerm, "roadmap/status/changelog data flow is incomplete");
    }
  }
}
const rootAgents = fs.readFileSync(path.join(root, "AGENTS.md"), "utf8");
if (!rootAgents.includes("document-semantics.md")) {
  addError(documentSemanticsErrors, "AGENTS.md", "root Agent router does not expose document semantics rule");
}
const projectManagementPath = path.join(root, ".orbitos/rules/core/project-management.md");
if (!fs.existsSync(projectManagementPath)) {
  addError(documentSemanticsErrors, ".orbitos/rules/core/project-management.md", "shared project management rule is missing");
} else {
  const projectManagement = fs.readFileSync(projectManagementPath, "utf8");
  for (const projectTerm of ["用户只需自然提出任务", "当场完成且不需要下次继续的小修改", "需要跨会话继续的工作", "只有用户决定现在推进后", "禁止自动流转", "否则标注“临时事项”", "已验证项使用 `[x]`", "STATUS 与 ROADMAP 必须在同一次 Progress Sync 中保持一致", "`repo/` 保存实际产品或发布仓库"]) {
    if (!projectManagement.includes(projectTerm)) {
      addError(documentSemanticsErrors, projectTerm, "shared project management rule is incomplete");
    }
  }
}
const progressSyncPath = path.join(root, ".orbitos/workflows/progress-sync.md");
const progressSync = fs.existsSync(progressSyncPath) ? fs.readFileSync(progressSyncPath, "utf8") : "";
for (const syncTerm of ["用户不需要主动说出同步命令", "project-management.md", "不把 STATUS 自动提升为 ROADMAP"]) {
  if (!progressSync.includes(syncTerm)) {
    addError(documentSemanticsErrors, syncTerm, "Progress Sync does not enforce project task flow");
  }
}
if (!rootAgents.includes("project-management.md")) {
  addError(documentSemanticsErrors, "AGENTS.md", "root Agent router does not expose project management rule");
}
const thinkingRulePath = path.join(root, ".orbitos/rules/core/thinking.md");
const thinkingReferencePath = path.join(root, ".orbitos/rules/core/thinking-modes.md");
if (!fs.existsSync(thinkingRulePath)) {
  addError(documentSemanticsErrors, ".orbitos/rules/core/thinking.md", "core thinking rule is missing");
} else {
  const thinkingRule = fs.readFileSync(thinkingRulePath, "utf8");
  for (const term of ["thinking-modes.md", "思考模式启动选择", "回复 1 / 2 / 3", "直接做"]) {
    if (!thinkingRule.includes(term)) addError(documentSemanticsErrors, ".orbitos/rules/core/thinking.md", `core thinking rule is missing: ${term}`);
  }
}
if (!rootAgents.includes("思考模式启动选择")) {
  addError(documentSemanticsErrors, "AGENTS.md", "root Agent router does not require thinking selection");
}
if (!fs.existsSync(thinkingReferencePath)) {
  addError(documentSemanticsErrors, ".orbitos/rules/core/thinking-modes.md", "core thinking modes reference is missing");
} else {
  const thinkingReference = fs.readFileSync(thinkingReferencePath, "utf8");
  for (const mode of ["5W1H", "苏格拉底提问", "SWOT", "第一性原理", "反向推导", "金字塔原理", "六顶思考帽", "批判性思维"]) {
    if (!thinkingReference.includes(mode)) addError(documentSemanticsErrors, mode, "thinking modes reference is incomplete");
  }
}
printCase("actual.document-semantics", true, documentSemanticsErrors);

caseCount += 1;
const eventFilenameErrors = [];
const eventsRoot = path.join(root, ".orbitos/logs/events");
const eventFilenamePattern = /^20[0-9]{6}_[0-9]{6}_[a-z0-9]+(?:_[a-z0-9]+)*\.yaml$/;
const eventCutoff = "20260615";
if (fs.existsSync(eventsRoot)) {
  for (const item of fs.readdirSync(eventsRoot, { withFileTypes: true })) {
    if (item.isDirectory()) {
      addError(eventFilenameErrors, `.orbitos/logs/events/${item.name}`, "event directory must stay flat; date subdirectories are not allowed");
      continue;
    }
    if (!item.name.endsWith(".yaml")) continue;
    const dateText = item.name.slice(0, 8);
    if (/^[0-9]{8}$/.test(dateText) && dateText >= eventCutoff && !eventFilenamePattern.test(item.name)) {
      addError(eventFilenameErrors, `.orbitos/logs/events/${item.name}`, "event file name must match YYYYMMDD_HHMMSS_slug.yaml with lowercase snake_case");
    }
    if (item.name.startsWith("evt_")) {
      const embeddedDate = item.name.slice(4, 12);
      if (/^[0-9]{8}$/.test(embeddedDate) && embeddedDate >= eventCutoff) {
        addError(eventFilenameErrors, `.orbitos/logs/events/${item.name}`, "event file name must not include evt_ prefix");
      }
    }
  }
}
printCase("actual.event-filenames", true, eventFilenameErrors);

caseCount += 1;
const eventRecordErrors = [];
if (fs.existsSync(eventsRoot)) {
  for (const name of fs.readdirSync(eventsRoot).filter((item) => item.endsWith(".yaml")).sort()) {
    const content = fs.readFileSync(path.join(eventsRoot, name), "utf8").trimStart();
    if (!content.startsWith("{")) continue;
    try {
      const eventData = JSON.parse(content);
      validateValue(eventData, schemas.event, `$[${name}]`, eventRecordErrors);
      const thinking = eventData.thinking;
      if (thinking && typeof thinking === "object") {
        const modes = Array.isArray(thinking.modes) ? thinking.modes : [];
        if (thinking.outcome === "selected" && modes.length === 0) addError(eventRecordErrors, `$[${name}].thinking`, "selected thinking must include at least one mode");
        if (thinking.outcome === "bypassed" && modes.length > 0) addError(eventRecordErrors, `$[${name}].thinking`, "bypassed thinking must not include modes");
        if (JSON.stringify(eventData.thinking_modes ?? []) !== JSON.stringify(modes.map((item) => item.mode))) {
          addError(eventRecordErrors, `$[${name}].thinking_modes`, "thinking modes summary must match thinking details");
        }
      }
    } catch (error) {
      addError(eventRecordErrors, `.orbitos/logs/events/${name}`, `invalid JSON-compatible event: ${error.message}`);
    }
  }
}
printCase("actual.event-records", true, eventRecordErrors);

caseCount += 1;
const systemManualErrors = [];
const systemDir = path.join(root, "00-系统");
const requiredSystemManual = [
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
];
const legacySystemManual = ["MAP.md", "CONTEXT.md", "PRINCIPLES.md", "DATA-LIFECYCLE.md", "CHANGELOG.md"];
for (const name of requiredSystemManual) {
  if (!fs.existsSync(path.join(systemDir, name))) {
    addError(systemManualErrors, `00-系统/${name}`, "required numbered system manual page is missing");
  }
}
for (const name of legacySystemManual) {
  if (fs.existsSync(path.join(systemDir, name))) {
    addError(systemManualErrors, `00-系统/${name}`, "legacy system manual filename must not be restored");
  }
}
printCase("actual.system-manual", true, systemManualErrors);

caseCount += 1;
const handoffStructureErrors = [];
const requiredHandoffFiles = [
  "00-系统/agents/BOARD.md",
  ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md",
  ".orbitos/module-packages/collaboration/workflows/agent-handoff.md",
  ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md",
  ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md",
  ".orbitos/scripts/handoff-status.py",
  "00-系统/agents/handoff/archive/.gitkeep",
];
for (const relativePath of requiredHandoffFiles) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    addError(handoffStructureErrors, relativePath, "handoff structure file is missing");
  }
}
const handoffWorkflowPath = path.join(root, ".orbitos/module-packages/collaboration/workflows/agent-handoff.md");
if (fs.existsSync(handoffWorkflowPath)) {
  const handoffWorkflow = fs.readFileSync(handoffWorkflowPath, "utf8");
  for (const term of ["execution_mode=delegated", "handoff_status", "current_owner", "closed", "STATUS.md", "validation"]) {
    if (!handoffWorkflow.includes(term)) {
      addError(handoffStructureErrors, ".orbitos/module-packages/collaboration/workflows/agent-handoff.md", `handoff workflow is missing required term: ${term}`);
    }
  }
}
const pickupWorkflowPath = path.join(root, ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md");
if (fs.existsSync(pickupWorkflowPath)) {
  const pickupWorkflow = fs.readFileSync(pickupWorkflowPath, "utf8");
  for (const term of ["获取交接工作", "00-系统/agents/BOARD.md", "current_owner", "next_action", "不得要求用户提供路径"]) {
    if (!pickupWorkflow.includes(term)) {
      addError(handoffStructureErrors, ".orbitos/module-packages/collaboration/workflows/handoff-pickup.md", `handoff pickup workflow is missing required term: ${term}`);
    }
  }
}
const adapterWorkflowPath = path.join(root, ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md");
if (fs.existsSync(adapterWorkflowPath)) {
  const adapterWorkflow = fs.readFileSync(adapterWorkflowPath, "utf8");
  for (const term of ["$handoff", "操作系统临时目录", "agent-handoff.md", "handoff-pickup.md", "不得扫描系统临时目录"]) {
    if (!adapterWorkflow.includes(term)) {
      addError(handoffStructureErrors, ".orbitos/module-packages/collaboration/workflows/handoff-adapter.md", `handoff adapter is missing required term: ${term}`);
    }
  }
}
const rootAgentPath = path.join(root, "AGENTS.md");
if (fs.existsSync(rootAgentPath)) {
  const rootAgent = fs.readFileSync(rootAgentPath, "utf8");
  for (const term of [
    "交给另一位 Agent 继续",
    "$handoff",
    ".orbitos/modules/collaboration/workflows/handoff-adapter.md",
    "获取交接工作",
    ".orbitos/modules/collaboration/workflows/handoff-pickup.md",
  ]) {
    if (!rootAgent.includes(term)) {
      addError(handoffStructureErrors, "AGENTS.md", `handoff route is missing required term: ${term}`);
    }
  }
}
const activeHandoffRoot = path.join(root, "00-系统/agents/handoff");
const archiveHandoffRoot = path.join(activeHandoffRoot, "archive");
const openHandoffStatuses = new Set(["delegated", "working", "returned"]);
const frontmatter = (text) => Object.fromEntries([...text.matchAll(/^([a-z_]+):\s*(.*?)\s*$/gm)].map(([, key, value]) => [key, value]));
const activeHandoffNames = new Set();
if (fs.existsSync(activeHandoffRoot)) {
  for (const name of fs.readdirSync(activeHandoffRoot).filter((item) => item.endsWith(".md"))) {
    const relativePath = `00-系统/agents/handoff/${name}`;
    const metadata = frontmatter(fs.readFileSync(path.join(activeHandoffRoot, name), "utf8"));
    activeHandoffNames.add(name.slice(0, -3));
    if (!openHandoffStatuses.has(metadata.handoff_status)) addError(handoffStructureErrors, relativePath, "active handoff must use delegated, working, or returned status");
    if (!metadata.current_owner) addError(handoffStructureErrors, relativePath, "active handoff is missing current_owner");
    if (!metadata.return_owner) addError(handoffStructureErrors, relativePath, "active handoff is missing return_owner");
    if (!metadata.next_action) addError(handoffStructureErrors, relativePath, "active handoff is missing next_action");
  }
}
if (fs.existsSync(archiveHandoffRoot)) {
  for (const name of fs.readdirSync(archiveHandoffRoot).filter((item) => item.endsWith(".md"))) {
    const relativePath = `00-系统/agents/handoff/archive/${name}`;
    const metadata = frontmatter(fs.readFileSync(path.join(archiveHandoffRoot, name), "utf8"));
    if (metadata.handoff_status !== "closed") addError(handoffStructureErrors, relativePath, "archived handoff must use closed status");
  }
}
if (fs.existsSync(path.join(root, "00-系统/agents/BOARD.md"))) {
  const board = fs.readFileSync(path.join(root, "00-系统/agents/BOARD.md"), "utf8");
  const boardNames = new Set([...board.matchAll(/\[\[handoff\/([^|\]]+)/g)].map(([, name]) => name));
  if (boardNames.size !== activeHandoffNames.size || [...boardNames].some((name) => !activeHandoffNames.has(name))) addError(handoffStructureErrors, "00-系统/agents/BOARD.md", "current handoff links must match active handoff files");
  if (activeHandoffNames.size && (!board.includes("状态：") || !board.includes("当前负责人：") || !board.includes("下一步："))) addError(handoffStructureErrors, "00-系统/agents/BOARD.md", "current handoff entries must include status, owner, and next action");
}
printCase("actual.agent-handoff-structure", true, handoffStructureErrors);

caseCount += 1;
const machineLayerErrors = [];
if (fs.existsSync(path.join(root, ".orbitos/docs"))) {
  addError(machineLayerErrors, ".orbitos/docs", "runtime machine layer must not contain human-readable design docs");
}
printCase("actual.machine-layer-boundary", true, machineLayerErrors);

caseCount += 1;
const moduleErrors = [];
let moduleCatalog = { modules: {} };
let moduleState = { modules: {} };
const catalogPath = path.join(root, ".orbitos/module-catalog.json");
const moduleStatePath = path.join(root, ".orbitos/state/modules.json");
if (!fs.existsSync(catalogPath)) {
  addError(moduleErrors, ".orbitos/module-catalog.json", "module catalog is missing");
} else {
  moduleCatalog = readJsonLike(".orbitos/module-catalog.json");
  validateValue(moduleCatalog, schemas["module-catalog"], "$", moduleErrors);
}
if (!fs.existsSync(moduleStatePath)) {
  addError(moduleErrors, ".orbitos/state/modules.json", "module state registry is missing");
} else {
  moduleState = readJsonLike(".orbitos/state/modules.json");
  validateValue(moduleState, schemas["module-state"], "$", moduleErrors);
}
const catalogModules = moduleCatalog.modules ?? {};
const stateModules = moduleState.modules ?? {};
const legacyVisibleDomains = new Set((moduleState.legacy_visible_domains ?? []).filter((item) => item && typeof item === "object").map((item) => item.path));
for (const [moduleId, record] of Object.entries(stateModules)) {
  if (!hasOwn(catalogModules, moduleId)) {
    addError(moduleErrors, `.orbitos/state/modules.json:${moduleId}`, "state references an unknown module");
    continue;
  }
  const stateName = record?.state;
  const liveRoot = path.join(root, ".orbitos/modules", moduleId);
  if (["installed_disabled", "enabled_unconfigured", "ready", "blocked", "disabled"].includes(stateName) && !fs.existsSync(liveRoot)) {
    addError(moduleErrors, `.orbitos/modules/${moduleId}`, "installed module files are missing");
  }
  if (stateName === "ready") {
    for (const requiredPath of catalogModules[moduleId].required_paths ?? []) {
      if (!fs.existsSync(path.join(liveRoot, requiredPath))) {
        addError(moduleErrors, `.orbitos/modules/${moduleId}/${requiredPath}`, "ready module is missing a required file");
      }
    }
    for (const visiblePath of catalogModules[moduleId].visible_paths ?? []) {
      if (!fs.existsSync(path.join(root, visiblePath))) {
        addError(moduleErrors, visiblePath, "ready module is missing its visible domain");
      }
    }
  }
}
const liveModulesRoot = path.join(root, ".orbitos/modules");
if (fs.existsSync(liveModulesRoot)) {
  for (const item of fs.readdirSync(liveModulesRoot, { withFileTypes: true })) {
    if (item.isDirectory() && !hasOwn(stateModules, item.name)) {
      addError(moduleErrors, `.orbitos/modules/${item.name}`, "module files exist without a state entry");
    }
  }
}
if (fs.existsSync(path.join(root, "05-阅读")) && !["ready", "disabled"].includes(stateModules.reading?.state)) {
  addError(moduleErrors, "05-阅读", "reading domain exists but the reading module is not ready");
}
for (const reservedName of ["06-资源", "07-输出"]) {
  if (fs.existsSync(path.join(root, reservedName)) && !legacyVisibleDomains.has(reservedName)) {
    addError(moduleErrors, reservedName, "reserved domain has no installable module package");
  }
}
for (const legacyName of legacyVisibleDomains) {
  if (!fs.existsSync(path.join(root, legacyName))) {
    addError(moduleErrors, legacyName, "legacy visible-domain entry must be removed after its directory is gone");
  }
}
printCase("actual.module-state", true, moduleErrors);

caseCount += 1;
const runtimeTemplateErrors = [];
const requiredRuntimeTemplates = [
  ".orbitos/templates/.orbitos/agents/registry.yaml",
  ".orbitos/templates/.orbitos/state/modules.json",
  ".orbitos/templates/01-收件箱/00-粘贴.md",
  ".orbitos/templates/02-时间线/今日.md",
  ".orbitos/templates/02-时间线/本周.md",
  ".orbitos/templates/00-系统/agents/handoff/TEMPLATE.md",
];
for (const relativePath of requiredRuntimeTemplates) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    addError(runtimeTemplateErrors, relativePath, "required runtime template is missing");
  }
}
const registryTemplatePath = path.join(root, ".orbitos/templates/.orbitos/agents/registry.yaml");
if (fs.existsSync(registryTemplatePath)) {
  validateValue(readJsonLike(".orbitos/templates/.orbitos/agents/registry.yaml"), schemas["agent-registry"], "$", runtimeTemplateErrors);
}
printCase("actual.runtime-templates", true, runtimeTemplateErrors);

caseCount += 1;
const clipboardFlowErrors = [];
const clipboardWorkflowPath = path.join(root, ".orbitos/workflows/clipboard-flush.md");
if (!fs.existsSync(clipboardWorkflowPath)) {
  addError(clipboardFlowErrors, ".orbitos/workflows/clipboard-flush.md", "clipboard flush workflow is missing");
} else {
  const clipboardWorkflow = fs.readFileSync(clipboardWorkflowPath, "utf8");
  for (const term of ["00-粘贴.md", "物化", "删除", "确认", "inbox-triage.md", "inbox-ingest.md"]) {
    if (!clipboardWorkflow.includes(term)) addError(clipboardFlowErrors, ".orbitos/workflows/clipboard-flush.md", `clipboard workflow is missing required term: ${term}`);
  }
}
if (fs.existsSync(path.join(root, "AGENTS.md")) && !fs.readFileSync(path.join(root, "AGENTS.md"), "utf8").includes("处理粘贴内容")) {
  addError(clipboardFlowErrors, "AGENTS.md", "clipboard workflow route is missing");
}
const clipboardTemplatePath = path.join(root, ".orbitos/templates/01-收件箱/00-粘贴.md");
if (fs.existsSync(clipboardTemplatePath) && !fs.readFileSync(clipboardTemplatePath, "utf8").includes("整理粘贴内容")) {
  addError(clipboardFlowErrors, ".orbitos/templates/01-收件箱/00-粘贴.md", "clipboard template is missing its processing entry");
}
printCase("actual.clipboard-flow", true, clipboardFlowErrors);

caseCount += 1;
const inboxWorkflowErrors = [];
for (const [relativePath, terms] of Object.entries({
  ".orbitos/workflows/inbox-triage.md": ["single_source", "source_collection", "不按 PDF、图片、Markdown"],
  ".orbitos/workflows/inbox-ingest.md": ["single_source", "source_collection", "不创建全局", "00-粘贴.md"],
})) {
  const fullPath = path.join(root, relativePath);
  if (!fs.existsSync(fullPath)) {
    addError(inboxWorkflowErrors, relativePath, "inbox workflow is missing");
    continue;
  }
  const workflow = fs.readFileSync(fullPath, "utf8");
  for (const term of terms) {
    if (!workflow.includes(term)) addError(inboxWorkflowErrors, relativePath, `inbox workflow is missing required term: ${term}`);
  }
}
printCase("actual.inbox-storage-boundary", true, inboxWorkflowErrors);

caseCount += 1;
const ingestErrors = [];
const ingestDir = path.join(root, ".orbitos/ingest/batches");
const ingestedDir = path.join(root, "01-收件箱/已入库");
const recordedFiles = new Set();
if (fs.existsSync(ingestDir)) {
  for (const name of fs.readdirSync(ingestDir).filter((item) => item.endsWith(".yaml")).sort()) {
    const relative = `.orbitos/ingest/batches/${name}`;
    const batch = readJsonLike(relative);
    validateValue(batch, schemas["ingest-batch"], `$[${name}]`, ingestErrors);
    if (Array.isArray(batch.items)) {
      for (const item of batch.items) {
        if (typeof item.file === "string") {
          recordedFiles.add(item.file);
          const storedPath = path.join(ingestedDir, item.file);
          if (!fs.existsSync(storedPath)) addError(ingestErrors, `${relative}:${item.file}`, "batch item file does not exist in 01-收件箱/已入库/");
        }
      }
    }
  }
}
function walkFiles(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...walkFiles(fullPath));
    else if (entry.isFile()) files.push(fullPath);
  }
  return files;
}

if (fs.existsSync(ingestedDir)) {
  for (const filePath of walkFiles(ingestedDir)) {
    const relativePath = path.relative(ingestedDir, filePath).split(path.sep).join("/");
    if (relativePath === "00-粘贴.md") {
      addError(ingestErrors, "01-收件箱/已入库/00-粘贴.md", "00-粘贴.md must remain in the inbox root clipboard slot, not inside 已入库/");
    } else if (!recordedFiles.has(relativePath)) {
      addError(ingestErrors, `01-收件箱/已入库/${relativePath}`, "ingested file is missing an ingest batch record");
    }
  }
}
printCase("actual.ingest-batches", true, ingestErrors);

caseCount += 1;
const eventWriterErrors = [];
if (!fs.existsSync(path.join(root, ".orbitos/scripts/write_event.py"))) {
  addError(eventWriterErrors, ".orbitos/scripts/write_event.py", "event writer is missing");
}
printCase("actual.event-writer.exists", true, eventWriterErrors);

if (failureCount > 0) {
  console.log("");
  console.log(`Validation eval failed: ${failureCount} case(s).`);
  process.exit(1);
}

console.log("");
console.log(`Validation eval passed: ${caseCount} case(s).`);
