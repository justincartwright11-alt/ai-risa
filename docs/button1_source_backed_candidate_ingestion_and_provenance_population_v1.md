# Button1 Source-Backed Candidate Ingestion and Provenance Population v1

## Scope
Implement a safe ingestion bridge so Button1 candidate rows can inherit real, explicit event-level URL provenance when available, without weakening Gate1 provenance rules.

## Problem
Button1 candidate rows sourced from local unresolved queues often contain only `source_tag` and `source_notes`. Those fields are intentionally non-authoritative and must remain blocked by Gate1 provenance checks.

## Implementation
- File updated: `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`
- Added URL extraction and event-level provenance lookup helpers:
  - `_extract_row_provenance_urls`
  - `_build_event_provenance_lookup`
  - `_propagate_event_provenance`
- `build_button1_runtime_context` now:
  - builds event URL lookup from discovered event rows
  - propagates event-level URLs to matching candidate rows by `event_name` only when explicit URLs exist
  - preserves existing strict normalization

## Safety/Governance Guarantees
- No synthetic/fake URLs are generated.
- Rows with only `source_tag`/`source_notes` remain non-provenanced and blocked.
- Gate1 dry-run and approved-save writer logic were not loosened.
- No filesystem writes or live web calls added.

## Verification
Executed:

```bash
C:/Users/jusin/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest \
  operator_dashboard/test_local_ai_orchestrator_readonly_runtime_context_loader_v1.py \
  operator_dashboard/test_local_ai_orchestrator_gate1_dry_run_apply_preview_api_v1.py \
  operator_dashboard/test_local_ai_orchestrator_gate1_approved_save_writer_api_preview_v1.py \
  operator_dashboard/test_local_ai_orchestrator_button2_report_readiness_adapter_hook_v1.py \
  operator_dashboard/test_local_ai_orchestrator_button3_source_yield_adapter_hook_v1.py
```

Result: `94 passed`.

## New Proof Points Added
- Event-level URL provenance propagates to matching local candidate rows.
- Event-level propagation does not occur when event rows do not contain explicit URLs.
- Existing cohort-without-URLs remains blocked in Gate1 dry-run and approved-save preview tests.

## Outcome
Button1 now supports source-backed provenance population through ingestion-ready event URL evidence while preserving strict fail-closed behavior when evidence is absent.
