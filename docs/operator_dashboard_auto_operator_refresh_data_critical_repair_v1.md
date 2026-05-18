# Operator Dashboard Auto-Operator Refresh Data Critical Repair v1

## Slice
`operator-dashboard-auto-operator-refresh-data-critical-repair-v1`

## Objective
Implement a narrow, governance-safe repair for the confirmed blocker type:
- dashboard data hydration / auto-refresh / runtime-context data-contract mismatch

## Scope Implemented
1. Restored dashboard hydration on load and periodic refresh in main dashboard JS.
2. Normalized Button 1 summary fallback counters from `candidate_rows` when explicit discovered/extracted rows are absent.
3. Fixed Button 2 selected-fight derivation from current bout CSV schema (`red_fighter`/`blue_fighter`).
4. Added safe Button 3 missing-ledger zero-state handling via `source_status.accuracy_ledger_missing` and non-mutating zero-state reason metric.
5. Added/updated tests proving repaired behavior and preserving safety gates.

## Files Updated
- `operator_dashboard/templates/index.html`
- `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`
- `operator_dashboard/local_ai_orchestrator_engine_adapter_registry.py`
- `operator_dashboard/local_ai_orchestrator_input_context_pack.py`
- `operator_dashboard/test_local_ai_orchestrator_button1_discovery_readiness_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_button2_report_readiness_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_button3_source_yield_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_readonly_runtime_context_loader_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_runtime_context_dashboard_wire_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_context_pack_end_to_end_smoke_v1.py`

## Repair Details
### 1) Dashboard Hydration Surface
In `index.html`:
- Added card-health summary rows to all three button cards with required labels:
  - Button 1: Ready to save, Needs review, Blocked, Waiting for refresh
  - Button 2: Customer Ready, Not Ready, Waiting for refresh
  - Button 3: Rows scanned, Results found, Needs source, Conflicts, Ready to compare, Waiting for refresh
- Added load-time hydration calls for all three source buttons using runtime context:
  - `hydrateDashboardCardsOnLoad()` invoked at startup
  - `setInterval(hydrateDashboardCardsOnLoad, 30000)` for periodic refresh
- Added summary parsing and safe count coercion helpers.

### 2) Button 1 Counter Normalization
In adapter registry:
- `_button1_safe_summary(...)` now falls back to `candidate_rows` for discovered/extracted counts.
- Added conservative row-flag inference for readiness/blocked/needs-fixture where explicit counts are absent.

### 3) Button 2 Queue/Fight Derivation Fix
In runtime loader:
- Added `_build_fight_ref_from_row(...)` fallback to derive refs from `red_fighter` + `blue_fighter`.
- `selected_fight_refs` now include these derived refs when `fight_key`/`fight_name` are absent.

In adapter registry:
- `_button2_safe_summary(...)` now supports `selected_fight_refs` fallback.
- Inferred non-mutating readiness counters from selected/report/analysis/customer refs when explicit counters are absent.

### 4) Button 3 Missing Ledger Safe Zero-State
In runtime loader:
- Added `accuracy_ledger_missing` runtime-state flag.
- Propagated to Button 3 payload via `source_status.accuracy_ledger_missing`.

In input context pack:
- Allowed `source_status` through Button 3 payload sanitizer.

In adapter registry:
- Zero-waiting-rows path now sets metric `zero_state_reason`:
  - `accuracy_ledger_missing` when flagged
  - otherwise `no_waiting_rows`
- Summary remains safe and zeroed; no writes, no apply, no learning.

## Test Evidence
Targeted suite:
- `operator_dashboard/test_local_ai_orchestrator_button1_discovery_readiness_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_button2_report_readiness_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_button3_source_yield_adapter_hook_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_readonly_runtime_context_loader_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_runtime_context_dashboard_wire_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_context_pack_end_to_end_smoke_v1.py`

Result:
- `99 passed`

## Governance Confirmation
All approval-gate and non-mutation constraints remain intact:
- no save without approval
- no delivery without approval
- no result apply/learning/calibration without approval
- preview telemetry remains fail-closed and non-mutating

## Verdict
Critical repair scope implemented and tested.
Paid-pilot decision flow may proceed to next governance checkpoint review.
