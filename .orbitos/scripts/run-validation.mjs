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

const schemas = {
  event: readJsonLike(".orbitos/schemas/event.schema.yaml"),
  "inbox-triage": readJsonLike(".orbitos/schemas/inbox-triage.schema.yaml"),
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
const registryErrors = [];
validateValue(readJsonLike(".orbitos/agents/registry.yaml"), schemas["agent-registry"], "$", registryErrors);
printCase("actual.agent-registry", true, registryErrors);

if (failureCount > 0) {
  console.log("");
  console.log(`Validation eval failed: ${failureCount} case(s).`);
  process.exit(1);
}

console.log("");
console.log(`Validation eval passed: ${caseCount} case(s).`);
