# Manual-Intervention Retry/Requeue Executor

_Generated: 2026-04-06T01:02:29.784533+00:00_

- **Execution ID:** e60bd32bac9b98f5
  - Case: `RES-b5565150eed50446` | Fingerprint: `b5565150eed50446e416b47b3419e3e083025870c5f77f4ca9e5b27fb145cfae`
  - State: `pending` | Eligibility: `eligible` | Result: `not_executed`
  - Type: `retry_requeue` | Attempt: 1 | Target: smtp://mail.example.com/queue/evt-002
  - Source: Event `evt-002` | Schedule `sched-2026-04-06` | Run `run-02` | Op `email_dispatch`
  - Failure: Family `smtp` | Code `451`
  - Requested: 2026-04-06T00:35:55.665577Z | Executed: None
  - Block Reason: None | Dedupe: RES-b5565150eed50446|retry_requeue|smtp://mail.example.com/queue/evt-002|1
