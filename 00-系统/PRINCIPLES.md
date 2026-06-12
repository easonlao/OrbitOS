---
title: 运行原则
area: system
purpose: rule
lifecycle: active
created: 2026-06-11
updated: 2026-06-12
tags:
  - orbitos
  - rules
---

# 运行原则

1. `AGENTS.md` 是唯一使用入口。
2. 任何 agent 进入 OrbitOS 后先执行 Startup Sync。
3. 实质性工作完成后执行 Progress Sync。
4. 只读取当前任务必要上下文，使用渐进式披露。
5. `.orbitos/logs/events/` 是事实底座。
6. 可见 Markdown 必须单一职责。
7. 人读层和机器层分离。
8. 知识区只收 confirmed / reviewed 内容，宁精不宜多。
9. Hindsight 是可选记忆增强层，不是核心依赖。
10. 修改系统内核前读取 `.orbitos/AGENTS.md`。
11. 讨论、设计和实现细节先进入 `.orbitos/docs/`；只有经过确认并改写成用户视角后，才进入 `00-系统/`。
