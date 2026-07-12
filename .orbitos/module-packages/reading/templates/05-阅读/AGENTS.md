# 阅读域 Agent 入口

本目录只保存用户的阅读内容：书籍原文、阅读进度、批注和阅读洞察。通用阅读能力、导入实现与工作流位于 `.orbitos/modules/reading/`。

## 进入条件

- 处理阅读任务时，先读取 `.orbitos/modules/reading/README.md`，再读取命中的 module workflow 或 capability instructions。
- 外部材料必须先进入 `01-收件箱/`；只有用户确认并完成入库后，才可进入 `books/`。

## 数据边界

- `raw.md` 是章节原文底本，只读，不改写、不删除。
- `progress.md` 只记录阅读顺序，不是项目 `STATUS.md`。
- `insight/` 是阅读现场的个人沉淀，不自动进入 `04-知识/`、Hindsight 或其他区域。
- 不在本目录放 Agent 专属 hooks、settings、插件或 dashboard 配置。

## 停止条件

- 未获用户确认、材料未完成入库、原文校验失败或目标书目录已存在时，停止并说明原因。
- 阅读单元视频缺少所需素材时，停止，不创建替代产物。
