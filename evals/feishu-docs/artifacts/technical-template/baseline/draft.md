# 任务记录查询接口与数据库变更

新增 `task_records` 表和 `get_task_record` 接口，用于按任务记录 ID 查询状态与创建时间。

## 数据库变更

数据库为 SQLite 3。`request_key` 用于幂等，查询按 `status` 使用状态索引。

```sql
CREATE TABLE task_records (
    id INTEGER PRIMARY KEY, -- 任务记录 ID
    request_key TEXT NOT NULL UNIQUE, -- 幂等请求标识
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'done')), -- 仅允许 pending、done
    created_at TEXT NOT NULL -- 创建时间，ISO 8601 UTC
);

CREATE INDEX idx_task_records_status ON task_records (status);
```

## 接口变更

接口名称：`get_task_record`。方法与路径：`GET /v1/task-records/{id}`。要求 JWT 鉴权，客户端版本 **>= 1.4.0**。

### 请求参数

| **参数** | **位置** | **类型** | **要求** |
| --- | --- | --- | --- |
| `id` | 路径 | 整数 | 必填，任务记录 ID |

### 响应

响应封装使用 `ok/payload/error`，无分页。成功时 `error=null`；失败时 `payload=null`。

| **字段** | **类型** | **说明** |
| --- | --- | --- |
| `ok` | 布尔值 | 成功为 `true`，失败为 `false` |
| `payload` | 对象或 `null` | 成功响应内容；失败为 `null` |
| `payload.task` | 对象 | 任务记录 |
| `payload.task.id` | 整数 | 任务记录 ID |
| `payload.task.status` | 字符串 | `pending` 或 `done` |
| `payload.task.created_at` | 字符串 | ISO 8601 UTC 创建时间 |
| `error` | 对象或 `null` | 错误信息；成功为 `null` |
| `error.kind` | 字符串 | 错误类型 |
| `error.detail` | 字符串 | 错误说明 |

成功：HTTP 200。

```json
{
  "ok": true,
  "payload": {
    "task": {
      "id": 7,
      "status": "done",
      "created_at": "2026-10-12T09:00:00Z"
    }
  },
  "error": null
}
```

未找到：HTTP 404。

```json
{
  "ok": false,
  "payload": null,
  "error": {
    "kind": "not_found",
    "detail": "Task record not found"
  }
}
```
