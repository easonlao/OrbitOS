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

  if (types.includes("object") && value !== null && typeof value === "object" && !Array.isArray(value)) {
    const properties = schema.properties ?? {};
    const required = schema.required ?? [];

    for (const name of required) {
      if (!hasOwn(value, name)) addError(errors, `${pathText}.${name}`, "missing required field");
    }

    if (schema.additionalProperties === false) {
      for (const name of Object.keys(value)) {
        if (!hasOwn(properties, name)) addError(errors, `${pathText}.${name}`, "additional property is not allowed");
      }
    }

    for (const name of Object.keys(properties)) {
      if (hasOwn(value, name)) validateValue(value[name], properties[name], `${pathText}.${name}`, errors);
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
  "inbox-triage": readJsonLike(".orbitos/schemas/inbox-triage.schema.yaml"),
  "ingest-batch": readJsonLike(".orbitos/schemas/ingest-batch.schema.yaml"),
  lifecycle: readJsonLike(".orbitos/schemas/lifecycle.schema.yaml"),
  "core-change": readJsonLike(".orbitos/schemas/core-change.schema.yaml"),
  "agent-registry": readJsonLike(".orbitos/schemas/agent-registry.schema.yaml"),
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
  if (name.startsWith("inbox-triage.")) return "inbox-triage";
  if (name.startsWith("agent-registry.")) return "agent-registry";
  if (name.startsWith("core-change.")) return "core-change";
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

caseCount += 1;
const visibleFiles = [
  path.join(root, "AGENTS.md"),
  path.join(root, "README.md"),
  path.join(root, "README.zh-CN.md"),
  ...walkMarkdown(path.join(root, "00-系统")),
  ...walkMarkdown(path.join(root, "02-时间线")),
];
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
const internalAgents = fs.readFileSync(path.join(root, ".orbitos/AGENTS.md"), "utf8");
if (!internalAgents.includes("document-semantics.md") || !internalAgents.includes("固定角色 Markdown")) {
  addError(documentSemanticsErrors, ".orbitos/AGENTS.md", "internal development router does not require document semantics for fixed-role Markdown");
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
if (!internalAgents.includes("project-management.md")) {
  addError(documentSemanticsErrors, ".orbitos/AGENTS.md", "internal rule index does not expose project management rule");
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
  "04-Agent协作.md",
  "05-安全与边界.md",
  "06-术语表.md",
  "07-系统变更.md",
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
const runtimeTemplateErrors = [];
const requiredRuntimeTemplates = [
  ".orbitos/templates/.orbitos/agents/registry.yaml",
  ".orbitos/templates/01-收件箱/00-粘贴.md",
  ".orbitos/templates/02-时间线/今日.md",
  ".orbitos/templates/02-时间线/本周.md",
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
if (fs.existsSync(ingestedDir)) {
  for (const item of fs.readdirSync(ingestedDir, { withFileTypes: true })) {
    if (item.isFile() && !recordedFiles.has(item.name)) {
      addError(ingestErrors, `01-收件箱/已入库/${item.name}`, "ingested file is missing an ingest batch record");
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
