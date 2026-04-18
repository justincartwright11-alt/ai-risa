# Dead-Letter Notification Email Retry Policy

Max Attempts: 3
Min Retry Spacing: 60 min
Terminal Non-Retry Reasons: invalid-address, permanent-failure, manual-suppression

| notification_id | delivery_id | status | attempts | last_attempt | eligible | reason |
|-----------------|-------------|--------|----------|--------------|----------|--------|
