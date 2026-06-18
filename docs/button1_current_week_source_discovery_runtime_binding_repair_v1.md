# Button 1 Runtime Binding Repair v1

## Slice
button1-current-week-source-discovery-runtime-binding-repair-v1

## Problem
Runtime smoke showed `live_source_status` in workflow-preview contained only a partial shape (`approved_source_event_rows_count`, `diagnostics`, `enabled`, `feed_used`) even though current-week/stale/demo guard logic existed in tests.

## Root Cause
Two runtime issues were identified:
1. `live_source_status` contract mapping in runtime payload was incomplete for required fields.
2. Smoke validation initially hit a stale reloader-bound server process path, masking updated runtime binding output.

## Repair
- Expanded Button 1 runtime `live_source_status` contract to include:
  - `feed_status`
  - `generated_at_utc`
  - `current_week_start`
  - `current_week_end`
  - `upcoming_window_days`
  - `source_freshness`
  - `feed_age_seconds`
  - `current_week_ready`
  - `save_allowed`
  - `fallback_used`
  - `diagnostics`
  - `feed_used`
  - `approved_source_event_rows_count`
  - `current_week_rows_count`
  - `source_backed_event_cards`
- Kept operator approval gate unchanged.
- Preserved preview-only behavior and no auto-save behavior.
- Updated no-current-week status label to:
  - `no_current_week_source_backed_matchups`

## Verification
- Required test suites for stale/current-week guard + runtime binding repair pass.
- Runtime smoke response after repair captured at:
  - `ops/release_checks/button1-current-week-source-discovery-runtime-binding-repair-v1/workflow_preview_response_after_repair.json`
- Current live smoke status is fail-closed due stale feed:
  - `feed_status=stale`
  - `current_week_ready=false`
  - `save_allowed=false`

## Governance
- No Button 2 rendering/template/gate changes.
- No Button 3 result/learning/calibration/apply changes.
- No auto queue writes.
- Operator approval remains required for permanent actions.
