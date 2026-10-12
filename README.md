# my-skills

个人 Agent Skills 集合。后续新技能统一放在 `skills/<skill-name>/`，每个技能独立维护并按需安装。

| 技能 | 用途 | 状态 |
| --- | --- | --- |
| [skill-rover](skills/skill-rover/SKILL.md) | 自动选择技能，并跟踪使用与定时复评 | 从原 SkillRover 仓库迁入，保留历史和测试 |
| [feishu-docs](skills/feishu-docs/SKILL.md) | 创建或编辑飞书原生文档，使用富文本表格、标题、列表、高亮块和代码块 | 已完成指引与离线场景验证；需要可用的飞书连接器或浏览器 |

## 使用方式

将需要的技能目录安装到智能体的技能目录。Codex 通常使用 `~/.codex/skills/<skill-name>`，Claude Code 可使用 `~/.claude/skills/<skill-name>`。保留完整目录中的 `SKILL.md`、`agents/` 和引用资源；安装后按宿主要求刷新技能列表。

也可以让支持技能安装的智能体从当前集合的指定技能目录安装。技能只是操作指引，账号连接、API 权限和浏览器登录需要由运行环境提供。

示例请求：

> 使用 feishu-docs，把这份上线方案写入飞书文档。使用分级标题、风险高亮块和原生富文本表格；完成后给我链接并核对格式。

`feishu-docs` 已提炼用户指定的 [《如何写好飞书文档？》](https://www.feishu.cn/hc/zh-CN/articles/360049067898-%E5%A6%82%E4%BD%95%E5%86%99%E5%A5%BD%E9%A3%9E%E4%B9%A6%E6%96%87%E6%A1%A3)，写作原则见 [来源与摘要](skills/feishu-docs/references/writing-principles.md)。

## 维护

新增技能遵循 [AGENTS.md](AGENTS.md)，并更新此索引。SkillRover 的主维护目录为 `skills/skill-rover/`；[原独立仓库](https://github.com/yangyanlei-jiang/skill-rover) 保留历史版本。集合当前在本地整理，尚未发布 GitHub 集合仓库或更新原仓库迁移公告。

验证记录见 [feishu-docs 评估](evals/feishu-docs/report.md)。SkillRover 检查可在 `skills/skill-rover/` 中运行：

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python examples/lifecycle_demo.py
```

本集合原创内容使用 [MIT License](LICENSE)。外部文章和产品文档的版权归其权利人；引用与归纳不改变其授权。
