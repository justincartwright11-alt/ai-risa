# Dead-Letter Notification Email Retry Policy

Max Attempts: 3
Min Retry Spacing: 60 min
Terminal Non-Retry Reasons: invalid-address, manual-suppression, permanent-failure

| notification_id | delivery_id | status | attempts | last_attempt | eligible | reason |
|-----------------|-------------|--------|----------|--------------|----------|--------|
| delivery-a8edb31df556e03e:opened | delivery-a8edb31df556e03e | sent | 1 | 2026-04-10T00:30:11.317570 | False | Already sent, never retry |
