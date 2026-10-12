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

首次目录迁移验收时尚未运行 GitHub 的 CI 矩阵，也尚未发布远程集合或修改旧仓库迁移公告。发布后的当前状态请查看仓库与其 Actions 记录。

## 补充验证：原生优先，简约输出

2026-10-12 根据用户要求新增总原则。独立执行者读取更新后的技能，将三项事实和一项风险编为简短周报：[草稿](artifacts/simple/draft.md)、[原生操作计划](artifacts/simple/plan.md)。

观察到的结果：正文仅两项进展列表和一项风险，标题使用标题字段；选择原生列表与高亮块，无额外章节、表格、图表或装饰。必需信息均保留，不声称已真实写入。清单验证再次通过；此检查仍是离线行为方案验证。

## 补充验证：数据库表与接口契约

2026-10-12 增加技术方案必要交付要求。独立执行者使用虚构的 SQLite 3 项目资料和明确的 `ok/payload/error` 响应契约，编写新增幂等记录表及查询接口方案：[正文](artifacts/technical/draft.md)、[DDL](artifacts/technical/create.sql)、[响应示例](artifacts/technical/responses.json)、[原生操作计划](artifacts/technical/plan.md)。

结果包含完整 CREATE TABLE、成功与未找到响应，并选择 SQL/JSON 原生代码块；响应未套用其他封装。主执行者核对正文与独立产物完全一致，在 SQLite 内存数据库执行 DDL 和有效插入，并确认唯一约束、状态约束、非空约束拒绝非法记录。此验证不涉及真实项目数据库、接口实测或飞书写入；示例中的 SQLite 与响应结构不作为技能的默认规范。

## 补充验证：Markdown 优先与局部原生补齐

2026-10-12 将默认流程改为先生成飞书兼容 Markdown，再批量转换，仅在最后处理当前转换链路未支持的原生格式。新增离线 `.md` 交付入口，保留技术方案和简约输出要求。

依据飞书官方 CLI 当前的 Markdown/XML 格式参考，区分通用 Markdown、允许原生 XML 扩展的飞书 Markdown，以及编辑器快捷语法；明确普通 `.md` 上传不等于原生文档。检查时本机未安装飞书 CLI，未实际执行云端转换。

独立基线使用更新前 `085ed88` 中的技能快照，并得到明确的批量转换能力说明：[Markdown](artifacts/md-baseline/draft.md)、[计划](artifacts/md-baseline/plan.md)。基线已经选择批量转换并只用浏览器补下划线、高亮块，没有观察到该场景下逐段重排的失败。因此不据此声称修复了已复现故障或测得性能提升。

更新后两个离线场景：

- 支持飞书原生扩展：[Markdown](artifacts/md-guided/A/draft.md)、[计划](artifacts/md-guided/A/plan.md)。下划线和高亮块在 Markdown 中直接表达，批量转换后结构读回验收，不预设浏览器操作。
- 只支持基础 Markdown：[Markdown](artifacts/md-guided/B/draft.md)、[计划](artifacts/md-guided/B/plan.md)。完整生成标题、列表、3×3 表格和 Python 围栏；批量转换后仅用浏览器补两项原生格式，不重建已有表格。

主执行者读取并核对全部产物，确认要求和数据保留、操作说明未混入正式正文、计划未宣称真实写入。XML 扩展片段的本地解析、技能清单、UI 配置与引用路径检查通过。以上是内容与操作计划验证，未验证真实工具的转换保真、浏览器执行或耗时。

## 补充验证：个人接口、建表与统一全宽表格格式

2026-10-12 通过已登录浏览器只读核对用户指定文档的 3.1 接口结构、5.1 SQL 展示及 2.2 原生表格结构和样式。公开技能仅保存可复用版式与虚构示例；私有地址、原文业务字段和数据未提交。未编辑原参考文档。

独立基线使用 `c30fb8d` 的旧技能快照与虚构资料：[正文](artifacts/technical-template/baseline/draft.md)、[计划](artifacts/technical-template/baseline/plan.md)。内容已包含正确的 SQL 与响应契约，但接口基本信息为段落、响应字段合并在一张表中，未使用此次指定的基本信息表与按对象分表版式。基线未获得该私人版式，因此不把这种差异视为原有接口内容错误，也不据此宣称准确率或性能提升。

更新后的 [任务记录方案](artifacts/technical-template/guided/draft.md) 采用基本信息、入参、返回格式、分对象字段表、JSON 示例和条件说明；新增表标题下直接放完整 SQL。首次指导样本重复列了公共响应根对象和单字段中间层，补充条件性说明后删除两张重复表，仅保留三张必要表格。

[不同契约变体](artifacts/technical-template/guided/another-draft.md) 使用 `success/result/fault`、X-Client-Key 与另一个 SQLite 表，未沿用技能示例的响应封装、JWT 或版本门槛。主执行者读回全部产物，解析 JSON，并在 SQLite 内存数据库执行两套 DDL，确认默认状态、唯一/枚举/非空约束和命名查询索引。没有调用真实接口或执行真实项目迁移。以上技术方案检查发生在后续表格样式补充之前，样式和宽度由下面单独场景验证。

用户进一步要求新表格采用 2.2 的浅灰表头、加粗居中、正文左/顶部对齐、自然换行与细边框，并让所有表格总宽度一致、铺满正文可用宽度。两种能力下的离线应用结果：

- [扩展 Markdown](artifacts/technical-template/guided/table-A.md)、[验收计划](artifacts/technical-template/guided/table-A-plan.md)：根据场景给定的 960px 正文宽度直接生成 XML；两列表为 240+720，三列表为 240+160+560，总宽均为 960。主执行者解析 XML，核对全部数据、特殊字符、表头样式、正文对齐及列宽总和。
- [基础 Markdown](artifacts/technical-template/guided/table-B.md)、[补齐计划](artifacts/technical-template/guided/table-B-plan.md)：保留完整管道表格，列出背景、对齐和全宽的具体缺口；取得目标正文宽度 W 后按内容分配列宽并保留相同总宽，只调整已有表格，不重建或逐格重填。

本地检查最初将分隔行中的列分隔符出现次数误当成表格数量；确认实际有两行分隔行后修正该验证断言并重新通过。未更改表格产物以迎合断言。

虚构资料见 [主场景](artifacts/technical-template/fixture.md)、[契约变体](artifacts/technical-template/variation.md)、[表格场景](artifacts/technical-template/table-fixture.md)。技能清单、引用、XML 示例、JSON 与 SQL 本地检查通过。以上均为离线生成与计划验证；真实 Markdown 转换、全宽渲染和浏览器补齐效果尚未实测。
