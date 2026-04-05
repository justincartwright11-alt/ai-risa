# Dead-Letter Notification Email Delivery History Ledger

| notification_id | dead_letter_id | delivery_id | delivery_status | recipients | notification_type | attempt_count | timestamp | terminal_reason |
|-----------------|----------------|-------------|----------------|------------|-------------------|---------------|-----------|----------------|
| test-sent:opened | test-sent | test-sent | sent |  | opened | 1 | 2026-04-06T12:00:00Z | Test sent reason |
| test-failed:opened | test-failed | test-failed | failed |  | opened | 1 | 2026-04-06T12:01:00Z | Test failed reason |
| test-skipped:opened | test-skipped | test-skipped | skipped |  | opened | 1 | 2026-04-06T12:02:00Z | Test skipped reason |
