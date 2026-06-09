#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const WORKSPACES = [
  ["system", "00-系统", "workspace-system"],
  ["inbox", "01-收件箱", "workspace-inbox"],
  ["journal", "02-日记", "workspace-journal"],
  ["knowledge", "03-知识", "workspace-knowledge"],
  ["projects", "04-项目", "workspace-projects"],
  ["resources", "05-资源", "workspace-resources"],
  ["outputs", "06-输出", "workspace-outputs"],
  ["archive", "99-归档", "workspace-archive"],
];

const WORKSPACE_SUBDIRS = {
  "00-系统": ["规范", "Skills", "Agent", "Schema", "运行时", "审计"],
  "01-收件箱": ["网页剪藏", "临时想法", "待整理", "素材暂存"],
  "02-日记": ["每日", "工作日志", "反思", "复盘", "人际事件"],
  "03-知识": ["AI学科", "AI工具学习", "AI工程", "AI论文", "Harness工程", "上下文工程", "书籍笔记", "多Agent协作开发", "开发", "开发工具", "开源项目蒸馏", "认知神经科学"],
  "04-项目": ["内容创作", "产品系统", "运营增长", "商业合作", "研究验证", "实验原型"],
  "05-资源": ["CLI工具", "工作流", "模板", "附件", "图片", "人物档案"],
  "06-输出": ["文章", "口播稿", "视频脚本", "PPT", "发布稿"],
  "99-归档": ["迁移记录", "废弃系统", "废弃工具", "完结项目"],
};

const TYPE_DEFAULTS = {
  "01-收件箱": { type: "clipping", status: "draft", source: "obsidian-clipper", subdir: "待整理" },
  "02-日记": { type: "worklog", status: "active", source: "manual", subdir: "每日" },
  "03-知识": { type: "note", status: "active", source: "manual", subdir: "AI工程" },
  "04-项目": { type: "roadmap", status: "active", source: "manual", subdir: "产品系统" },
  "05-资源": { type: "note", status: "active", source: "manual", subdir: "模板" },
  "06-输出": { type: "article", status: "draft", source: "manual", subdir: "文章" },
  "99-归档": { type: "note", status: "archived", source: "manual", subdir: "迁移记录" },
};

const SUBSYSTEM_CONTRACTS = {
  system: {
    workspace: "00-系统",
    name: "System Control Plane",
    skill: "workspace-system",
    allowedStatus: ["active", "archived"],
    requiredFiles: ["WORKSPACE.md", "规范/07_自治子系统设计规范.md"],
    requiredDirs: WORKSPACE_SUBDIRS["00-系统"],
  },
  inbox: {
    workspace: "01-收件箱",
    name: "Intake Router",
    skill: "workspace-inbox",
    allowedStatus: ["draft", "processed", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: ["网页剪藏", "临时想法", "待整理", "素材暂存"],
  },
  journal: {
    workspace: "02-日记",
    name: "Timeline System",
    skill: "workspace-journal",
    allowedStatus: ["active", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: ["每日", "工作日志", "反思", "复盘", "人际事件"],
  },
  knowledge: {
    workspace: "03-知识",
    name: "Knowledge Memory",
    skill: "workspace-knowledge",
    allowedStatus: ["active", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: WORKSPACE_SUBDIRS["03-知识"],
  },
  projects: {
    workspace: "04-项目",
    name: "Project Runtime",
    skill: "workspace-projects",
    allowedStatus: ["active", "ready", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: WORKSPACE_SUBDIRS["04-项目"],
  },
  resources: {
    workspace: "05-资源",
    name: "Resource Library",
    skill: "workspace-resources",
    allowedStatus: ["active", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: WORKSPACE_SUBDIRS["05-资源"],
  },
  outputs: {
    workspace: "06-输出",
    name: "Publishing Pipeline",
    skill: "workspace-outputs",
    allowedStatus: ["draft", "ready", "published", "archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: WORKSPACE_SUBDIRS["06-输出"],
  },
  archive: {
    workspace: "99-归档",
    name: "Archive Ledger",
    skill: "workspace-archive",
    allowedStatus: ["archived"],
    requiredFiles: ["WORKSPACE.md"],
    requiredDirs: WORKSPACE_SUBDIRS["99-归档"],
  },
};

const PROJECT_CATEGORIES = {
  content: {
    label: "内容创作",
    directory: "内容创作",
    keywords: ["创作", "视频", "口播", "脚本", "分镜", "publish", "storyboard", "topic", "内容"],
  },
  product: {
    label: "产品系统",
    directory: "产品系统",
    keywords: ["MoonOS", "产品", "系统", "插件", "MCP", "CLI", "PRD", "spec", "harness", "Msg-Collect", "灵犀"],
  },
  operations: {
    label: "运营增长",
    directory: "运营增长",
    keywords: ["知识星球", "运营", "增长", "SOP", "用户地图", "内容矩阵", "数据看板", "变现"],
  },
  business: {
    label: "商业合作",
    directory: "商业合作",
    keywords: ["商业", "合作", "客户", "代理商", "pricing", "线索", "变现", "报价", "声文智汇"],
  },
  research: {
    label: "研究验证",
    directory: "研究验证",
    keywords: ["调研", "研究", "验证", "方案", "探索", "spike", "评估"],
  },
  experiment: {
    label: "实验原型",
    directory: "实验原型",
    keywords: ["MVP", "原型", "实验", "试验", "AI童伴", "demo", "prototype"],
  },
};

const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

const INTENT_ROUTES = [
  {
    id: "dev_doc",
    patterns: ["开发文档", "技术方案", "部署", "架构", "接口", "SDK", "API", "工程文档"],
    workspace: "03-知识",
    subdir: "开发",
    type: "note",
    topic: "dev",
    status: "active",
    reason: "意图包含开发文档/技术方案语义，路由到长期技术知识。",
  },
  {
    id: "tool_doc",
    patterns: ["CLI", "工具", "命令", "脚本", "自动化"],
    workspace: "03-知识",
    subdir: "开发工具",
    type: "note",
    topic: "tools",
    status: "active",
    reason: "意图包含工具/命令/自动化语义，路由到开发工具知识。",
  },
  {
    id: "article",
    patterns: ["文章", "教程", "发布", "长文"],
    workspace: "06-输出",
    subdir: "文章",
    type: "article",
    topic: "writing",
    status: "draft",
    reason: "意图包含可发布文章语义，路由到输出工作区。",
  },
  {
    id: "voiceover",
    patterns: ["口播", "口播稿", "短视频文案"],
    workspace: "06-输出",
    subdir: "口播稿",
    type: "voiceover",
    topic: "writing",
    status: "draft",
    reason: "意图包含口播/短视频文案语义，路由到口播稿。",
  },
  {
    id: "worklog",
    patterns: ["工作日志", "日报", "记录今天"],
    workspace: "02-日记",
    subdir: "工作日志",
    type: "worklog",
    topic: "work",
    status: "active",
    skill: "worklog",
    reason: "意图包含工作日志语义，路由到日记工作区。",
  },
  {
    id: "lifeos_event",
    patterns: ["人际", "关系事件", "人物", "LifeOS", "lifeos", "事件复盘", "关系复盘"],
    workspace: "02-日记",
    subdir: "人际事件/事件",
    type: "event",
    topic: "life",
    status: "active",
    skill: "lifeos",
    reason: "意图包含人际关系、人物或事件复盘语义，路由到 LifeOS 人际事件。",
  },
];

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      args._.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function scriptFilePath() {
  return decodeURIComponent(new URL(import.meta.url).pathname);
}

function writeIfMissing(file, content) {
  if (fs.existsSync(file)) return false;
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, content, "utf8");
  return true;
}

function writeIfChanged(file, content, mode) {
  ensureDir(path.dirname(file));
  if (fs.existsSync(file) && fs.readFileSync(file, "utf8") === content) return false;
  fs.writeFileSync(file, content, mode ? { encoding: "utf8", mode } : "utf8");
  if (mode) fs.chmodSync(file, mode);
  return true;
}

function copyDir(source, target) {
  if (!fs.existsSync(source)) return { copied: 0 };
  ensureDir(target);
  let copied = 0;
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (["node_modules", "__pycache__", ".git"].includes(entry.name)) continue;
    const src = path.join(source, entry.name);
    const dst = path.join(target, entry.name);
    if (entry.isDirectory()) {
      copied += copyDir(src, dst).copied;
    } else if (entry.isFile()) {
      ensureDir(path.dirname(dst));
      fs.copyFileSync(src, dst);
      copied += 1;
    }
  }
  return { copied };
}

function nowString() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function dateString() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
}

function normalizeTitle(title) {
  const normalized = String(title || "")
    .trim()
    .replace(/[\\/:*?"<>|\s]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  if (!normalized) throw new Error("title is required");
  return normalized;
}

function locateWorkspaceByPath(cwd, vaultRoot) {
  const resolvedCwd = path.resolve(cwd);
  const resolvedRoot = path.resolve(vaultRoot);
  for (const [id, dir, skill] of WORKSPACES) {
    const workspacePath = path.join(resolvedRoot, dir);
    if (resolvedCwd === workspacePath || resolvedCwd.startsWith(`${workspacePath}${path.sep}`)) {
      return { id, dir, skill, path: workspacePath, workspaceDoc: path.join(workspacePath, "WORKSPACE.md") };
    }
  }
  return { id: "unknown", dir: "", skill: "orbit-vault", path: resolvedRoot, workspaceDoc: path.join(resolvedRoot, "AGENTS.md") };
}

function toVaultRelativePath(vaultRoot, targetPath) {
  const relativePath = path.relative(path.resolve(vaultRoot), path.resolve(targetPath));
  if (!relativePath || relativePath.startsWith("..") || path.isAbsolute(relativePath)) return "";
  return relativePath.split(path.sep).join("/");
}

function parseSimpleYamlScalar(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  return trimmed;
}

function readManagedPaths(vaultRoot) {
  const schemaPath = path.join(vaultRoot, ".orbit", "schema", "managed-paths.yaml");
  const result = { schemaPath, managedPaths: {}, fallback: {} };
  if (!fs.existsSync(schemaPath)) return result;
  const lines = fs.readFileSync(schemaPath, "utf8").split(/\r?\n/);
  let section = "";
  let currentPath = "";
  let currentListKey = "";
  for (const rawLine of lines) {
    const line = rawLine.replace(/\s+#.*$/, "");
    if (!line.trim() || line.trim().startsWith("#")) continue;
    const topMatch = line.match(/^([A-Za-z0-9_-]+):\s*$/);
    if (topMatch) {
      section = topMatch[1];
      currentPath = "";
      currentListKey = "";
      continue;
    }
    if (section === "managed_paths") {
      const pathMatch = line.match(/^  ["']?([^"':]+(?:\/[^"':]+)*)["']?:\s*$/);
      if (pathMatch) {
        currentPath = pathMatch[1];
        result.managedPaths[currentPath] = { path: currentPath };
        currentListKey = "";
        continue;
      }
      const keyMatch = line.match(/^    ([A-Za-z0-9_-]+):\s*(.*)$/);
      if (currentPath && keyMatch) {
        const key = keyMatch[1];
        const value = keyMatch[2];
        if (!value) {
          result.managedPaths[currentPath][key] = [];
          currentListKey = key;
        } else {
          result.managedPaths[currentPath][key] = parseSimpleYamlScalar(value);
          currentListKey = "";
        }
        continue;
      }
      const itemMatch = line.match(/^      -\s*(.*)$/);
      if (currentPath && currentListKey && itemMatch) {
        result.managedPaths[currentPath][currentListKey].push(parseSimpleYamlScalar(itemMatch[1]));
      }
    } else if (section === "fallback") {
      const fallbackMatch = line.match(/^  ([A-Za-z0-9_-]+):\s*(.*)$/);
      if (fallbackMatch) result.fallback[fallbackMatch[1]] = parseSimpleYamlScalar(fallbackMatch[2]);
    }
  }
  return result;
}

function locateManagedPath(vaultRoot, cwd, managedPaths) {
  const relativeCwd = toVaultRelativePath(vaultRoot, cwd);
  let best = null;
  for (const [managedPath, rule] of Object.entries(managedPaths || {})) {
    if (relativeCwd === managedPath || relativeCwd.startsWith(`${managedPath}/`)) {
      if (!best || managedPath.length > best.path.length) best = rule;
    }
  }
  return best;
}

function yamlList(items) {
  return `[${items.map((item) => `"${String(item).replaceAll('"', '\\"')}"`).join(", ")}]`;
}

function yamlScalar(value) {
  if (Array.isArray(value)) return yamlList(value);
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return `"${String(value ?? "").replaceAll('"', '\\"')}"`;
}

function buildFrontmatter(meta) {
  const tags = meta.tags?.length ? meta.tags : [meta.topic, meta.type, meta.status].filter(Boolean);
  const lines = [
    "---",
    `title: "${meta.title}"`,
    `type: "${meta.type}"`,
    `topic: "${meta.topic}"`,
    `workspace: "${meta.workspace}"`,
    `created: "${meta.created}"`,
    `modified: "${meta.modified}"`,
    `tags: ${yamlList(tags)}`,
    `source: "${meta.source}"`,
    `status: "${meta.status}"`,
  ];
  for (const [key, value] of Object.entries(meta.extra || {})) {
    if (value !== undefined && value !== null && value !== "") lines.push(`${key}: ${yamlScalar(value)}`);
  }
  lines.push("---", "");
  return lines.join("\n");
}

function stripFrontmatter(markdown) {
  if (!markdown.startsWith("---\n")) return markdown;
  const end = markdown.indexOf("\n---", 4);
  if (end === -1) return markdown;
  return markdown.slice(end + 5).replace(/^\n+/, "");
}

function parseFrontmatter(markdown) {
  if (!markdown.startsWith("---\n")) return { meta: {}, body: markdown };
  const end = markdown.indexOf("\n---", 4);
  if (end === -1) return { meta: {}, body: markdown };
  const raw = markdown.slice(4, end);
  const body = markdown.slice(end + 5).replace(/^\n+/, "");
  const meta = {};
  for (const line of raw.split("\n")) {
    const match = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!match) continue;
    const [, key, value] = match;
    meta[key] = value.trim().replace(/^"(.*)"$/, "$1");
  }
  return { meta, body };
}

function uniquePath(target) {
  if (!fs.existsSync(target)) return target;
  const dir = path.dirname(target);
  const ext = path.extname(target);
  const base = path.basename(target, ext);
  for (let i = 2; i < 1000; i += 1) {
    const candidate = path.join(dir, `${base}_${i}${ext}`);
    if (!fs.existsSync(candidate)) return candidate;
  }
  throw new Error(`cannot find unique path for ${target}`);
}

function parseFluxFilename(file) {
  const base = path.basename(file, path.extname(file));
  const match = base.match(/^([^_]+)_(\d{8})(?:_(\d{6}))?_(.+)$/);
  if (!match) {
    return {
      sourcePrefix: "flux",
      date: dateString(),
      created: nowString(),
      title: base,
    };
  }
  const [, sourcePrefix, date, time, rest] = match;
  const created = `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)} ${time ? `${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}` : "00:00:00"}`;
  return { sourcePrefix, date, created, title: rest };
}

function rewriteFluxAssetLinks(markdown) {
  return markdown.replaceAll("(assets/images/", "(../../05-资源/图片/flux-intake-assets/");
}

function migrateFluxIntake(args = {}) {
  const resolved = resolveVault(args);
  const vaultRoot = resolved.vaultRoot;
  const dryRun = Boolean(args["dry-run"]);
  const sourceRoot = path.join(vaultRoot, "flux", "intake");
  const sourceAssets = path.join(sourceRoot, "assets", "images");
  const targetInbox = path.join(vaultRoot, "01-收件箱", "网页剪藏");
  const targetAssets = path.join(vaultRoot, "05-资源", "图片", "flux-intake-assets");
  const targetData = path.join(vaultRoot, "05-资源", "附件", "flux-intake-data");
  const manifestDir = path.join(vaultRoot, ".orbit", "manifests");
  const reportPath = path.join(manifestDir, `${dateString()}_flux-intake-migration.json`);
  const markdownFiles = fs.existsSync(sourceRoot)
    ? fs.readdirSync(sourceRoot).filter((name) => name.endsWith(".md")).map((name) => path.join(sourceRoot, name))
    : [];
  const dataFiles = fs.existsSync(sourceRoot)
    ? fs.readdirSync(sourceRoot, { withFileTypes: true })
      .filter((entry) => entry.isFile() && !entry.name.endsWith(".md"))
      .map((entry) => path.join(sourceRoot, entry.name))
    : [];
  const assetFiles = fs.existsSync(sourceAssets)
    ? fs.readdirSync(sourceAssets, { withFileTypes: true }).filter((entry) => entry.isFile()).map((entry) => path.join(sourceAssets, entry.name))
    : [];
  const moves = [];

  for (const asset of assetFiles) {
    const target = uniquePath(path.join(targetAssets, path.basename(asset)));
    moves.push({ type: "asset", source: path.relative(vaultRoot, asset), target: path.relative(vaultRoot, target) });
    if (!dryRun) {
      ensureDir(path.dirname(target));
      fs.renameSync(asset, target);
    }
  }

  for (const file of dataFiles) {
    const target = uniquePath(path.join(targetData, path.basename(file)));
    moves.push({ type: "data", source: path.relative(vaultRoot, file), target: path.relative(vaultRoot, target) });
    if (!dryRun) {
      ensureDir(path.dirname(target));
      fs.renameSync(file, target);
    }
  }

  for (const file of markdownFiles) {
    const parsedName = parseFluxFilename(file);
    const original = fs.readFileSync(file, "utf8");
    const { meta, body } = parseFrontmatter(original);
    const title = meta.title || parsedName.title;
    const filename = `${parsedName.date}_${normalizeTitle(title)}.md`;
    const target = uniquePath(path.join(targetInbox, filename));
    const oldTags = meta.tags ? Array.from(meta.tags.matchAll(/"([^"]+)"|'([^']+)'|([\u4e00-\u9fa5A-Za-z0-9_-]+)/g)).map((m) => m[1] || m[2] || m[3]).filter((tag) => tag !== "tags") : [];
    const frontmatter = buildFrontmatter({
      title,
      type: "clipping",
      topic: meta.topic || "intake",
      workspace: "01-收件箱",
      created: meta.created || parsedName.created,
      modified: nowString(),
      tags: Array.from(new Set([...oldTags, "flux-intake", "clipping", "draft"])),
      source: meta.source || parsedName.sourcePrefix || "web",
      status: "draft",
      extra: {
        url: meta.url,
        author: meta.author,
        publish_date: meta.publish_date,
        site_name: meta.site_name,
        site_type: meta.site_type,
        origin: meta.origin || "flux",
        original_status: meta.status,
        original_path: path.relative(vaultRoot, file),
      },
    });
    const rewritten = rewriteFluxAssetLinks(body);
    moves.push({ type: "markdown", source: path.relative(vaultRoot, file), target: path.relative(vaultRoot, target) });
    if (!dryRun) {
      ensureDir(path.dirname(target));
      fs.writeFileSync(target, `${frontmatter}${rewritten}`, "utf8");
      fs.unlinkSync(file);
    }
  }

  const result = {
    generatedAt: nowString(),
    vaultRoot,
    dryRun,
    source: "flux/intake",
    targetInbox: "01-收件箱/网页剪藏",
    targetAssets: "05-资源/图片/flux-intake-assets",
    targetData: "05-资源/附件/flux-intake-data",
    summary: {
      markdown: markdownFiles.length,
      assets: assetFiles.length,
      data: dataFiles.length,
      totalMoves: moves.length,
    },
    moves,
  };
  if (!dryRun) {
    ensureDir(manifestDir);
    fs.writeFileSync(reportPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
    result.manifestPath = reportPath;
    for (const maybeEmpty of [sourceAssets, path.join(sourceRoot, "assets"), sourceRoot]) {
      try {
        if (fs.existsSync(maybeEmpty) && fs.readdirSync(maybeEmpty).length === 0) fs.rmdirSync(maybeEmpty);
      } catch {
        // Keep non-empty legacy folders for later review.
      }
    }
  }
  return result;
}

function initVault(vaultRoot, args = {}) {
  let dirs = 0;
  let files = 0;
  for (const [, dir] of WORKSPACES) {
    const root = path.join(vaultRoot, dir);
    ensureDir(root);
    dirs += 1;
    for (const subdir of WORKSPACE_SUBDIRS[dir] || []) {
      ensureDir(path.join(root, subdir));
      dirs += 1;
    }
  }
  for (const dir of ["schema", "queues", "manifests", "reports", "data/lifeos"]) {
    ensureDir(path.join(vaultRoot, ".orbit", dir));
    dirs += 1;
  }
  ensureDir(path.join(vaultRoot, ".orbit", "events"));
  dirs += 1;
  files += writeIfMissing(path.join(vaultRoot, "AGENTS.md"), "# OrbitOS Agent 入口\n\n读取 `.orbit/workspace-index.yaml` 后按当前工作区规范执行。\n") ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, "CLAUDE.md"), "# OrbitOS Claude Code 入口\n\n先读 `AGENTS.md`、`.orbit/workspace-index.yaml`、`.orbit/schema/taxonomy.yaml` 和 `.orbit/schema/managed-paths.yaml`，再读取当前工作区的 `WORKSPACE.md`。\n") ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, "README.md"), "# OrbitOS 知识库\n\n中文管理、扁平工作区、Agent-native 的知识库。\n") ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "workspace-index.yaml"), renderWorkspaceIndex(vaultRoot)) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "taxonomy.yaml"), renderTaxonomySchema()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "managed-paths.yaml"), renderManagedPathsSchema()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "event-log.yaml"), renderEventLogSchema()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "project-taxonomy.yaml"), renderProjectTaxonomy()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "subsystems.yaml"), renderSubsystemContracts()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "event-capture.yaml"), renderEventCaptureSchema()) ? 1 : 0;
  files += writeIfMissing(path.join(vaultRoot, ".orbit", "schema", "workspace-tools.yaml"), renderWorkspaceToolsSchema()) ? 1 : 0;
  const skills = ensureCanonicalSkills(vaultRoot, args);
  const runtime = syncRuntimeTemplates({ vault: vaultRoot });
  for (const [, dir, skill] of WORKSPACES) {
    files += writeIfMissing(path.join(vaultRoot, dir, "WORKSPACE.md"), `# ${dir} 工作区规范\n\n## 子 Skill\n\n使用 \`${skill}\`。\n`) ? 1 : 0;
  }
  const result = { vaultRoot, dirsTouched: dirs, filesCreated: files, skills, runtime };
  if (args.installMachineRuntime || args.install_machine_runtime || args["install-machine-runtime"] || args.all) {
    result.installedRuntime = installMachineRuntime({ ...args, vault: vaultRoot, all: true });
  }
  return result;
}

function renderWorkspaceIndex(vaultRoot) {
  const lines = [
    `vault_root: "${vaultRoot}"`,
    'default_filename: "YYYYMMDD_主题.md"',
    'workspace_doc: "WORKSPACE.md"',
    "workspaces:",
  ];
  for (const [id, dir, skill] of WORKSPACES) {
    lines.push(`  ${id}:`);
    lines.push(`    path: "${dir}"`);
    lines.push(`    skill: "${skill}"`);
  }
  return `${lines.join("\n")}\n`;
}

function renderTaxonomySchema() {
  return [
    "# 合法 topic / type 列表",
    "# 供 Agent 校验 Frontmatter 时使用，路径无关。",
    "",
    "topic_values:",
    "  - ai",
    "  - dev",
    "  - reading",
    "  - work",
    "  - project",
    "  - tools",
    "  - writing",
    "  - life",
    "  - system",
    "",
    "type_values:",
    "  - note",
    "  - card",
    "  - article",
    "  - voiceover",
    "  - script",
    "  - review",
    "  - reflection",
    "  - worklog",
    "  - clipping",
    "  - study",
    "  - spec",
    "  - skill",
    "  - roadmap",
    "  - board",
    "  - event",
    "",
  ].join("\n");
}

function renderManagedPathsSchema() {
  return [
    'version: "1.0"',
    'description: "OrbitOS 高价值路径规则。只管理会改变 Agent 行为的子目录，普通子目录继承 WORKSPACE.md。"',
    "managed_paths:",
    '  "02-日记/工作日志":',
    '    reason: "Hook 和 Agent 事件写入目标，有固定章节。"',
    '    type: "worklog"',
    '    topic: "work"',
    '    status: "active"',
    '    skill: "worklog"',
    '    required_sections: ["今日重点", "今日Todo", "Git 提交", "重点记录", "关键决策", "问题与风险", "明日计划"]',
    '  "02-日记/复盘":',
    '    reason: "周期性回顾内容，结构和普通日记不同。"',
    '    type: "review"',
    '    topic: "work"',
    '    status: "active"',
    '    skill: "review"',
    '  "04-项目/内容创作":',
    '    reason: "内容生产项目，有发布、素材和复盘链路。"',
    '    type: "board"',
    '    topic: "writing"',
    '    status: "active"',
    '    skill: "workspace-projects"',
    '  "04-项目/产品系统":',
    '    reason: "产品和系统项目，默认承载规格、roadmap 和项目文档。"',
    '    type: "roadmap"',
    '    topic: "project"',
    '    status: "active"',
    '    skill: "workspace-projects"',
    '  "06-输出/文章":',
    '    reason: "可发布文章成品。"',
    '    type: "article"',
    '    topic: "writing"',
    '    status: "draft"',
    '    skill: "workspace-outputs"',
    '  "06-输出/口播稿":',
    '    reason: "可发布口播稿成品。"',
    '    type: "voiceover"',
    '    topic: "writing"',
    '    status: "draft"',
    '    skill: "workspace-outputs"',
    "fallback:",
    '  unknown_path: "inherit_workspace"',
    '  uncertain_route: "01-收件箱/待整理"',
    "",
  ].join("\n");
}

function renderEventLogSchema() {
  return [
    'version: "1.0"',
    'description: "OrbitOS raw event log schema. Files live at .orbit/events/YYYYMMDD.ndjson, one JSON object per line."',
    "common_required_fields:",
    '  - "event_id"',
    '  - "type"',
    '  - "timestamp"',
    '  - "actor_type"',
    '  - "actor_id"',
    '  - "recorded_via"',
    '  - "session_id"',
    "event_types:",
    "  git_commit:",
    '    required: ["origin_cwd", "repo", "repo_name", "branch", "commit", "commit_short", "subject", "files"]',
    "  agent_work:",
    '    required: ["summary", "origin_cwd"]',
    "  decision:",
    '    required: ["decision", "reason", "origin_cwd"]',
    "storage:",
    '  path_pattern: ".orbit/events/{YYYYMMDD}.ndjson"',
    '  git_policy: "ignored_local_runtime"',
    "",
  ].join("\n");
}

function renderProjectTaxonomy() {
  const lines = [
    "project_categories:",
  ];
  for (const [id, category] of Object.entries(PROJECT_CATEGORIES)) {
    lines.push(`  ${id}:`);
    lines.push(`    label: "${category.label}"`);
    lines.push(`    directory: "${category.directory}"`);
    lines.push(`    keywords: ${yamlList(category.keywords)}`);
  }
  lines.push("audit_policy:");
  lines.push("  high_confidence: 0.8");
  lines.push("  auto_move: false");
  lines.push("  require_trace_for_move: true");
  return `${lines.join("\n")}\n`;
}

function renderWorkspaceToolsSchema() {
  return [
    'version: "2026-05-24"',
    'description: "OrbitOS 工作区工具框架。根 Skill 负责解析和路由，工作区 Skill 负责自治，领域 Skill 按需加载。"',
    "root:",
    '  skill: "orbit-vault"',
    '  skill_root: "00-系统/Skills"',
    '  tools: ["resolve-vault", "locate-workspace", "explain-route", "create-routed-note", "ensure-daily-worklog", "record-agent-work-event", "record-git-commit-event", "sync-runtime-templates", "install-machine-runtime", "audit-workspaces", "audit-subsystems", "audit-skill-locations"]',
    "progressive_loading:",
    '  level_0_global: ["AGENTS.md", ".orbit/workspace-index.yaml", ".orbit/schema/taxonomy.yaml", ".orbit/schema/managed-paths.yaml", ".orbit/schema/subsystems.yaml", ".orbit/schema/event-capture.yaml", ".orbit/schema/event-log.yaml", ".orbit/schema/workspace-tools.yaml"]',
    '  level_1_workspace: ["<workspace>/WORKSPACE.md", "<workspace-skill>/SKILL.md"]',
    '  level_2_domain: "Only load domain skills when the intent or file type requires them."',
    "workspaces:",
    '  "01-收件箱": { workspace_skill: "workspace-inbox", domain_skills: ["knowledge", "video-collector"], tools: ["create-routed-note", "migrate-flux-intake", "build-intake-queue"], archived_legacy_sources: ["flux/intake", "flux/videos"] }',
    '  "02-日记": { workspace_skill: "workspace-journal", domain_skills: ["worklog", "reflect", "review", "lifeos"], legacy_sources: ["space/crafted/work"], archived_legacy_sources: ["space/crafted/lifeos"] }',
    '  "03-知识": { workspace_skill: "workspace-knowledge", domain_skills: ["knowledge", "harness-architect", "obsidian-canvas"] }',
    '  "04-项目": { workspace_skill: "workspace-projects", domain_skills: ["mvp-project", "ship-learn-next", "creation-tracking"] }',
    '  "05-资源": { workspace_skill: "workspace-resources", domain_skills: ["lifeos", "video-analyzer", "mkd2pic"], legacy_sources: ["space/templates", "space/workflow"], archived_legacy_sources: ["flux/intake/assets", "flux/lifeos/people.json"] }',
    '  "06-输出": { workspace_skill: "workspace-outputs", domain_skills: ["article", "video-analyzer", "huashu-slides"] }',
    '  "99-归档": { workspace_skill: "workspace-archive", domain_skills: [] }',
    "",
  ].join("\n");
}

function renderSubsystemContracts() {
  const lines = [
    'version: "2026-05-24"',
    'description: "OrbitOS 自治子系统契约。"',
    "subsystems:",
  ];
  for (const [id, contract] of Object.entries(SUBSYSTEM_CONTRACTS)) {
    lines.push(`  ${id}:`);
    lines.push(`    workspace: "${contract.workspace}"`);
    lines.push(`    name: "${contract.name}"`);
    lines.push(`    skill: "${contract.skill}"`);
    lines.push(`    allowed_status: ${yamlList(contract.allowedStatus)}`);
    lines.push(`    required_files: ${yamlList(contract.requiredFiles)}`);
    lines.push(`    required_dirs: ${yamlList(contract.requiredDirs)}`);
  }
  lines.push("audit_policy:");
  lines.push('  report_path: ".orbit/reports/YYYYMMDD_自治子系统审计.md"');
  lines.push('  queue_path: ".orbit/queues/subsystem-maintenance.yaml"');
  lines.push("  cross_workspace_move_requires_trace: true");
  return `${lines.join("\n")}\n`;
}

function renderEventCaptureSchema() {
  return [
    'version: "2026-05-24"',
    'description: "全局路由、Git Hook、Agent Hook 和工作日志事件采集契约。"',
    "vault_resolver:",
    '  order: ["walk_up:.orbit/workspace-index.yaml", "env:ORBIT_VAULT", "env:orbit_VAULT (deprecated)", "file:~/.orbit/config.yaml", "fallback:error (no hardcoded fallback)"]',
    "worklog:",
    '  path_template: "02-日记/工作日志/YYYYMMDD_工作日志_周X.md"',
    '  sections: ["今日重点", "今日Todo", "Git 提交", "重点记录", "关键决策", "问题与风险", "明日计划"]',
    "hook_policy:",
    '  git_hook: "post-commit"',
    "  overwrite_existing_hook: false",
    '  vault_runtime_root: "00-系统/运行时"',
    '  hook_template: "00-系统/运行时/hooks/global-post-commit.sh"',
    '  crontab_template: "00-系统/运行时/crontab/orbit-worklog.cron"',
    '  automation_spec: "00-系统/运行时/automations/codex-orbit-worklog.yaml"',
    "",
  ].join("\n");
}

function runtimeRoot(vaultRoot) {
  return path.join(vaultRoot, "00-系统", "运行时");
}

function skillRoot(vaultRoot) {
  return path.join(vaultRoot, "00-系统", "Skills");
}

function sourceSkillRoot() {
  return path.resolve(path.dirname(scriptFilePath()), "..", "..");
}

function ensureCanonicalSkills(vaultRoot, args = {}) {
  const source = sourceSkillRoot();
  const target = skillRoot(vaultRoot);
  if (path.resolve(source) === path.resolve(target)) {
    ensureDir(target);
    return { source, target, status: "already-canonical", copied: 0 };
  }
  if (fs.existsSync(path.join(target, "orbit-vault", "SKILL.md")) && !args.refreshSkills && !args.refresh_skills) {
    return { source, target, status: "already-exists", copied: 0 };
  }
  const { copied } = copyDir(source, target);
  return { source, target, status: "copied", copied };
}

function currentScriptPath(vaultRoot) {
  return path.join(skillRoot(vaultRoot), "orbit-vault", "scripts", "orbit-vault.mjs");
}

function renderGlobalPostCommitHook(vaultRoot) {
  const scriptPath = currentScriptPath(vaultRoot);
  return [
    "#!/bin/sh",
    "# OrbitOS portable global post-commit hook.",
    "# Source of truth: 00-系统/运行时/hooks/global-post-commit.sh",
    `VAULT="${vaultRoot}"`,
    `SCRIPT="${scriptPath}"`,
    'NODE_BIN="$(command -v node 2>/dev/null)"',
    '[ -n "$NODE_BIN" ] || exit 0',
    '[ -f "$SCRIPT" ] || exit 0',
    '[ -d "$VAULT" ] || exit 0',
    'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"',
    '"$NODE_BIN" "$SCRIPT" record-git-commit-event --vault "$VAULT" --repo "$REPO_ROOT" >/dev/null 2>&1 || true',
    "exit 0",
    "",
  ].join("\n");
}

function renderRepoPostCommitHook(vaultRoot) {
  const scriptPath = currentScriptPath(vaultRoot);
  return [
    "#!/bin/sh",
    "# OrbitOS portable repo post-commit hook.",
    "# Source of truth: 00-系统/运行时/hooks/repo-post-commit.sh",
    `VAULT="${vaultRoot}"`,
    `SCRIPT="${scriptPath}"`,
    'NODE_BIN="$(command -v node 2>/dev/null)"',
    '[ -n "$NODE_BIN" ] || exit 0',
    '[ -f "$SCRIPT" ] || exit 0',
    'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"',
    '"$NODE_BIN" "$SCRIPT" record-git-commit-event --vault "$VAULT" --repo "$REPO_ROOT" >/dev/null 2>&1 || true',
    "exit 0",
    "",
  ].join("\n");
}

function renderCrontabTemplate(vaultRoot) {
  const scriptPath = currentScriptPath(vaultRoot);
  return [
    "# OrbitOS daily worklog bootstrap.",
    "# Source of truth: 00-系统/运行时/crontab/OrbitOS-worklog.cron",
    "# Installed by: orbit-vault install-machine-runtime --crontab",
    `0 8 * * * /bin/zsh -lc 'node "${scriptPath}" ensure-daily-worklog --vault "${vaultRoot}" >/tmp/OrbitOS-worklog.log 2>&1'`,
    "",
  ].join("\n");
}

function renderCodexAutomationSpec(vaultRoot) {
  const scriptPath = currentScriptPath(vaultRoot);
  return [
    'name: "OrbitOS 每日工作日志初始化"',
    'kind: "cron"',
    'status: "ACTIVE"',
    'schedule: "daily 08:00 Asia/Shanghai"',
    `cwd: "${vaultRoot}"`,
    'execution_environment: "local"',
    'model: "gpt-5.2"',
    'reasoning_effort: "low"',
    "prompt: >-",
    `  Run node ${scriptPath} ensure-daily-worklog --vault ${vaultRoot}.`,
    "",
  ].join("\n");
}

function renderRuntimeReadme(vaultRoot) {
  return [
    "---",
    'workspace: "00-系统"',
    'type: "spec"',
    'topic: "runtime"',
    'status: "active"',
    'source: "agent"',
    "---",
    "",
    "# OrbitOS 运行时资产",
    "",
    "这里保存跨电脑迁移需要的运行时规格。Agent 应该把这里当成 hook、crontab、自动化任务的源头，而不是只依赖本机散落配置。",
    "",
    "## 目录",
    "",
    "- `hooks/`: Git hook 模板。",
    "- `crontab/`: crontab 模板。",
    "- `automations/`: Codex 或其他 Agent 平台的自动化任务规格。",
    "- `manifest.yaml`: 当前运行时资产索引。",
    "",
    "## 初始化",
    "",
    "Agent 在新机器上应调用：",
    "",
    "```bash",
    `node ${currentScriptPath(vaultRoot)} install-machine-runtime --vault ${vaultRoot} --all`,
    "```",
    "",
    "这会从 vault 内模板安装全局 Git hook，并注册每日工作日志 crontab。",
    "",
  ].join("\n");
}

function renderRuntimeManifest(vaultRoot) {
  return [
    'version: "2026-05-26"',
    'description: "OrbitOS 可迁移运行时资产索引。"',
    `vault_root: "${vaultRoot}"`,
    'skill_root: "00-系统/Skills"',
    'runtime_root: "00-系统/运行时"',
    "assets:",
    '  global_git_hook: "00-系统/运行时/hooks/global-post-commit.sh"',
    '  repo_git_hook: "00-系统/运行时/hooks/repo-post-commit.sh"',
    '  crontab: "00-系统/运行时/crontab/orbit-worklog.cron"',
    '  codex_automation: "00-系统/运行时/automations/codex-orbit-worklog.yaml"',
    "install:",
    '  command: "orbit-vault install-machine-runtime --all"',
    '  global_git_hooks_path: "~/.config/git/hooks"',
    '  crontab_marker: "OrbitOS DAILY WORKLOG"',
    "",
  ].join("\n");
}

function syncRuntimeTemplates(args = {}) {
  const vaultRoot = path.resolve(args.vault || resolveVault(args).vaultRoot);
  const root = runtimeRoot(vaultRoot);
  const files = [
    [path.join(root, "README.md"), renderRuntimeReadme(vaultRoot), null],
    [path.join(root, "manifest.yaml"), renderRuntimeManifest(vaultRoot), null],
    [path.join(root, "hooks", "global-post-commit.sh"), renderGlobalPostCommitHook(vaultRoot), 0o755],
    [path.join(root, "hooks", "repo-post-commit.sh"), renderRepoPostCommitHook(vaultRoot), 0o755],
    [path.join(root, "crontab", "orbit-worklog.cron"), renderCrontabTemplate(vaultRoot), null],
    [path.join(root, "automations", "codex-orbit-worklog.yaml"), renderCodexAutomationSpec(vaultRoot), null],
  ];
  let changed = 0;
  for (const [file, content, mode] of files) {
    if (writeIfChanged(file, content, mode)) changed += 1;
  }
  return { vaultRoot, runtimeRoot: root, files: files.map(([file]) => file), changed };
}

function installGlobalGitHook(vaultRoot, args = {}) {
  const home = process.env.HOME || "";
  if (!home) throw new Error("HOME is not set");
  const hookDir = path.join(home, ".config", "git", "hooks");
  const hookPath = path.join(hookDir, "post-commit");
  const content = renderGlobalPostCommitHook(vaultRoot);
  ensureDir(hookDir);
  if (fs.existsSync(hookPath)) {
    const existing = fs.readFileSync(hookPath, "utf8");
    const owned = existing.includes("OrbitOS portable global post-commit hook") || existing.includes("Global Git post-commit hook for OrbitOS");
    if (!owned && !args.force) {
      const sidecar = path.join(hookDir, "post-commit.orbit-vault");
      writeIfChanged(sidecar, content, 0o755);
      return { status: "sidecar-created-existing-hook-not-overwritten", hookPath: sidecar, hooksPath: hookDir };
    }
  }
  writeIfChanged(hookPath, content, 0o755);
  execFileSync("git", ["config", "--global", "core.hooksPath", hookDir], { encoding: "utf8" });
  return { status: "installed", hookPath, hooksPath: hookDir };
}

function installCrontab(vaultRoot) {
  const body = renderCrontabTemplate(vaultRoot).trim();
  const begin = "# BEGIN OrbitOS DAILY WORKLOG";
  const end = "# END OrbitOS DAILY WORKLOG";
  let current = "";
  try {
    current = execFileSync("crontab", ["-l"], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch {
    current = "";
  }
  const block = `${begin}\n${body}\n${end}`;
  const pattern = new RegExp(`${begin}[\\s\\S]*?${end}\\n?`, "m");
  const next = pattern.test(current)
    ? current.replace(pattern, `${block}\n`)
    : `${current.trim() ? `${current.trim()}\n\n` : ""}${block}\n`;
  execFileSync("crontab", ["-"], { input: next, encoding: "utf8" });
  return { status: pattern.test(current) ? "updated" : "installed", marker: "OrbitOS DAILY WORKLOG" };
}

function installMachineRuntime(args = {}) {
  const vaultRoot = path.resolve(args.vault || resolveVault(args).vaultRoot);
  const assets = syncRuntimeTemplates({ vault: vaultRoot });
  const installAll = args.all || (!args.globalHook && !args.global_hook && !args["global-hook"] && !args.crontab);
  const result = { vaultRoot, assets, installed: {} };
  if (installAll || args.globalHook || args.global_hook || args["global-hook"]) {
    result.installed.globalGitHook = installGlobalGitHook(vaultRoot, args);
  }
  if (installAll || args.crontab) {
    result.installed.crontab = installCrontab(vaultRoot);
  }
  return result;
}

function createFile(args) {
  const vaultRoot = path.resolve(args.vault || resolveVault(process.cwd()).vaultRoot);
  const workspace = args.workspace || locateWorkspaceByPath(args.cwd || process.cwd(), vaultRoot).dir || "01-收件箱";
  const defaults = TYPE_DEFAULTS[workspace] || TYPE_DEFAULTS["01-收件箱"];
  const title = args.title || args._[1];
  const topic = args.topic || "system";
  const type = args.type || defaults.type;
  const status = args.status || defaults.status;
  const source = args.source || defaults.source;
  const subdir = args.subdir || defaults.subdir || "";
  const created = args.created || nowString();
  const filename = args.filename || `${dateString()}_${normalizeTitle(title)}.md`;
  const targetDir = path.join(vaultRoot, workspace, subdir);
  const target = path.join(targetDir, filename);
  if (fs.existsSync(target) && !args.force) {
    throw new Error(`target exists: ${target}`);
  }
  const body = args.content || `# ${title}\n`;
  const frontmatter = buildFrontmatter({ title, type, topic, workspace, created, modified: created, tags: args.tags ? args.tags.split(",") : [], source, status });
  ensureDir(targetDir);
  fs.writeFileSync(target, `${frontmatter}${stripFrontmatter(body)}`, "utf8");
  return { path: target, workspace, type, topic, status };
}

function updateFrontmatter(args) {
  const file = path.resolve(args.file);
  const vaultRoot = path.resolve(args.vault || resolveVault(process.cwd()).vaultRoot);
  const current = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
  if (!current) throw new Error(`file not found or empty: ${file}`);
  const detected = locateWorkspaceByPath(path.dirname(file), vaultRoot);
  const title = args.title || path.basename(file, ".md").replace(/^\d{8}_/, "");
  const workspace = args.workspace || detected.dir || "01-收件箱";
  const defaults = TYPE_DEFAULTS[workspace] || TYPE_DEFAULTS["01-收件箱"];
  const created = args.created || nowString();
  const frontmatter = buildFrontmatter({
    title,
    type: args.type || defaults.type,
    topic: args.topic || "system",
    workspace,
    created,
    modified: nowString(),
    tags: args.tags ? args.tags.split(",") : [],
    source: args.source || defaults.source,
    status: args.status || defaults.status,
  });
  fs.writeFileSync(file, `${frontmatter}${stripFrontmatter(current)}`, "utf8");
  return { path: file, workspace };
}

function findVaultUpwards(cwd) {
  let current = path.resolve(cwd || process.cwd());
  while (true) {
    if (fs.existsSync(path.join(current, ".orbit", "workspace-index.yaml"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return "";
    current = parent;
  }
}

function readConfiguredVault() {
  const home = process.env.HOME || require("os").homedir();
  const config = path.join(home, ".orbit", "config.yaml");
  if (!fs.existsSync(config)) return "";
  const text = fs.readFileSync(config, "utf8");
  const match = text.match(/(?:vault_root|default_vault):\s*"?([^"\n]+)"?/);
  return match ? match[1].trim() : "";
}

function resolveVault(args = {}) {
  if (args.vault) return { vaultRoot: path.resolve(args.vault), source: "arg" };
  const cwd = path.resolve(args.cwd || process.cwd());
  const upward = findVaultUpwards(cwd);
  if (upward) return { vaultRoot: upward, source: "walk_up", cwd };
  const envVault = process.env.ORBIT_VAULT || process.env.orbit_VAULT;
  if (envVault) {
    const envRoot = path.resolve(envVault);
    if (fs.existsSync(path.join(envRoot, ".orbit", "workspace-index.yaml"))) {
      return { vaultRoot: envRoot, source: "env", cwd };
    }
  }
  const configured = readConfiguredVault();
  if (configured) return { vaultRoot: path.resolve(configured), source: "config", cwd };
  throw new Error("Cannot resolve vault root. Run from within a vault directory or set ORBIT_VAULT.");
}

function classifyIntentRoute(intent = "") {
  const normalized = String(intent || "");
  for (const route of INTENT_ROUTES) {
    if (route.patterns.some((pattern) => normalized.toLowerCase().includes(pattern.toLowerCase()))) {
      return route;
    }
  }
  return {
    id: "fallback",
    workspace: "01-收件箱",
    subdir: "待整理",
    type: "note",
    topic: "system",
    status: "draft",
    reason: "未匹配到高置信度意图，保守路由到收件箱待整理。",
  };
}

function workspaceByDir(dir) {
  const found = WORKSPACES.find(([, workspaceDir]) => workspaceDir === dir);
  if (!found) return null;
  const [id, workspaceDir, skill] = found;
  return {
    id,
    dir: workspaceDir,
    skill,
  };
}

function explainRoute(args) {
  const resolved = resolveVault(args);
  const vaultRoot = resolved.vaultRoot;
  const cwd = path.resolve(args.cwd || process.cwd());
  const intent = args.intent || args._[1] || "";
  const pathContext = locateWorkspaceByPath(cwd, vaultRoot);
  const managedSchema = readManagedPaths(vaultRoot);
  const managedPath = locateManagedPath(vaultRoot, cwd, managedSchema.managedPaths);
  const intentRoute = intent ? classifyIntentRoute(intent) : null;
  const highConfidenceIntent = Boolean(intentRoute && intentRoute.id !== "fallback");
  const managedWorkspace = managedPath ? workspaceByDir(managedPath.path.split("/")[0]) : null;
  const managedSubdir = managedPath ? managedPath.path.split("/").slice(1).join("/") : "";
  const workspaceDefaults = TYPE_DEFAULTS[pathContext.dir] || TYPE_DEFAULTS["01-收件箱"];
  const fallbackWorkspace = workspaceByDir("01-收件箱");
  let targetSource = "workspace";
  let targetWorkspace = pathContext.id === "unknown" ? fallbackWorkspace : workspaceByDir(pathContext.dir);
  let targetSubdir = workspaceDefaults.subdir;
  let targetType = workspaceDefaults.type;
  let targetTopic = "system";
  let targetStatus = workspaceDefaults.status;
  let targetSkill = targetWorkspace?.skill || "orbit-vault";

  if (managedPath && managedWorkspace) {
    targetSource = "managed-path";
    targetWorkspace = managedWorkspace;
    targetSubdir = managedSubdir;
    targetType = managedPath.type || targetType;
    targetTopic = managedPath.topic || targetTopic;
    targetStatus = managedPath.status || targetStatus;
    targetSkill = managedPath.skill || managedWorkspace.skill;
  }

  if (highConfidenceIntent) {
    const routeWorkspace = workspaceByDir(intentRoute.workspace);
    targetSource = "intent";
    targetWorkspace = routeWorkspace || targetWorkspace;
    targetSubdir = intentRoute.subdir;
    targetType = intentRoute.type;
    targetTopic = intentRoute.topic;
    targetStatus = intentRoute.status;
    targetSkill = intentRoute.skill || routeWorkspace?.skill || targetSkill;
  } else if (intentRoute && pathContext.id === "unknown" && !managedPath) {
    targetSource = "fallback";
    targetWorkspace = fallbackWorkspace;
    targetSubdir = intentRoute.subdir;
    targetType = intentRoute.type;
    targetTopic = intentRoute.topic;
    targetStatus = intentRoute.status;
    targetSkill = fallbackWorkspace.skill;
  }

  const explicit = {
    type: args.type,
    topic: args.topic,
    status: args.status,
    subdir: args.subdir,
  };
  if (explicit.subdir) targetSubdir = explicit.subdir;
  if (explicit.type) targetType = explicit.type;
  if (explicit.topic) targetTopic = explicit.topic;
  if (explicit.status) targetStatus = explicit.status;

  const matchedBy = ["vault"];
  if (pathContext.id !== "unknown") matchedBy.push("cwd-workspace");
  if (managedPath) matchedBy.push("managed-path");
  if (intent) matchedBy.push(highConfidenceIntent ? "intent" : "intent-fallback");
  if (Object.values(explicit).some(Boolean)) matchedBy.push("explicit-args");

  return {
    vaultRoot,
    resolver: resolved.source,
    cwd,
    relativeCwd: toVaultRelativePath(vaultRoot, cwd),
    workspace: pathContext,
    managedPath,
    intentRoute,
    effective: {
      source: targetSource,
      workspace: targetWorkspace?.dir || "01-收件箱",
      subdir: targetSubdir,
      type: targetType,
      topic: targetTopic,
      status: targetStatus,
      skill: targetSkill,
      targetDir: path.join(vaultRoot, targetWorkspace?.dir || "01-收件箱", targetSubdir || ""),
    },
    matchedBy,
    fallback: {
      intent: intentRoute?.id === "fallback",
      effective: targetSource === "fallback",
    },
    schema: {
      managedPaths: managedSchema.schemaPath,
      fallback: managedSchema.fallback,
    },
  };
}

function createRoutedNote(args) {
  const explanation = explainRoute(args);
  const vaultRoot = explanation.vaultRoot;
  const cwd = explanation.cwd;
  const intent = args.intent || args._[1] || "";
  const route = explanation.intentRoute || {
    id: explanation.effective.source,
    reason: `使用 ${explanation.effective.source} 规则确定落点。`,
  };
  const title = args.title || intent || "未命名记录";
  const created = args.created || nowString();
  const filename = args.filename || `${dateString()}_${normalizeTitle(title)}.md`;
  const targetDir = explanation.effective.targetDir;
  const target = path.join(targetDir, filename);
  if (fs.existsSync(target) && !args.force) throw new Error(`target exists: ${target}`);
  const result = {
    vaultRoot,
    resolver: explanation.resolver,
    route: route.id,
    reason: route.reason,
    routeSource: explanation.effective.source,
    matchedBy: explanation.matchedBy,
    path: target,
    workspace: explanation.effective.workspace,
    subdir: explanation.effective.subdir,
    type: explanation.effective.type,
    topic: explanation.effective.topic,
    status: explanation.effective.status,
    skill: explanation.effective.skill,
    dryRun: Boolean(args["dry-run"]),
  };
  if (args["dry-run"]) return result;
  const body = args.content || `# ${title}\n\n`;
  const frontmatter = buildFrontmatter({
    title,
    type: explanation.effective.type,
    topic: explanation.effective.topic,
    workspace: explanation.effective.workspace,
    created,
    modified: created,
    tags: args.tags ? args.tags.split(",") : [explanation.effective.topic, explanation.effective.type, route.id].filter(Boolean),
    source: args.source || "agent",
    status: explanation.effective.status,
    extra: {
      origin_cwd: cwd,
      route_intent: intent,
      route_reason: route.reason,
      route_id: route.id,
      route_source: explanation.effective.source,
      route_matched_by: explanation.matchedBy,
      route_skill: explanation.effective.skill,
    },
  });
  ensureDir(targetDir);
  fs.writeFileSync(target, `${frontmatter}${stripFrontmatter(body)}`, "utf8");
  return result;
}

function todayParts() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    compact: `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`,
    weekday: WEEKDAYS[d.getDay()],
    timestamp: nowString(),
  };
}

function worklogPath(vaultRoot, parts = todayParts()) {
  return path.join(vaultRoot, "02-日记", "工作日志", `${parts.compact}_工作日志_${parts.weekday}.md`);
}

function ensureDailyWorklog(args = {}) {
  const resolved = resolveVault(args);
  const vaultRoot = resolved.vaultRoot;
  const parts = todayParts();
  const file = worklogPath(vaultRoot, parts);
  if (fs.existsSync(file)) return { path: file, created: false, vaultRoot };
  const frontmatter = buildFrontmatter({
    title: `${parts.date} ${parts.weekday} 工作日志`,
    type: "worklog",
    topic: "work",
    workspace: "02-日记",
    created: parts.timestamp,
    modified: parts.timestamp,
    tags: ["worklog", "work", "event-capture"],
    source: "agent",
    status: "active",
  });
  const body = [
    `# ${parts.date} ${parts.weekday} 工作日志`,
    "",
    "## 今日重点",
    "",
    "## 今日Todo",
    "",
    "## Git 提交",
    "",
    "## 重点记录",
    "",
    "## 关键决策",
    "",
    "## 问题与风险",
    "",
    "## 明日计划",
    "",
  ].join("\n");
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, `${frontmatter}${body}`, "utf8");
  return { path: file, created: true, vaultRoot };
}

function appendToSection(markdown, section, content, eventId = "") {
  if (eventId && markdown.includes(eventId)) return { markdown, appended: false };
  const heading = `## ${section}`;
  const idx = markdown.indexOf(heading);
  if (idx === -1) return { markdown: `${markdown.trimEnd()}\n\n${heading}\n\n${content}\n`, appended: true };
  const nextIdx = markdown.indexOf("\n## ", idx + heading.length);
  const insertAt = nextIdx === -1 ? markdown.length : nextIdx;
  const before = markdown.slice(0, insertAt).trimEnd();
  const after = markdown.slice(insertAt);
  return { markdown: `${before}\n\n${content}\n${after}`, appended: true };
}

function detectActorId(args = {}) {
  return args.actor
    || args.actor_id
    || process.env.ORBIT_AGENT_ID
    || process.env.AGENT_ID
    || "unknown-agent";
}

function detectSessionId(args = {}) {
  return args.session_id
    || process.env.ORBIT_SESSION_ID
    || process.env.SESSION_ID
    || "unknown";
}

function detectRecordedVia(args = {}, fallback) {
  return args.recorded_via || args.via || fallback;
}

function appendEventToWorklog(vaultRoot, event) {
  const ensured = ensureDailyWorklog({ vault: vaultRoot });
  const file = ensured.path;
  let markdown = fs.readFileSync(file, "utf8");
  const section = event.section || (event.type === "git_commit" ? "Git 提交" : event.type === "decision" ? "关键决策" : "重点记录");
  const eventId = event.event_id || `${event.type}:${event.commit || event.timestamp}`;
  const eventRecord = { ...event, event_id: eventId };
  validateEventLogRecord(eventRecord);
  const content = formatEvent(event, eventId);
  const result = appendToSection(markdown, section, content, eventId);
  if (result.appended) {
    markdown = result.markdown.replace(/modified: ".*?"/, `modified: "${nowString()}"`);
    fs.writeFileSync(file, markdown, "utf8");
  }
  appendRawEvent(vaultRoot, eventRecord);
  return { path: file, appended: result.appended, eventId };
}

function validateEventLogRecord(event) {
  const common = ["event_id", "type", "timestamp", "actor_type", "actor_id", "recorded_via", "session_id"];
  const requiredByType = {
    git_commit: ["origin_cwd", "repo", "repo_name", "branch", "commit", "commit_short", "subject", "files"],
    agent_work: ["summary", "origin_cwd"],
    decision: ["decision", "reason", "origin_cwd"],
  };
  const required = [...common, ...(requiredByType[event.type] || [])];
  const missing = required.filter((field) => event[field] === undefined || event[field] === "");
  if (!requiredByType[event.type]) {
    throw new Error(`Unsupported event log type: ${event.type}`);
  }
  if (missing.length) {
    throw new Error(`Invalid event log record. Missing fields: ${missing.join(", ")}`);
  }
}

function appendRawEvent(vaultRoot, event) {
  const parts = todayParts();
  const eventFile = path.join(vaultRoot, ".orbit", "events", `${parts.compact}.ndjson`);
  ensureDir(path.dirname(eventFile));
  fs.appendFileSync(eventFile, `${JSON.stringify(event)}\n`, "utf8");
}

function formatEvent(event, eventId) {
  if (event.type === "git_commit") {
    const files = event.files?.length ? `；文件：${event.files.join(", ")}` : "";
    return `- ${event.timestamp} [${eventId}] \`${event.repo_name || event.repo}\` ${event.branch} ${event.commit_short}：${event.subject}${files}；记录方：\`${event.actor_id}\`；写入方式：\`${event.recorded_via}\``;
  }
  if (event.type === "decision") {
    const sessionId = event.session_id || "unknown";
    return [
      `### ${event.timestamp.slice(11, 16)} — ${event.decision}`,
      "",
      `- 记录ID：\`${eventId}\``,
      `- 记录方：\`${event.actor_id}\` (${event.actor_type})`,
      `- 写入方式：\`${event.recorded_via}\``,
      `- 会话ID：\`${sessionId}\``,
      `- 来源目录：\`${event.origin_cwd}\``,
      "",
      `**为什么做**：${event.reason}`,
      `**怎么做的**：形成并确认关键决策。`,
      `**改了什么**：记录决策结论。`,
    ].join("\n");
  }
  const sessionId = event.session_id || "unknown";
  const artifact = event.artifact || "未显式记录";
  return [
    `### ${event.timestamp.slice(11, 16)} — ${event.summary}`,
    "",
    `- 记录ID：\`${eventId}\``,
    `- 记录方：\`${event.actor_id}\` (${event.actor_type})`,
    `- 写入方式：\`${event.recorded_via}\``,
    `- 会话ID：\`${sessionId}\``,
    `- 来源目录：\`${event.origin_cwd}\``,
    "",
    `**为什么做**：${event.reason || "记录本次 Agent 产出。"}`,
    `**怎么做的**：${event.how || "基于当前会话与工作目录生成结构化记录。"}`,
    `**改了什么**：${artifact}`,
  ].join("\n");
}

function git(repo, args) {
  return execFileSync("git", ["-C", repo, ...args], { encoding: "utf8" }).trim();
}

function gitOptional(repo, args) {
  try {
    return git(repo, args);
  } catch {
    return "";
  }
}

function recordGitCommitEvent(args = {}) {
  const resolved = resolveVault(args);
  const repo = path.resolve(args.repo || args.cwd || process.cwd());
  const commit = args.commit || git(repo, ["rev-parse", "HEAD"]);
  const subject = git(repo, ["log", "-1", "--pretty=%s", commit]);
  const branch = git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]);
  const files = git(repo, ["show", "--pretty=", "--name-only", commit]).split("\n").filter(Boolean).slice(0, 20).map(decodeGitPath);
  const event = {
    type: "git_commit",
    timestamp: nowString(),
    actor_type: "automation",
    actor_id: detectActorId({ ...args, actor: args.actor || "git-hook" }),
    recorded_via: detectRecordedVia(args, "git-hook"),
    session_id: detectSessionId(args),
    origin_cwd: repo,
    repo,
    repo_name: path.basename(repo),
    branch,
    commit,
    commit_short: commit.slice(0, 7),
    subject,
    files,
  };
  return { vaultRoot: resolved.vaultRoot, ...appendEventToWorklog(resolved.vaultRoot, event), event };
}

function recordAgentWorkEvent(args = {}) {
  const resolved = resolveVault(args);
  const event = {
    type: args.decision ? "decision" : "agent_work",
    timestamp: nowString(),
    actor_type: args.actor_type || "agent",
    actor_id: detectActorId(args),
    recorded_via: detectRecordedVia(args, "record-agent-work-event"),
    session_id: detectSessionId(args),
    summary: args.summary || args._[1] || "Agent 产出记录",
    decision: args.decision || "",
    reason: args.reason || "",
    artifact: args.artifact || "",
    how: args.how || "",
    origin_cwd: path.resolve(args.cwd || process.cwd()),
    importance: args.importance || "normal",
  };
  return { vaultRoot: resolved.vaultRoot, ...appendEventToWorklog(resolved.vaultRoot, event), event };
}

function registerHooks(args = {}) {
  const repo = path.resolve(args.repo || args.cwd || process.cwd());
  const gitDir = git(repo, ["rev-parse", "--git-dir"]);
  const configuredHooksPath = gitOptional(repo, ["config", "--get", "core.hooksPath"]);
  const hookDir = configuredHooksPath
    ? (path.isAbsolute(configuredHooksPath) ? configuredHooksPath : path.join(repo, configuredHooksPath))
    : (path.isAbsolute(gitDir) ? path.join(gitDir, "hooks") : path.join(repo, gitDir, "hooks"));
  const hookPath = path.join(hookDir, "post-commit");
  const scriptPath = scriptFilePath();
  const nodePath = process.execPath;
  const vaultRoot = resolveVault(args).vaultRoot;
  const content = [
    "#!/bin/sh",
    "# orbit-vault post-commit hook",
    'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"',
    `"${nodePath}" "${scriptPath}" record-git-commit-event --vault "${vaultRoot}" --repo "$REPO_ROOT" >/dev/null 2>&1 || true`,
    "",
  ].join("\n");
  ensureDir(hookDir);
  if (fs.existsSync(hookPath)) {
    const existing = fs.readFileSync(hookPath, "utf8");
    if (existing.includes("orbit-vault post-commit hook")) {
      fs.writeFileSync(hookPath, content, { encoding: "utf8", mode: 0o755 });
      return { repo, hookPath, hooksPath: configuredHooksPath || ".git/hooks", status: "updated" };
    }
    const sidecar = path.join(hookDir, "post-commit.orbit-vault");
    fs.writeFileSync(sidecar, content, { encoding: "utf8", mode: 0o755 });
    return { repo, hookPath: sidecar, hooksPath: configuredHooksPath || ".git/hooks", status: "sidecar-created-existing-hook-not-overwritten" };
  }
  fs.writeFileSync(hookPath, content, { encoding: "utf8", mode: 0o755 });
  fs.chmodSync(hookPath, 0o755);
  return { repo, hookPath, hooksPath: configuredHooksPath || ".git/hooks", status: "installed" };
}

function auditSystem(vaultRoot) {
  const checks = [];
  const activeBad = [
    ["00-系统/Agent/CONTEXT.md", "旧全局上下文不应常驻 Agent 运行时"],
    ["00-系统/Agent/CURRENT_STATE.md", "旧状态文件需要归档或改为生成物"],
    ["00-系统/Agent/bootstrap.md", "旧 bootstrap 与新工作区模型冲突"],
    ["00-系统/Skills/legacy-prompts-migration.md", "旧 prompt 机制说明应归档"],
  ];
  for (const [relative, message] of activeBad) {
    const full = path.join(vaultRoot, relative);
    if (fs.existsSync(full)) checks.push({ severity: "warning", path: relative, message });
  }
  for (const relative of ["00-系统/WORKSPACE.md", "00-系统/Agent/README.md", "00-系统/Skills/README.md"]) {
    const full = path.join(vaultRoot, relative);
    checks.push({ severity: fs.existsSync(full) ? "ok" : "error", path: relative, message: fs.existsSync(full) ? "exists" : "missing" });
  }
  return checks;
}

function walkFiles(dir, maxDepth = 2, depth = 0) {
  if (!fs.existsSync(dir) || depth > maxDepth) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name === ".git") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkFiles(full, maxDepth, depth + 1));
    } else {
      files.push(full);
    }
  }
  return files;
}

function readProjectEvidence(projectDir) {
  const files = walkFiles(projectDir, 2).slice(0, 80);
  const names = files.map((file) => path.basename(file)).join(" ");
  const markdownSnippets = files
    .filter((file) => file.endsWith(".md"))
    .slice(0, 12)
    .map((file) => {
      try {
        return fs.readFileSync(file, "utf8").slice(0, 1200);
      } catch {
        return "";
      }
    })
    .join("\n");
  return `${projectDir}\n${names}\n${markdownSnippets}`;
}

function classifyProject(projectDir, currentCategory) {
  const base = path.basename(projectDir);
  const evidence = readProjectEvidence(projectDir);
  const normalizedEvidence = evidence.toLowerCase();
  const scores = {};
  const reasons = [];

  for (const [id, category] of Object.entries(PROJECT_CATEGORIES)) {
    let score = 0;
    for (const keyword of category.keywords) {
      const normalizedKeyword = keyword.toLowerCase();
      if (normalizedEvidence.includes(normalizedKeyword)) {
        score += 1;
      }
    }
    scores[id] = score;
  }

  const name = base.toLowerCase();
  if (base.includes("20260415_创作")) {
    scores.content += 8;
    reasons.push("项目名和内部结构指向内容创作流水线");
  }
  if (base.includes("知识星球")) {
    scores.operations += 8;
    reasons.push("项目名和文档包含知识星球运营语义");
  }
  if (base.includes("MoonOS") || base.includes("短视频创作者AI知识库")) {
    scores.product += 7;
    reasons.push("项目名指向软件/知识库产品系统");
  }
  if (base.includes("声文智汇")) {
    scores.business += 7;
    reasons.push("项目名和文档包含商业构想/客户线索语义");
  }
  if (base.includes("AI童伴") || name.includes("demo") || name.includes("mvp")) {
    scores.experiment += 5;
    reasons.push("项目名指向早期试验或原型，需要人工确认是否升级为产品系统");
  }

  if (currentCategory === "创作") scores.content += 1;
  if (currentCategory === "产品") scores.product += 1;
  if (currentCategory === "知识星球") scores.operations += 1;
  for (const [id, category] of Object.entries(PROJECT_CATEGORIES)) {
    if (currentCategory === category.directory) scores[id] += 2;
  }

  const ranked = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const [bestId, bestScore] = ranked[0];
  const [, secondScore] = ranked[1] || ["", 0];
  const category = PROJECT_CATEGORIES[bestId];
  const confidence = Math.max(0.45, Math.min(0.95, 0.55 + (bestScore - secondScore) * 0.08 + bestScore * 0.02));
  const targetPath = path.join("04-项目", category.directory, base);

  if (!reasons.length) {
    reasons.push(`关键词匹配 ${category.label}，但证据较少`);
  }

  return {
    project: base,
    currentPath: path.relative(path.dirname(path.dirname(projectDir)), projectDir).startsWith("..")
      ? projectDir
      : path.relative(process.cwd(), projectDir),
    currentCategory,
    suggestedType: bestId,
    suggestedCategory: category.label,
    suggestedPath: targetPath,
    confidence: Number(confidence.toFixed(2)),
    needsHumanConfirmation: confidence < 0.8,
    reasons,
    scores,
  };
}

function discoverProjectDirs(vaultRoot) {
  const projectsRoot = path.join(vaultRoot, "04-项目");
  if (!fs.existsSync(projectsRoot)) return [];
  const firstLevel = fs.readdirSync(projectsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
    .map((entry) => entry.name);
  const projectDirs = [];
  for (const category of firstLevel) {
    const categoryDir = path.join(projectsRoot, category);
    const children = fs.readdirSync(categoryDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."));
    for (const child of children) {
      projectDirs.push({ currentCategory: category, dir: path.join(categoryDir, child.name) });
    }
  }
  return projectDirs;
}

function renderProjectAuditMarkdown(audit) {
  const lines = [
    "# 04-项目 分类审计报告",
    "",
    `- 生成时间：${audit.generatedAt}`,
    `- 项目数：${audit.projects.length}`,
    `- 高置信度建议：${audit.summary.highConfidence}`,
    `- 需要人工确认：${audit.summary.needsHumanConfirmation}`,
    "",
    "## 建议表",
    "",
    "| 当前路径 | 建议分类 | 建议路径 | 置信度 | 人工确认 | 理由 |",
    "|---|---|---|---:|---|---|",
  ];
  for (const item of audit.projects) {
    lines.push(`| \`${item.currentPath}\` | ${item.suggestedCategory} | \`${item.suggestedPath}\` | ${item.confidence} | ${item.needsHumanConfirmation ? "需要" : "否"} | ${item.reasons.join("；")} |`);
  }
  lines.push("");
  lines.push("## 执行原则");
  lines.push("");
  lines.push("- 本报告只提供分类建议，不自动移动项目目录。");
  lines.push("- 低于 0.8 的建议必须人工确认。");
  lines.push("- 执行移动时只能移动完整项目目录，并写入 trace。");
  lines.push("- 复杂项目内部结构保留，不打散 `_assets/`、`research/`、`renders/`、`.codex/skills/`。");
  lines.push("");
  return `${lines.join("\n")}\n`;
}

function auditProjects(vaultRoot, args = {}) {
  const discovered = discoverProjectDirs(vaultRoot);
  const projects = discovered.map(({ dir, currentCategory }) => classifyProject(dir, currentCategory));
  const summary = {
    highConfidence: projects.filter((item) => item.confidence >= 0.8).length,
    needsHumanConfirmation: projects.filter((item) => item.needsHumanConfirmation).length,
  };
  const audit = {
    generatedAt: nowString(),
    taxonomy: "00-系统/规范/06_项目工作区分类治理规则.md",
    projects,
    summary,
  };
  if (args["write-report"]) {
    const reportPath = path.join(vaultRoot, ".orbit", "reports", `${dateString()}_04-项目_分类审计.md`);
    ensureDir(path.dirname(reportPath));
    fs.writeFileSync(reportPath, renderProjectAuditMarkdown(audit), "utf8");
    audit.reportPath = reportPath;
  }
  return audit;
}

function auditWorkspaces(vaultRoot, args = {}) {
  const checks = [];
  for (const [, dir] of WORKSPACES) {
    const root = path.join(vaultRoot, dir);
    const allowed = new Set(WORKSPACE_SUBDIRS[dir] || []);
    if (!fs.existsSync(root)) {
      checks.push({ severity: "error", path: dir, message: "workspace missing" });
      continue;
    }
    for (const subdir of allowed) {
      const full = path.join(root, subdir);
      checks.push({ severity: fs.existsSync(full) ? "ok" : "warning", path: path.join(dir, subdir), message: fs.existsSync(full) ? "exists" : "allowed subdir missing" });
    }
    const firstLevelDirs = fs.readdirSync(root, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
      .map((entry) => entry.name);
    for (const name of firstLevelDirs) {
      if (!allowed.has(name)) {
        checks.push({ severity: "warning", path: path.join(dir, name), message: "unexpected first-level directory" });
      }
    }
    if (dir !== "04-项目" && dir !== "99-归档") {
      for (const file of walkFiles(root, 8)) {
        const relative = path.relative(vaultRoot, file);
        const parts = relative.split(path.sep);
        const isAllowedLifeosNestedFile = dir === "02-日记"
          && parts[1] === "人际事件"
          && ["事件", "原始记录"].includes(parts[2])
          && parts.length === 4;
        const isAllowedResourceBundleFile = dir === "05-资源"
          && ((parts[1] === "图片" && parts[2] === "flux-intake-assets")
            || (parts[1] === "附件" && parts[2] === "flux-intake-data"))
          && parts.length === 4;
        const isAllowedSkillImplementationFile = dir === "00-系统" && parts[1] === "Skills";
        const isAllowedSystemRuntimeFile = dir === "00-系统" && parts[1] === "运行时";
        if (isAllowedLifeosNestedFile || isAllowedResourceBundleFile || isAllowedSkillImplementationFile || isAllowedSystemRuntimeFile) continue;
        if (parts.length > 3) {
          checks.push({ severity: "warning", path: relative, message: "active workspace file is deeper than one category level" });
        }
      }
    }
  }
  const audit = {
    generatedAt: nowString(),
    summary: {
      ok: checks.filter((item) => item.severity === "ok").length,
      warning: checks.filter((item) => item.severity === "warning").length,
      error: checks.filter((item) => item.severity === "error").length,
    },
    checks,
  };
  if (args["write-report"]) {
    const lines = [
      "# 全库工作区结构审计",
      "",
      `- 生成时间：${audit.generatedAt}`,
      `- OK：${audit.summary.ok}`,
      `- Warning：${audit.summary.warning}`,
      `- Error：${audit.summary.error}`,
      "",
      "| 级别 | 路径 | 信息 |",
      "|---|---|---|",
      ...checks.map((item) => `| ${item.severity} | \`${item.path}\` | ${item.message} |`),
      "",
    ];
    const reportPath = path.join(vaultRoot, ".orbit", "reports", `${dateString()}_全库工作区结构审计.md`);
    ensureDir(path.dirname(reportPath));
    fs.writeFileSync(reportPath, lines.join("\n"), "utf8");
    audit.reportPath = reportPath;
  }
  return audit;
}

function countMarkdownFiles(dir) {
  return walkFiles(dir, 20).filter((file) => {
    if (!file.endsWith(".md")) return false;
    if (file.includes(`${path.sep}00-系统${path.sep}Skills${path.sep}`)) return false;
    return true;
  }).length;
}

function countFilesMissingFrontmatter(dir) {
  return walkFiles(dir, 20).filter((file) => {
    if (!file.endsWith(".md")) return false;
    if (file.includes(`${path.sep}00-系统${path.sep}Skills${path.sep}`)) return false;
    try {
      return !fs.readFileSync(file, "utf8").startsWith("---\n");
    } catch {
      return false;
    }
  }).length;
}

function skillPathFor(vaultRoot, skillName) {
  return path.join(vaultRoot, "00-系统", "Skills", skillName, "SKILL.md");
}

function auditSkillLocations(vaultRoot, args = {}) {
  const canonicalRoot = skillRoot(vaultRoot);
  const checks = [];
  const allFiles = walkFiles(vaultRoot, 30);
  const skillFiles = allFiles.filter((file) => path.basename(file) === "SKILL.md");
  const scriptFiles = allFiles.filter((file) => file.split(path.sep).includes("scripts"));
  for (const file of skillFiles) {
    const relative = path.relative(vaultRoot, file);
    const inCanonicalRoot = file.startsWith(`${canonicalRoot}${path.sep}`);
    const inLegacy = relative.startsWith(`_legacy${path.sep}`);
    checks.push({
      severity: inCanonicalRoot || inLegacy ? "ok" : "warning",
      path: relative,
      message: inCanonicalRoot ? "canonical skill" : (inLegacy ? "legacy skill ignored" : "skill outside 00-系统/Skills"),
    });
  }
  for (const file of scriptFiles) {
    const relative = path.relative(vaultRoot, file);
    const inCanonicalRoot = file.startsWith(`${canonicalRoot}${path.sep}`);
    const inLegacy = relative.startsWith(`_legacy${path.sep}`);
    if (!inCanonicalRoot && !inLegacy) {
      checks.push({ severity: "warning", path: relative, message: "script outside canonical Skill root" });
    }
  }
  const audit = {
    generatedAt: nowString(),
    canonicalRoot,
    summary: {
      ok: checks.filter((item) => item.severity === "ok").length,
      warning: checks.filter((item) => item.severity === "warning").length,
      error: checks.filter((item) => item.severity === "error").length,
    },
    checks,
  };
  if (args["write-report"]) {
    const lines = [
      "# Skill 位置审计",
      "",
      `- 生成时间：${audit.generatedAt}`,
      `- Canonical root：\`${canonicalRoot}\``,
      `- OK：${audit.summary.ok}`,
      `- Warning：${audit.summary.warning}`,
      `- Error：${audit.summary.error}`,
      "",
      "| 级别 | 路径 | 信息 |",
      "|---|---|---|",
      ...checks.map((item) => `| ${item.severity} | \`${item.path}\` | ${item.message} |`),
      "",
    ];
    const reportPath = path.join(vaultRoot, ".orbit", "reports", `${dateString()}_Skill位置审计.md`);
    ensureDir(path.dirname(reportPath));
    fs.writeFileSync(reportPath, lines.join("\n"), "utf8");
    audit.reportPath = reportPath;
  }
  return audit;
}

function auditSubsystems(vaultRoot, args = {}) {
  const checks = [];
  const maintenanceItems = [];
  const schemaFiles = [
    ".orbit/workspace-index.yaml",
    ".orbit/schema/taxonomy.yaml",
    ".orbit/schema/managed-paths.yaml",
    ".orbit/schema/subsystems.yaml",
    ".orbit/schema/frontmatter.yaml",
    ".orbit/schema/event-capture.yaml",
    ".orbit/schema/event-log.yaml",
    ".orbit/schema/workspace-tools.yaml",
  ];

  for (const relative of schemaFiles) {
    const full = path.join(vaultRoot, relative);
    checks.push({ severity: fs.existsSync(full) ? "ok" : "error", subsystem: "root", path: relative, message: fs.existsSync(full) ? "control file exists" : "control file missing" });
  }

  for (const [id, contract] of Object.entries(SUBSYSTEM_CONTRACTS)) {
    const root = path.join(vaultRoot, contract.workspace);
    if (!fs.existsSync(root)) {
      const item = { severity: "error", subsystem: id, path: contract.workspace, message: "workspace missing" };
      checks.push(item);
      maintenanceItems.push(item);
      continue;
    }

    const skillFile = skillPathFor(vaultRoot, contract.skill);
    checks.push({ severity: fs.existsSync(skillFile) ? "ok" : "error", subsystem: id, path: skillFile, message: fs.existsSync(skillFile) ? "skill exists" : "skill missing" });

    for (const relative of contract.requiredFiles) {
      const full = path.join(root, relative);
      const item = { severity: fs.existsSync(full) ? "ok" : "warning", subsystem: id, path: path.join(contract.workspace, relative), message: fs.existsSync(full) ? "required file exists" : "required file missing" };
      checks.push(item);
      if (item.severity !== "ok") maintenanceItems.push(item);
    }

    for (const relative of contract.requiredDirs) {
      const full = path.join(root, relative);
      const item = { severity: fs.existsSync(full) ? "ok" : "warning", subsystem: id, path: path.join(contract.workspace, relative), message: fs.existsSync(full) ? "required directory exists" : "required directory missing" };
      checks.push(item);
      if (item.severity !== "ok") maintenanceItems.push(item);
    }

    const missingFrontmatter = countFilesMissingFrontmatter(root);
    const markdownCount = countMarkdownFiles(root);
    if (missingFrontmatter > 0) {
      const item = { severity: "warning", subsystem: id, path: contract.workspace, message: `${missingFrontmatter}/${markdownCount} markdown files missing frontmatter` };
      checks.push(item);
      maintenanceItems.push(item);
    } else {
      checks.push({ severity: "ok", subsystem: id, path: contract.workspace, message: `${markdownCount} markdown files have frontmatter or no markdown files` });
    }
  }

  const audit = {
    generatedAt: nowString(),
    summary: {
      ok: checks.filter((item) => item.severity === "ok").length,
      warning: checks.filter((item) => item.severity === "warning").length,
      error: checks.filter((item) => item.severity === "error").length,
      maintenanceItems: maintenanceItems.length,
    },
    checks,
  };

  if (args["write-report"]) {
    const reportPath = path.join(vaultRoot, ".orbit", "reports", `${dateString()}_自治子系统审计.md`);
    const lines = [
      "# 自治子系统审计",
      "",
      `- 生成时间：${audit.generatedAt}`,
      `- OK：${audit.summary.ok}`,
      `- Warning：${audit.summary.warning}`,
      `- Error：${audit.summary.error}`,
      `- 维护项：${audit.summary.maintenanceItems}`,
      "",
      "| 级别 | 子系统 | 路径 | 信息 |",
      "|---|---|---|---|",
      ...checks.map((item) => `| ${item.severity} | ${item.subsystem} | \`${item.path}\` | ${item.message} |`),
      "",
    ];
    ensureDir(path.dirname(reportPath));
    fs.writeFileSync(reportPath, lines.join("\n"), "utf8");
    audit.reportPath = reportPath;

    const queuePath = path.join(vaultRoot, ".orbit", "queues", "subsystem-maintenance.yaml");
    const queueLines = [
      `generated: "${audit.generatedAt}"`,
      "items:",
      ...maintenanceItems.map((item) => [
        `  - subsystem: "${item.subsystem}"`,
        `    severity: "${item.severity}"`,
        `    path: "${String(item.path).replaceAll('"', '\\"')}"`,
        `    message: "${String(item.message).replaceAll('"', '\\"')}"`,
      ].join("\n")),
      "",
    ];
    ensureDir(path.dirname(queuePath));
    fs.writeFileSync(queuePath, queueLines.join("\n"), "utf8");
    audit.queuePath = queuePath;
  }

  return audit;
}

function printHelp() {
  console.log(`orbit-vault commands:
  resolve-vault --cwd <path>
  locate-workspace --vault <path> --cwd <path>
  explain-route --vault <path> [--cwd <path>] [--intent <text>]
  init --vault <path> [--refresh-skills]
  init --vault <path> --install-machine-runtime [--refresh-skills]
  create --vault <path> --workspace <dir> --title <title> [--topic ai] [--type note] [--subdir AI工程]
  create-routed-note --intent <text> --title <title> [--cwd <path>] [--content <markdown>] [--dry-run]
  migrate-flux-intake [--vault <path>] [--dry-run]
  ensure-daily-worklog [--vault <path>]
  record-agent-work-event --summary <text> [--decision <text>] [--reason <text>] [--artifact <path>] [--cwd <path>]
  record-git-commit-event --repo <path> [--vault <path>]
  register-hooks --repo <path> [--vault <path>]
  sync-runtime-templates [--vault <path>]
  install-machine-runtime [--vault <path>] [--all] [--global-hook] [--crontab]
  update-frontmatter --file <path> [--vault <path>] [--topic ai] [--type note]
  audit-system --vault <path>
  audit-projects --vault <path> [--write-report]
  audit-workspaces --vault <path> [--write-report]
  audit-subsystems --vault <path> [--write-report]
  audit-skill-locations --vault <path> [--write-report]
`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const command = args._[0] || "help";
  const vaultRoot = path.resolve(args.vault || resolveVault(process.cwd()).vaultRoot);
  let result;
  if (command === "help") {
    printHelp();
    return;
  }
  if (command === "resolve-vault") result = resolveVault(args);
  else if (command === "locate-workspace") result = locateWorkspaceByPath(args.cwd || process.cwd(), vaultRoot);
  else if (command === "explain-route") result = explainRoute(args);
  else if (command === "init") result = initVault(vaultRoot, args);
  else if (command === "create") result = createFile(args);
  else if (command === "create-routed-note") result = createRoutedNote(args);
  else if (command === "migrate-flux-intake") result = migrateFluxIntake(args);
  else if (command === "ensure-daily-worklog") result = ensureDailyWorklog(args);
  else if (command === "record-agent-work-event") result = recordAgentWorkEvent(args);
  else if (command === "record-git-commit-event") result = recordGitCommitEvent(args);
  else if (command === "register-hooks") result = registerHooks(args);
  else if (command === "sync-runtime-templates") result = syncRuntimeTemplates(args);
  else if (command === "install-machine-runtime") result = installMachineRuntime(args);
  else if (command === "update-frontmatter") result = updateFrontmatter(args);
  else if (command === "audit-system") result = auditSystem(vaultRoot);
  else if (command === "audit-projects") result = auditProjects(vaultRoot, args);
  else if (command === "audit-workspaces") result = auditWorkspaces(vaultRoot, args);
  else if (command === "audit-subsystems") result = auditSubsystems(vaultRoot, args);
  else if (command === "audit-skill-locations") result = auditSkillLocations(vaultRoot, args);
  else throw new Error(`unknown command: ${command}`);
  console.log(JSON.stringify(result, null, 2));
}

function decodeGitPath(p) {
  if (p.startsWith('"') && p.endsWith('"')) {
    p = p.slice(1, -1);
    try {
      const bytes = [];
      for (let i = 0; i < p.length; i++) {
        if (p[i] === '\\') {
          i++;
          if (i >= p.length) {
            bytes.push(92); // trailing backslash
            break;
          }
          const next = p[i];
          if (/[0-7]/.test(next)) {
            const octalStr = p.slice(i, i + 3);
            if (/^[0-7]{3}$/.test(octalStr)) {
              bytes.push(parseInt(octalStr, 8));
              i += 2;
            } else {
              bytes.push(parseInt(next, 8));
            }
          } else {
            const escapeMap = {
              a: 7, b: 8, t: 9, n: 10, v: 11, f: 12, r: 13,
              '"': 34, '\\': 92
            };
            if (next in escapeMap) {
              bytes.push(escapeMap[next]);
            } else {
              bytes.push(92, next.charCodeAt(0));
            }
          }
        } else {
          bytes.push(p.charCodeAt(i));
        }
      }
      return Buffer.from(bytes).toString("utf8");
    } catch (e) {
      return p;
    }
  }
  return p;
}

main();
