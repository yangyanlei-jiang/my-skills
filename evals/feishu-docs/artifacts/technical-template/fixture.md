# 离线虚构项目资料

请生成一份适合飞书批量转换的技术方案 Markdown，只写本次接口与数据库变更，无需登录、发布或浏览器。

项目契约：
- SQLite 3；表名 snake_case，主键 INTEGER PRIMARY KEY；不支持 ENGINE/CHARSET、MySQL COMMENT、TiDB 扩展。
- 新增任务记录表 task_records：id（整数主键），request_key（文本，非空，唯一，用于幂等），status（文本，非空，默认 pending，仅 pending/done），created_at（文本，非空，ISO 8601 UTC）；查询按 status，需状态索引。字段含义可在 SQL 行注释中说明。
- 新增接口 get_task_record，GET /v1/task-records/{id}，JWT 鉴权，客户端版本 >= 1.4.0。
- 入参：路径 id，整数，必填。
- 项目响应封装固定为 ok/payload/error，成功 HTTP 200：{"ok":true,"payload":{"task":{"id":7,"status":"done","created_at":"2026-10-12T09:00:00Z"}},"error":null}。
- 未找到 HTTP 404：{"ok":false,"payload":null,"error":{"kind":"not_found","detail":"Task record not found"}}。
- payload.task 字段：id 整数；status 字符串 pending/done；created_at 字符串 ISO 8601 UTC。
- error 字段：kind 字符串，detail 字符串；失败时 payload=null；成功时 error=null。
- 无分页。不要发明响应字段、数据库参数或技术实现细节。

交付：draft.md 正文与 plan.md 简短转换/验收计划。
