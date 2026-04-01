# AI-RISA v1.1 Ops Visibility

## Scope

v1.1 slice 1 and slice 2 add a read-only operations visibility layer on top of
the v1.0 canonical run-history and summary artifacts.

This layer does not change:
- pipeline stage behavior
- existing scheduler pipeline tasks
- retention behavior
- v1.0 summary schema fields

## Components

- `check_latest_run_alert.py`
- `generate_daily_health_summary.py`
- `generate_weekly_health_rollup.py`
- `generate_operator_summary_artifact.py`
- `verify_scheduler_tasks.py`
- `send_ops_notification.py`
- `generate_operator_checklist.py`
- `ops_visibility_aggregation.py`
- `schedule_latest_run_alert_check.ps1`
- `schedule_daily_health_summary.ps1`
- `schedule_weekly_health_rollup.ps1`
- `register_ops_visibility_tasks.ps1`

## Artifacts

Alert outputs:
- `ops/alerts/latest_run_alert.json`
- `ops/alerts/latest_run_alert.md`

Health outputs:
- `ops/health/daily_health_summary.json`
- `ops/health/daily_health_summary.md`
- `ops/health/weekly_health_rollup.json`
- `ops/health/weekly_health_rollup.md`

Operator summary outputs:
- `ops/summary/operator_summary.json`
- `ops/summary/operator_summary.md`

Scheduler verification outputs:
- `ops/verification/scheduler_verification.json`
- `ops/verification/scheduler_verification.md`

Notification outputs (transition-based, optional):
- `ops/notifications/latest_notification.json`
- `ops/notifications/latest_notification.md`
- `ops/state/notification_state.json`

Operator checklist outputs:
- `ops/checklists/operator_checklist_daily.md`
- `ops/checklists/operator_checklist_weekly.md`

Log outputs:
- `ops/logs/latest_run_alert_check.log`
- `ops/logs/daily_health_summary.log`
- `ops/logs/weekly_health_rollup.log`

## Alert Criteria

The latest run is in alert state if any are true:
- non-zero latest run `exit_code`
- latest run status is non-success
- full pipeline summary missing/malformed
- required stage summary artifact missing
- stage-level non-success detected in full summary stage details
- run index unreadable

Reason codes:
- `non_zero_exit`
- `run_status_failed`
- `missing_run_summary`
- `missing_stage_summary`
- `stage_failed`
- `malformed_summary`
- `run_index_unreadable`

## Scheduling

The registration script creates additive tasks only:
- `AI-RISA-Latest-Run-Alert-Check` (interval)
- `AI-RISA-Daily-Health-Summary` (daily)
- `AI-RISA-Weekly-Health-Rollup` (weekly)

These tasks are independent from existing v1.0 pipeline tasks.

The daily and weekly wrappers refresh `operator_summary` after their primary
health artifacts are written so operators get an up-to-date fast-read summary
without introducing extra task sprawl.

Slice 3 extensions:
- alert-check wrapper executes `send_ops_notification.py` using alert state transitions
- daily/weekly wrappers execute `verify_scheduler_tasks.py`
- daily/weekly wrappers generate period-specific operator checklists

No existing production pipeline task semantics are changed.

## Scheduler Verification

Verification status model:
- `pass`
- `warn`
- `fail`

The script validates required tasks for existence, enablement, acceptable state,
expected action script path, and principal/logon context.

Required task set:
- `AI-RISA-Pipeline-Dry-Run`
- `AI-RISA-Pipeline-Normal-Run`
- `AI-RISA-Latest-Run-Alert-Check`
- `AI-RISA-Daily-Health-Summary`
- `AI-RISA-Weekly-Health-Rollup`

## Notification Hooks

Notification delivery is local-first and optional:
- stdout sink
- local json/markdown event artifacts
- optional webhook sink via `ops/config/notification_config.json` (disabled by default)

Notifications are transition-based:
- `false -> true` sends alert notification
- `true -> false` sends recovery notification
- unchanged state sends nothing unless forced

## Operator Checklists

Generated artifacts provide fast daily/weekly operator review with checks for:
- latest run success
- alert review
- health artifact freshness
- scheduler verification status
- failed run review
- run-history health
- recommended next action

## Operator Summary Status Rules

- `healthy`: no active alert and weekly success rate >= 0.90
- `watch`: no active hard alert but recent failures, declining trend, or weekly success rate < 0.90
- `degraded`: active alert or weekly success rate < 0.75

Thresholds are explicit in code:
- `healthy_min_weekly_success_rate = 0.90`
- `watch_min_weekly_success_rate = 0.75`
- `watch_decline_delta = -0.05`

## Smoke Tests

```powershell
python .\check_latest_run_alert.py
python .\generate_daily_health_summary.py
python .\generate_weekly_health_rollup.py
python .\generate_operator_summary_artifact.py
python .\verify_scheduler_tasks.py
python .\send_ops_notification.py
python .\generate_operator_checklist.py --period both
powershell -ExecutionPolicy Bypass -File .\register_ops_visibility_tasks.ps1
```
