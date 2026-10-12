# 离线应用变体

使用同一个技能，独立生成 another-draft.md、another-plan.md。此次内容不同于技能示例，只生成飞书兼容 Markdown，不发布、不操作浏览器。

- SQLite 3；新增 message_receipts 表，id INTEGER PRIMARY KEY；dedupe_key TEXT NOT NULL UNIQUE；state TEXT NOT NULL DEFAULT queued，只允许 queued/sent；created_at TEXT NOT NULL，ISO 8601 UTC。按 state 查询，需要命名索引 idx_message_receipts_state。
- 接口 get_message_receipt，GET /v2/message-receipts/{id}，项目认证为 X-Client-Key Header（不要写 JWT），无客户端版本限制。
- 入参：路径 id，integer，必填。
- 成功 HTTP 200：{"success":true,"result":{"receipt":{"id":12,"state":"sent","created_at":"2026-10-12T10:00:00Z"}},"fault":null}。
- 未找到 HTTP 404：{"success":false,"result":null,"fault":{"reason":"missing","description":"Receipt not found"}}。
- result.receipt 子字段与上例一致，fault 字段为 reason/description，均 string。失败时 result=null，成功时 fault=null。无分页。
- 原生富文本表格、SQL/JSON 代码围栏在生成阶段完成；不引入原技能示例的接口、表名、ok/payload/error、认证或版本门槛。
