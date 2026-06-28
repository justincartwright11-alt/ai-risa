# Button 3 Result-Comparison Controlled Preview Endpoint/Dashboard Binding Discovery v1

## 1. Baseline
- branch: master
- HEAD: 99eb9a5
- tag: button3-result-comparison-controlled-preview-fail-closed-status-hardening-proof-and-review-v1

## 2. Purpose
This slice performs read-only discovery to identify the safest future endpoint and dashboard binding path for the hardened Button 3 result-comparison preview module.

The goal is to expose preview response visibility only, while preserving fail-closed behavior and blocking all mutation, learning, calibration, write, provider, and customer-output authority.

## 3. Source Artifacts Reviewed
- operator_dashboard/button3_result_comparison_preview_v1.py
- operator_dashboard/test_button3_result_comparison_preview_v1.py
- docs/button3_result_comparison_controlled_preview_fail_closed_status_hardening_proof_and_review_v1.md
- docs/button3_result_comparison_controlled_preview_implementation_readiness_gate_v1.md

## 4. Current Hardened Module
- Module: operator_dashboard/button3_result_comparison_preview_v1.py
- Test file: operator_dashboard/test_button3_result_comparison_preview_v1.py
- Focused test proof: 20/20 passed
- Four fail-closed conditions hardened:
  - partial evidence
  - unknown comparison_status
  - duplicate same-result evidence
  - stale-result evidence
- Current posture: preview-only, deterministic, operator-visible, non-mutating

## 5. Candidate Endpoint/Dashboard Surfaces

### A) operator_dashboard/app.py
- Why relevant:
  - Defines the hardened preview endpoint route `/api/button3/result-comparison/preview-v1`.
  - Contains Button 3 operator routes and route-level governance messaging.
  - Contains workflow preview endpoint `/api/local-ai/orchestrator/workflow-preview` currently used by normal dashboard Button 3 click path.
- Safe for future slice:
  - Yes, but only via minimal route-binding edits that keep response read-only and preserve existing route contracts.
- Currently dirty (from visible git status):
  - Yes.
- Risk level:
  - High (route-layer authority boundary, dirty-file contamination risk, cross-route regression risk).

### B) operator_dashboard/templates/index.html
- Why relevant:
  - Contains Button 3 UI panel text and preview field surface.
  - Contains Button 3 click handler path that currently requests workflow preview route with `source_button=button3_find_results`.
  - Is the direct dashboard wire point for exposing hardened result-comparison preview response without opening apply authority.
- Safe for future slice:
  - Yes, if edits remain narrow to Button 3 preview rendering and endpoint invocation only.
- Currently dirty (from visible git status):
  - Not visible as dirty in current status output.
- Risk level:
  - Medium-High (UI can accidentally imply apply authority or learning execution if copy/labels/wire are widened).

### C) operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
- Why relevant:
  - Already validates `/api/button3/result-comparison/preview-v1` behavior and no-apply endpoint posture.
  - Provides direct route-contract baseline for future endpoint/dashboard bind implementation.
- Safe for future slice:
  - Yes, required.
- Currently dirty (from visible git status):
  - Not visible as dirty in current status output.
- Risk level:
  - Low.

### D) operator_dashboard/test_operator_dashboard_button3_idiot_proof_review_results_flow_v1.py
- Why relevant:
  - Validates Button 3 preview flow, five-state summaries, and approval gate behavior.
  - Protects against accidentally treating preview as apply authority.
- Safe for future slice:
  - Yes, required for regression safety.
- Currently dirty (from visible git status):
  - Not visible as dirty in current status output.
- Risk level:
  - Low-Medium.

### E) operator_dashboard/test_local_ai_orchestrator_runtime_context_dashboard_wire_v1.py
- Why relevant:
  - Confirms normal dashboard Button 3 currently uses runtime-context workflow-preview wire.
  - Useful for controlled migration path or coexistence assertions when introducing explicit result-comparison preview binding.
- Safe for future slice:
  - Yes, if updated only to preserve and clarify non-mutating wire intent.
- Currently dirty (from visible git status):
  - Not visible as dirty in current status output.
- Risk level:
  - Medium (cross-button wire assumptions).

### F) operator_dashboard/test_button3_auto_result_source_yield_template_js_explicit_endpoint_wire_v1.py
- Why relevant:
  - Encodes current template endpoint wiring assumptions for Button 3 UI.
  - Must be considered when introducing or adjusting explicit preview endpoint/dashboard binding behavior.
- Safe for future slice:
  - Yes, if changed narrowly and kept read-only.
- Currently dirty (from visible git status):
  - Not visible as dirty in current status output.
- Risk level:
  - Medium (test contract drift if endpoint role split is not explicit).

## 6. Read-Only Binding Contract
Future binding must satisfy all of the following:
- accepts preview input only
- calls the hardened preview module only
- returns preview response only
- exposes `comparison_status` and provenance (`result_source_url`, `source_tier`)
- exposes blocked or fail-closed conditions clearly
- does not consume approval as execution authority
- does not mutate records
- does not write queues or databases
- does not update accuracy ledgers
- does not apply learning or calibration
- does not generate customer output
- does not authorize Button 1 source execution
- does not authorize Button 2 report generation

## 7. Blocked Surfaces
The following remain explicitly blocked in the future endpoint/dashboard binding slice:
- result apply endpoint
- official-result save/write endpoint
- accuracy-ledger mutation
- calibration mutation
- controlled-learning application
- customer PDF/report generation
- provider execution
- network/source calls
- Button 1 live-source authorization
- Button 2 output promotion

## 8. Future Implementation Slice Recommendation
Recommended next and only implementation slice:
- slice name: button3-result-comparison-controlled-preview-endpoint-dashboard-binding-implementation-v1

Exact allowed files:
- operator_dashboard/app.py
- operator_dashboard/templates/index.html
- operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
- operator_dashboard/test_operator_dashboard_button3_idiot_proof_review_results_flow_v1.py
- operator_dashboard/test_local_ai_orchestrator_runtime_context_dashboard_wire_v1.py
- operator_dashboard/test_button3_auto_result_source_yield_template_js_explicit_endpoint_wire_v1.py

Exact blocked files:
- operator_dashboard/button3_result_comparison_preview_v1.py
- operator_dashboard/test_button3_result_comparison_preview_v1.py
- operator_dashboard/button1_provider_adapter_execution_gate_v1.py
- operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- operator_dashboard/button2_template_pack_asset_renderer_v1.py
- operator_dashboard/button2_html_composition_entry_point_v1.py
- ops/approved_sources/button1_live_provider_registry.json
- all queue/database/storage writer modules
- all customer output generation/render/export modules outside existing read-only preview display

Required focused tests:
- endpoint contract tests for `/api/button3/result-comparison/preview-v1` remain pass
- dashboard Button 3 click wire tests remain pass with explicit preview-only semantics
- regression tests proving no apply endpoint is consumed by normal dashboard click path
- regression tests proving provenance and fail-closed statuses are rendered and not upgraded to apply authority
- regression tests proving no Button 1/2 authorization side effects

Required no-write checks:
- mutation_performed=false
- queue_write_performed=false
- learning_apply_performed=false
- calibration_write_performed=false
- button3_mutation_performed=false
- any ledger/database write sentinel remains false

Staged-set guard:
- staged set must match the exact allowed files list only
- any extra staged file is blocking failure
- any missing allowed file is blocking failure
- pre-existing dirty files remain unstaged and untouched

Abort conditions:
- any write/mutation/learning/calibration path opens
- any provider/network/source call introduced
- any apply authority implied from preview response or approval token
- any Button 1 or Button 2 authorization side effect introduced
- staged set differs from approved file scope
- pre-existing dirty file staged

Proposed commit message:
- Bind Button 3 result comparison preview endpoint to dashboard read-only flow

Proposed tag:
- button3-result-comparison-controlled-preview-endpoint-dashboard-binding-implementation-v1

## 9. Risks and Guardrails
- Risk: preview mistaken for apply authority.
  - Guardrail: explicit preview-only language in endpoint response and UI rendering.
- Risk: operator approval consumed as execution authority.
  - Guardrail: keep apply endpoint separate; no approval token consumption in preview path.
- Risk: dashboard accidentally implying learning.
  - Guardrail: explicit no-learning/no-calibration status copy in Button 3 panel.
- Risk: endpoint accidentally writing records.
  - Guardrail: require false no-write flags and test enforcement.
- Risk: stale or unknown result shown as ready.
  - Guardrail: preserve fail-closed status mapping and blocked-state rendering.
- Risk: dirty-file contamination.
  - Guardrail: strict staged-set equality check and immediate abort on mismatch.

## 10. Final Verdict
BUTTON3_RESULT_COMPARISON_CONTROLLED_PREVIEW_ENDPOINT_DASHBOARD_BINDING_DISCOVERY_LOCKED_READ_ONLY
