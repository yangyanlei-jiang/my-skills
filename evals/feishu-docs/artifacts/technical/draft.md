离线草稿。拟用飞书文档标题字段：**回调幂等与状态查询**。下面的章节、正文、列表及 SQL / JSON 示例，实际写入时分别使用原生标题块、正文段落、无序列表和对应语言的原生代码块。

## 记录表

新增 SQLite 3 表 `idempotency_records`，以唯一请求键记录回调处理状态。

- `id`：整数主键。
- `request_key`：非空字符串，唯一约束防止同一请求键产生多条记录；该约束同时支持按键查询，无需重复建索引。
- `status`：非空字符串，仅允许 `pending`（处理中）或 `done`（已完成）。
- `created_at`：非空字符串，记录创建时间，由应用写入。

```sql
CREATE TABLE idempotency_records (
    id INTEGER PRIMARY KEY,
    request_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'done')),
    created_at TEXT NOT NULL
);
```

回调开始时创建 `pending` 记录，处理完成后更新为 `done`。重复请求遇到唯一键冲突时读取已有记录，避免再次执行同一回调；业务处理与状态更新的一致性需由实现保障。

## 查询接口

`GET /api/idempotency/{request_key}`，请求键取路径参数 `request_key`，按 `request_key` 查询记录。数据库字段 `request_key` 映射为响应字段 `requestKey`，状态原样返回。

找到记录：HTTP 200。

```json
{
  "ok": true,
  "payload": {
    "requestKey": "req-001",
    "status": "done"
  },
  "error": null
}
```

未找到记录：HTTP 404。

```json
{
  "ok": false,
  "payload": null,
  "error": {
    "type": "NOT_FOUND",
    "detail": "记录不存在"
  }
}
```
