# 任务记录查询接口与数据库变更方案

## 1 `get_task_record` — 任务记录查询（新增）

| **项** | **说明** |
| --- | --- |
| 方法与路径 | `GET /v1/task-records/{id}` |
| 认证 | JWT 鉴权 |
| 生效版本 | 客户端版本 ≥ 1.4.0 |

**入参：** 路径参数 `id`，整数，必填。

**返回格式：** 新增任务记录查询响应，沿用项目固定的 `ok/payload/error` 封装；成功返回 `payload.task`，未找到时返回错误对象，无分页。

`payload.task`：

| **字段** | **类型** | **说明** |
| --- | --- | --- |
| `id` | integer | 任务记录 ID |
| `status` | string | 任务状态，仅 `pending` 或 `done` |
| `created_at` | string | 创建时间，ISO 8601 UTC |

`error`（失败时）：

| **字段** | **类型** | **说明** |
| --- | --- | --- |
| `kind` | string | 错误类型；未找到时为 `not_found` |
| `detail` | string | 错误说明；未找到时为 `Task record not found` |

**返回示例（成功，HTTP 200）：**

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

**返回示例（未找到，HTTP 404）：**

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

**条件说明：** 查询成功时返回 HTTP 200，且 `ok=true`、`error=null`；未找到记录时返回 HTTP 404，且 `ok=false`、`payload=null`。接口要求 JWT 鉴权及客户端版本 ≥ 1.4.0。

## 2 新增任务记录表 `task_records`

```sql
CREATE TABLE task_records (
    id INTEGER PRIMARY KEY, -- 任务记录 ID
    request_key TEXT NOT NULL UNIQUE, -- 幂等请求标识
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'done')), -- 任务状态，仅 pending/done
    created_at TEXT NOT NULL -- 创建时间，ISO 8601 UTC
);

CREATE INDEX idx_task_records_status ON task_records (status);
```
