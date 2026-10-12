# feishu-docs 验证记录

日期：2026-10-12。版本：首次编写。范围：技能清单、来源提炼、离线行为方案与集合迁移。未使用真实飞书账号或执行真实文档写入。

## 结构与引用

- `skill-creator/scripts/quick_validate.py` 检查 feishu-docs 与 skill-rover：均通过。
- UI 配置保留 `$feishu-docs` 入口，允许隐式调用；技能不绑定虚构 MCP 服务。
- 用户指定文章的来源、作者、投稿与页面更新时间已记录；正文以归纳方式提炼，不整篇转载。
- 核心流程链接到写作原则、原生格式与工具适配。旧界面图标和历史限制未写成固定 API 规则。

## 独立离线行为检查

场景要求见 [scenarios.md](scenarios.md)。执行者提交的完整内容保存在 `artifacts/`，由主执行者读取检查。

| 场景 | 观察到的行为 | 结果与边界 |
| --- | --- | --- |
| 未读取新技能的基线 | 原生插入 3×3 表格、高亮块、Python 代码块、日期下划线；未假设 Markdown 自动转换；不声称真实写入 | 基线已正确处理主要格式，未观察到这些方面的失败 |
| 读取技能后的编写方案 | 表格逐格填入并加粗表头；正文重点保持正文；图示取决于实际渲染能力；不重复正文标题 | 离线方案满足要求；尚未操作真实编辑器 |
| 仅纯文本工具 | 明确不能完成原生表格验收，不将 Markdown 外观或纯文本读回作为成功证明 | 边界处理符合预期；没有真实工具调用 |
| 单元格编辑 | 仅更新目标 B3；“已”加粗，“完成”保留原 URL 与非加粗属性；不重写 T2 或其他单元格；计划读回验收 | 最小离线参数符合给定契约；未验证真实 API |

产物：

- 基线：[内容](artifacts/baseline/draft.md)、[原生操作](artifacts/baseline/operations.md)。
- 受指导：[内容](artifacts/guided/draft.md)、[原生操作](artifacts/guided/operations.md)。
- 边界与编辑：[工具不足响应](artifacts/boundary/response.md)、[编辑参数](artifacts/boundary/edit.json)、[定位与验收](artifacts/boundary/rationale.md)。

这是操作方案检查，不是实际浏览器执行或 API 集成测试。基线已通过主要格式要求，且指导场景额外增加正文强调要求，不能据此声称技能提升了成功率。

指导执行者额外收到宿主 SkillRover 复评提醒，读取了该技能和 due 状态；这是场景隔离偏差。没有联网、访问飞书或修改管理状态。其文档产物依据 feishu-docs 及引用资料编写，不能当作完全隔离的受控实验。

## 本机部署

验证后将技能复制到 `~/.codex/skills/feishu-docs`，确认安装内容与集合源目录一致。安装使用普通目录：执行器不支持将授权写入路径设为符号链接，初次链接已替换。未覆盖其他技能。后续修改以集合目录为源，重新同步安装副本。宿主可能需要刷新技能列表或重新开始会话；本次不宣称已经验证真实隐式触发，也未在 Claude Code 实机测试。

## SkillRover 目录迁移

将原仓库内容迁到 `skills/skill-rover/`，保留历史，未改动运行时实现。CI 的命令工作目录同步调整。使用现有 Python 环境在新目录执行：

- `python -B -m unittest discover -s tests -v`：62 项测试通过。
- `python -B examples/lifecycle_demo.py`：首次加载计时、重复加载不重置、替换与归档演示通过。

尚未运行 GitHub 的 CI 矩阵。集合目前是本地 Git 仓库，没有发布远程集合或修改旧仓库迁移公告。
