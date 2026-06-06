---
workspace: "00-系统"
type: "spec"
topic: "system"
status: "active"
source: "agent"
---

# OrbitOS 运行时资产

这里保存跨电脑迁移需要的运行时规格。Agent 应该把这里当成 hook、crontab、自动化任务的源头，而不是只依赖本机散落配置。

## 目录

- `hooks/`：Git hook 模板。
- `crontab/`：crontab 模板。
- `automations/`：Codex 或其他 Agent 平台的自动化任务规格。
- `manifest.yaml`：当前运行时资产索引（路径无关，无硬编码绝对路径）。

## 初始化（新机器）

在 vault 根目录执行：

```bash
# 1. 解析 vault 根（如果不在 vault 内）
VAULT=$(node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs resolve-vault --cwd "$PWD")

# 2. 安装运行时（git hook + crontab）
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs install-runtime --vault "$VAULT" --all

# 3. 验收
ls "$VAULT/.orbit"
cat "$VAULT/.orbit/workspace-index.yaml"
```

`{SKILLS}` = OrbitOS skills 根目录（vault 内相对路径 `./00-系统/Skills`，即 `{VAULT}/00-系统/Skills`）。

## Obsidian 插件

插件随 vault 版本控制（`.obsidian/plugins/orbit-dashboard/`）。初始化后在 Obsidian 中：设置 → 第三方插件 → 启用 OrbitOS Dashboard。

## 规格引用

- `manifest.yaml`：资产索引 + 安装命令
- `{VAULT}/.orbit/schema/event-capture.yaml`：Agent 事件采集规格
- `{VAULT}/.orbit/schema/workspace-tools.yaml`：工作区→Skill 绑定
