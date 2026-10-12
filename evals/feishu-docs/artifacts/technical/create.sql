CREATE TABLE idempotency_records (
    id INTEGER PRIMARY KEY,
    request_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'done')),
    created_at TEXT NOT NULL
);
