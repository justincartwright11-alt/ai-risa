# Button 1 Current-Week Live Source Provider Orchestrator Scaffold v1

## Slice
button1-current-week-live-source-provider-orchestrator-scaffold-v1

## Baseline
- Design baseline: button1-current-week-live-source-provider-design-v1
- Commit: f88c81a
- Tag: button1-current-week-live-source-provider-design-v1

## Goal
Scaffold the Button 1 live source provider orchestrator and adapter contract while preserving deterministic fail-closed behavior unless a real approved provider is configured and returns valid source-backed rows in the discovery window.

## Scope
- In scope:
  - Approved provider registry scaffold
  - Adapter interface scaffold
  - Disabled/unconfigured handling
  - Normalized provider result object
  - Canonical refreshed feed artifact contract scaffold
  - Diagnostics and deterministic fail-closed outputs
- Out of scope:
  - Real web-source implementation
  - Button 2 changes
  - Button 3 changes
  - Queue/database writes

## Implemented Files
- operator_dashboard/button1_live_source_provider_orchestrator_v1.py
- operator_dashboard/test_button1_current_week_live_source_provider_orchestrator_scaffold_v1.py
- docs/button1_current_week_live_source_provider_orchestrator_scaffold_v1.md
- ops/release_checks/button1-current-week-live-source-provider-orchestrator-scaffold-v1/orchestrator_scaffold_summary.json

## Required Fail-Closed Semantics
1. Empty provider registry:
   - feed_status: unavailable
   - current_week_ready: false
   - save_allowed: false
   - diagnostics includes no_approved_live_source_provider_configured
2. Provider disabled:
   - feed_status: unavailable
   - current_week_ready: false
   - save_allowed: false
   - diagnostics includes provider_disabled
3. Invalid provider payload:
   - feed_status: unavailable
   - current_week_ready: false
   - save_allowed: false
   - diagnostics includes provider_payload_invalid
4. Rows outside discovery window:
   - feed_status: no_current_week_source_backed_matchups
   - current_week_ready: false
   - save_allowed: false
5. Valid rows in discovery window:
   - feed_status: current_week_ready
   - current_week_ready: true
   - save_allowed: true for preview eligibility only
   - operator approval remains required before any persistent write

## Output Contract
The orchestrator result includes:
- feed_status
- generated_at_utc
- current_week_start
- current_week_end
- upcoming_window_days
- source_freshness
- feed_age_seconds
- current_week_ready
- save_allowed
- fallback_used
- diagnostics
- provider_count
- provider_names
- selected_provider
- source_backed_event_cards
- current_week_rows_count
- approved_source_event_rows_count

## Governance Guardrails Preserved
- No auto-save of fights
- No auto-promotion to Button 2 queue
- No Button 2 renderer/report/PDF changes
- No Button 3 results/accuracy/learning changes
- No unapproved provider enabled by default
- No fake current-week event generation

## Validation Plan
- pytest operator_dashboard/test_button1_current_week_live_source_provider_orchestrator_scaffold_v1.py -q
- pytest operator_dashboard/test_button1_current_week_source_discovery_refresh_and_stale_feed_guard_v1.py -q
- pytest operator_dashboard/test_button1_current_week_source_discovery_runtime_binding_repair_v1.py -q

## Expected Verdict
LOCKED/PASS when tests pass and git scope confirms only scaffold files are committed.
