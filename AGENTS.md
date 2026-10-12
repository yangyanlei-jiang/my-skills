# 集合维护约定

- 用户新增的个人技能统一放在 `skills/<skill-name>/`。每个目录是可单独安装的完整技能，不依赖另一个技能的内部文件。
- 使用准确、简短的英文目录名与 `name`；面向用户的说明可以使用中文。新增或更名时更新根 README 的技能索引。
- `SKILL.md` 保持可执行的核心流程；详细资料放入 `references/` 并从入口链接。只添加实际有用的脚本或资源。
- 不把账号、访问令牌、私人文档或会话状态放进仓库。需要外部工具时明确能力边界，不声称技能本身提供连接或权限。
- 提炼外部资料保留来源、作者与核对日期；用自己的文字归纳，区分历史界面建议和当前工具契约。
- 修改技能后验证清单结构、引用路径，并进行与修改相关的行为场景检查。迁移可执行技能时运行其原有测试，不以静态关键词检查代替行为验证。
- SkillRover 在本集合统一维护；不要将集合内容推送到原独立仓库。远程发布和原仓库迁移公告应使用明确的实际目标。

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- Use `codegraph_explore` when available; name a file or symbol to read its current line-numbered source and call paths.
- Shell fallback: `codegraph explore "<symbol names or question>"`.
- If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
