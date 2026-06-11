---
title: Obsidian 写作规范
area: system
purpose: rule
lifecycle: active
created: 2026-06-11
updated: 2026-06-11
tags:
  - orbitos
  - obsidian
---

# Obsidian 写作规范

## Frontmatter

可见 Markdown 默认必须包含：

```yaml
---
title:
area:
purpose:
lifecycle:
created:
updated:
tags:
---
```

例外：

- `README.md` 和 `README.zh-CN.md` 面向 GitHub 首页展示，不要求 frontmatter。
- `01-收件箱/粘贴.md` 是自由输入入口，不要求格式。

## 三轴

- `area`: system / timeline / inbox / project / knowledge / resource / output / archive
- `purpose`: map / status / rule / workflow / record / knowledge / resource / output / review
- `lifecycle`: draft / active / reviewed / archived

## MAP

MAP 是区域导航，不写状态。默认不创建。

## STATUS

STATUS 是有生命周期对象的当前状态，不做导航。

建议结构：

```markdown
## 当前状态
## 最近变化
## 待确认
## 可继续
## 来源
```

## 正文

每个可见 Markdown 只承担一个职责。历史过程进入 event log、归档快照或 ADR。
