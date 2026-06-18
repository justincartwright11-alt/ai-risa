# Button 1 Current-Week Live Source Provider Runtime Integration Preview v1

## Slice
button1-current-week-live-source-provider-runtime-integration-preview-v1

## Baseline
- Slice: button1-current-week-live-source-provider-orchestrator-scaffold-v1
- Commit: 01551a1
- Tag: button1-current-week-live-source-provider-orchestrator-scaffold-v1

## Goal
Wire the Button 1 live source provider orchestrator into the Button 1 preview/runtime path only, while keeping the system fail-closed unless an approved provider is configured and returns valid source-backed current-week/upcoming rows.

## Scope
- In scope:
  - Button 1 workflow-preview runtime integration
  - Orchestrated `live_source_status` binding for preview/runtime
  - Fail-closed no-provider behavior
  - Stale approved-source JSON suppression as live discovery authority
  - Runtime preview smoke evidence
- Out of scope:
  - Button 2 renderer, PDF generation, report templates, or customer-ready gates
  - Button 3 result, accuracy, learning, calibration, or apply behavior
  - Auto-save fights
  - Auto-promotion to Button 2 queue
  - Real web scraping or random providers

## Implemented Runtime Behavior
- Button 1 workflow-preview now uses the orchestrated preview helper.
- No approved provider configured:
  - `feed_status=unavailable`
  - `current_week_ready=false`
  - `save_allowed=false`
  - diagnostics include `no_approved_live_source_provider_configured`
  - queue/database write flags remain false
- Existing stale approved-source JSON no longer acts as live discovery authority in the preview path.
- Operator approval gate remains required before any persistent queue or database write.

## Runtime Smoke Evidence
- Saved workflow preview response JSON:
  - `ops/release_checks/button1-current-week-live-source-provider-runtime-integration-preview-v1/workflow_preview_response.json`

## Validation Plan
- `pytest operator_dashboard/test_button1_current_week_live_source_provider_orchestrator_scaffold_v1.py -q`
- `pytest operator_dashboard/test_button1_current_week_live_source_provider_runtime_integration_preview_v1.py -q`
- `pytest operator_dashboard/test_button1_current_week_source_discovery_refresh_and_stale_feed_guard_v1.py operator_dashboard/test_button1_current_week_source_discovery_runtime_binding_repair_v1.py -q`

## Expected Verdict
LOCKED/PASS once the runtime preview smoke and focused tests pass, with Button 2 and Button 3 unchanged.
