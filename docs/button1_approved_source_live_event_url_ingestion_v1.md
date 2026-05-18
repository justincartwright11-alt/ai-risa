# Button1 Approved Source Live Event URL Ingestion v1

## Slice
button1-approved-source-live-event-url-ingestion-v1

## Objective
Connect approved-source live event URL ingestion into Button 1 runtime candidate feed so source-backed candidates can become would-save eligible under existing Gate 1 rules, while non-URL rows remain blocked.

## What Was Added
### 1) Approved-source ingestion path in runtime loader
Updated `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`:
- Added governed config + feed ingestion for Button 1 approved sources.
- New runtime ingestion source:
  - `ops/approved_sources/button1_live_event_source_rows.json`
  - `ops/approved_sources/button1_live_event_source_rows.jsonl`
  - `ops/approved_sources/live_event_source_rows.json`
- Added approved URL pattern validation (official promotions only by default):
  - UFC / UFCStats
  - ONE Championship
  - GLORY
  - Matchroom
  - Queensberry
  - Top Rank
  - No Limit Boxing
- Normalized approved-source event rows into accepted provenance fields:
  - `source_url`
  - `source_name`
  - `source_type`
  - `event_url`
  - `canonical_source_url`
  - `provenance.source_url`
  - `provenance.source_name`
  - `provenance.source_type`

### 2) Candidate provenance propagation enhancement
- Existing event-name propagation now carries source metadata (not just URL):
  - source name/type/event URL/canonical URL
  - provenance source name/type

### 3) Fail-closed live ingestion diagnostics
Runtime payload now includes `live_source_status` with clear fail-closed diagnostics:
- `live_source_unavailable`
- `approved_source_not_configured`
- `no_source_backed_events_found`

### 4) Dashboard visibility
Updated `operator_dashboard/templates/index.html` Button 1 status rendering:
- Adds explicit Approved Source Live Ingestion preview section showing:
  - approved source-backed event row count
  - feed used path
  - fail-closed diagnostics
  - approval-gated/no auto-save status

### 5) Button 1 summary readiness fallback for dashboard counters
Updated `operator_dashboard/local_ai_orchestrator_engine_adapter_registry.py`:
- Source-backed candidate rows now contribute to `ready_for_report_count` fallback.
- This ensures Button 1 card counters reflect source-backed candidates in normal dashboard hydration.

## Governance / Safety
- Gate 1 logic was not relaxed.
- No provenance checks were bypassed.
- No fake URL or synthetic official provenance was generated.
- No automatic queue save/write added.
- Operator approval remains required.
- No Button 2 PDF generation logic changed.
- No Button 3 learning/calibration logic changed.
- No Phase 7 controlled delivery logic changed.
- No uncontrolled writes introduced.

## Validation
Command run:

```bash
C:/Users/jusin/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest \
  operator_dashboard/test_local_ai_orchestrator_readonly_runtime_context_loader_v1.py \
  operator_dashboard/test_local_ai_orchestrator_button1_discovery_readiness_adapter_hook_v1.py \
  operator_dashboard/test_local_ai_orchestrator_gate1_dry_run_apply_preview_api_v1.py \
  operator_dashboard/test_local_ai_orchestrator_gate1_approved_save_writer_api_preview_v1.py \
  operator_dashboard/test_local_ai_orchestrator_runtime_context_dashboard_wire_v1.py \
  operator_dashboard/test_local_ai_orchestrator_runtime_context_end_to_end_smoke_v1.py \
  operator_dashboard/test_local_ai_orchestrator_context_pack_end_to_end_smoke_v1.py \
  operator_dashboard/test_local_ai_orchestrator_button2_report_readiness_adapter_hook_v1.py \
  operator_dashboard/test_local_ai_orchestrator_button3_source_yield_adapter_hook_v1.py
```

Result: `175 passed, 0 failed`.

## Proof Highlights
- Approved-source event URL row enters Button 1 runtime context from feed file.
- Source-backed event/matchup rows carry accepted provenance fields.
- Mixed dry-run proof: URL-backed candidate enters `would_save`, non-URL candidate remains blocked.
- Existing local no-URL cohort remains blocked under Gate 1.

## Outcome
Button 1 now ingests approved-source live event URL rows (via governed approved-source feed artifacts), propagates URL-backed provenance into candidate rows, and preserves strict fail-closed/operator-approval governance.
