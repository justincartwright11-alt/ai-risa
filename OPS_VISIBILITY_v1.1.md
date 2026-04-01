# AI-RISA v1.1 Ops Visibility

## Scope

v1.1 slice 1 adds a read-only operations visibility layer on top of the v1.0
canonical run-history and summary artifacts.

This layer does not change:
- pipeline stage behavior
- existing scheduler pipeline tasks
- retention behavior
- v1.0 summary schema fields

## Components

- `check_latest_run_alert.py`
- `generate_daily_health_summary.py`
- `schedule_latest_run_alert_check.ps1`
- `schedule_daily_health_summary.ps1`
- `register_ops_visibility_tasks.ps1`

## Artifacts

Alert outputs:
- `ops/alerts/latest_run_alert.json`
- `ops/alerts/latest_run_alert.md`

Health outputs:
- `ops/health/daily_health_summary.json`
- `ops/health/daily_health_summary.md`

Log outputs:
- `ops/logs/latest_run_alert_check.log`
- `ops/logs/daily_health_summary.log`

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

These tasks are independent from existing v1.0 pipeline tasks.

## Smoke Tests

```powershell
python .\check_latest_run_alert.py
python .\generate_daily_health_summary.py
powershell -ExecutionPolicy Bypass -File .\register_ops_visibility_tasks.ps1
```
