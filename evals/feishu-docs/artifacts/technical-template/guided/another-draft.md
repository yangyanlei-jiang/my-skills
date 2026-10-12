# 消息回执查询接口与数据库变更方案

## 1 `get_message_receipt` — 消息回执查询（新增）

| **项** | **说明** |
| --- | --- |
| 方法与路径 | `GET /v2/message-receipts/{id}` |
| 认证 | 使用 `X-Client-Key` Header |

**入参：** 路径参数 `id`，integer，必填。

**返回格式：** 新增消息回执查询响应，使用项目的 `success/result/fault` 封装；成功返回 `result.receipt`，未找到时返回错误对象，无分页。

`result.receipt`：

| **字段** | **类型** | **说明** |
| --- | --- | --- |
| `id` | integer | 消息回执 ID |
| `state` | string | 回执状态，仅 `queued` 或 `sent` |
| `created_at` | string | 创建时间，ISO 8601 UTC |

`fault`（失败时）：

| **字段** | **类型** | **说明** |
| --- | --- | --- |
| `reason` | string | 错误原因；未找到时为 `missing` |
| `description` | string | 错误说明；未找到时为 `Receipt not found` |

**返回示例（成功，HTTP 200）：**

```json
{
  "success": true,
  "result": {
    "receipt": {
      "id": 12,
      "state": "sent",
      "created_at": "2026-10-12T10:00:00Z"
    }
  },
  "fault": null
}
```

**返回示例（未找到，HTTP 404）：**

```json
{
  "success": false,
  "result": null,
  "fault": {
    "reason": "missing",
    "description": "Receipt not found"
  }
}
```

**条件说明：** 查询成功时返回 HTTP 200，且 `success=true`、`fault=null`；未找到回执时返回 HTTP 404，且 `success=false`、`result=null`。接口使用 `X-Client-Key` Header 认证，无客户端版本限制。

## 2 新增消息回执表 `message_receipts`

```sql
CREATE TABLE message_receipts (
    id INTEGER PRIMARY KEY, -- 消息回执 ID
    dedupe_key TEXT NOT NULL UNIQUE, -- 去重标识
    state TEXT NOT NULL DEFAULT 'queued'
        CHECK (state IN ('queued', 'sent')), -- 回执状态，仅 queued/sent
    created_at TEXT NOT NULL -- 创建时间，ISO 8601 UTC
);

CREATE INDEX idx_message_receipts_state ON message_receipts (state);
```
