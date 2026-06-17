# OrbitOS 设计

## 1. 顶层目录职责

| 路径 | 职责 | 是否为状态源 |
|---|---|---|
| `00-系统/` | 用户系统说明 | 否 |
| `01-收件箱/` | 临时输入与已入库原件 | 原件是内容证据 |
| `02-时间线/` | 今日、本周、待确认、下一步 | 否，属于聚合视图 |
| `03-项目/` | 项目内容和项目状态 | 项目 `STATUS.md` 是项目状态源 |
| `04-知识/` | 草稿与当前确认知识 | active knowledge 是当前认知来源 |
| `05-资源/` | 已识别、可引用资料 | 否 |
| `06-输出/` | Obsidian 内正式 Markdown 产物 | 产物自身是正式内容 |
| `99-归档/` | 已退出当前视野的对象 | 否 |
| `.orbitos/` | 控制面与机器运行记录 | event/ingest 对应各自事实 |

## 2. 收件箱设计

```text
01-收件箱/
  00-粘贴.md
  已入库/
```

- 收件箱根目录允许无格式输入。
- `00-粘贴.md` 是固定自由输入入口，数字前缀用于保证稳定显示在收件箱最前面，不要求 frontmatter。
- Triage 只盘点、聚类和提出建议，不移动文件。
- 用户确认处理后，原件移动到 `已入库/`，并写 ingest batch。
- 已入库不等于知识完成，只表示该原件已经处理过且不会被重复当作新输入。
- 知识转写不得修改已入库原件。

## 3. 知识设计

```text
04-知识/
  00-草稿箱/
  NN-主题/
```

### 3.1 草稿

- `lifecycle: draft`。
- 必须指向至少一个原始证据或已确认来源。
- 可以包含推测，但必须明确标注。
- 不作为当前确认知识被其他 agent 无条件引用。

### 3.2 Active Knowledge

- 用户确认后移出草稿箱并改为 `lifecycle: active`。
- 表达当前最可信综合理解，而不是复制原始材料。
- Active 文件不得直接进行语义修改。
- 需要补充结论、调整摘要、改变边界、合并内容或删除重要信息时，先把文件移回 `00-草稿箱/` 并改为 `lifecycle: draft`。
- 修改完成并经用户重新确认后，才能移回正式主题目录并恢复 `active`。
- 错字、格式、链接和不改变语义的维护可由 agent 自动完成，并在实质性维护时留 event。

### 3.3 更新与冲突

- 新证据支持现有结论：如需改变正文语义，先把 active 文件移回草稿箱；只补不改变语义的来源链接可以直接维护。
- 新证据与现有结论冲突：把 active 文件移回草稿箱，保留原结论、新证据和冲突说明，等待用户确认。
- 结论过时：把文件移回草稿箱，保留来源和变更原因，再由用户确认更新或归档。

## 4. 时间线设计

```text
02-时间线/
  今日.md
  本周.md
  待确认.md
  下一步.md
  归档/
```

- `今日.md`：当天关键变化与当前入口。
- `本周.md`：当前 ISO 周的方向性总结，只由 Weekly Review 更新。
- `待确认.md`：跨区域聚合的用户决策入口，不是事实源。
- `下一步.md`：当前可执行入口，不保存完整路线图。
- `归档/`：旧时间视图快照，不等于全局归档。

## 5. 项目设计

最小项目结构：

```text
03-项目/{project}/
  README.md
  STATUS.md
  ROADMAP.md
  TASKS.md
  OPEN-QUESTIONS.md
  docs/
  repo/
```

- `README.md`：稳定定位、范围和使用方法。
- `STATUS.md`：当前阶段、已完成、进行中、阻塞和下一里程碑。
- `ROADMAP.md`：完整阶段顺序和里程碑。
- `TASKS.md`：当前阶段可执行任务。
- `OPEN-QUESTIONS.md`：未确认问题、原因、选项和建议。
- `docs/`：专项调研、评审、handoff 和设计记录。
- `repo/`：项目实际产品或 release Git 仓库；没有独立发布物的项目可以不创建。
- 历史 review、handoff 和专项调查保留为证据，但不承担当前状态。

## 6. Event 设计

Event 只记录操作事实：

- 谁执行。
- 何时发生。
- 为什么执行。
- 做了什么。
- 改了哪些文件。
- validation 结果。
- 是否需要用户确认。

Event 不保存完整推理，不代替原始内容，也不代替 active knowledge。

## 7. Hindsight 设计

- Hindsight 是可选长期记忆投影。
- 不自动复制整个知识库。
- Retain 需要稳定 `document_id`、受控 tags、来源、适用边界和 event 记录。
- Recall 结果不能直接覆盖项目 STATUS、原件或 active knowledge。
- 当前正式主 bank、迁移策略和认证边界仍由项目 `OPEN-QUESTIONS.md` 管理。

## 8. Git 与 Runtime 设计

- Runtime 根目录是普通 Git clone。
- 系统文件被 Git 跟踪并通过 `git pull` 更新。
- 用户内容、Agent Profile、registry、event、queue、state 和 mutable views 被忽略。
- 首次 clone 后运行 `python .orbitos/scripts/init-runtime.py`，只创建缺失本地文件，不覆盖已有内容。

## 9. Skills 边界

当前 OrbitOS 不存在专属 Skills 层。

- Agent 行为只来源于 `AGENTS.md`、rules、workflows 和 schemas。
- 旧 OrbitOS Skills 已归档，不得作为当前设计依据。
- Role、Thinking Mode 和 Skills 属于不同资产，未来分别设计，不能混为同一对象。

## 10. MAP、STATUS 与 Frontmatter

- `MAP.md` 只做导航，不写状态。
- `STATUS.md` 只写当前状态，不写完整历史。
- 可见 Markdown 默认使用 `title / area / purpose / lifecycle / created / updated / tags`。
- 分类优先使用目录和 tags，不增加重复 frontmatter 字段。
