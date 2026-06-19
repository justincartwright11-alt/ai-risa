# Official Source Approved Apply Operation ID Endpoint Binding App Import Isolation Lazy-Load Implementation Plan v1

## 1. Purpose
Plan the future app.py lazy-load implementation that will allow operation_id endpoint-binding tests to collect without requiring unrelated Gate1, global, Button1, Button2, and Button3 import chains.

This is docs-only. It does not edit app.py, edit tests, copy files, or modify bridge payload.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint 7fe28ed
- tag official-source-approved-apply-operation-id-endpoint-binding-app-import-isolation-lazy-load-design-review-v1

## 3. Inputs Reviewed
- app import-surface blocker and allowlist-amendment decision
- app import isolation and lazy-load design
- app import isolation and lazy-load design review

## 4. Why Implementation Planning Is Required
- bridge v2 passed corrected import smoke
- pytest collection imports app.py
- app.py top-level imports unrelated Gate1, global, Button1, Button2, and Button3 modules
- this forces operation_id tests into a wider Button 2 and global chain
- the approved design review selected lazy-load import isolation as the narrow path

## 5. Future Implementation Target
- operator_dashboard/app.py only, unless implementation planning discovers a necessary test-only helper
- no bridge payload changes in this planning slice
- no dependency copying in this planning slice

## 6. Candidate Top-Level Imports to Move to Lazy Route or Function Scope
- local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview.py
- local_ai_orchestrator_gate1_approved_save_writer.py
- local_ai_orchestrator_workflow_plan.py
- global_fighter_identity_resolver_preview.py
- global_fighter_known_records_readonly_loader.py
- button1_to_button2_readonly_dossier_handoff_preview.py
- button2_readonly_dossier_handoff_ingest_preview.py
- button2_dossier_handoff_report_context_preview.py
- button2_report_generation_route_render_gate_integration_v1.py
- button2_customer_flow_dry_run_contract_preview_v1.py
- button2_pdf_output_root_config_v1.py
- button2_controlled_delivery_scaffold.py
- button2_template_pack_asset_renderer_v1.py
- button3_result_comparison_preview_v1.py
- button2_queue_loader_readonly_v1.py

## 7. Imports Allowed to Remain Top-Level
- local_ai_orchestrator_input_context_pack.py
- local_ai_orchestrator_readonly_runtime_context_loader.py
- local_ai_orchestrator_job_schema.py
- approved operation_id endpoint-binding dependencies
- standard library imports
- Flask and app framework imports already required for app creation

## 8. Implementation Approach
- move each candidate import into the smallest route or function scope that uses it
- preserve current symbol names where possible
- avoid changing route signatures
- avoid changing response shapes except explicit fail-closed missing-dependency errors for routes whose lazy dependency is unavailable
- no silent pass or fallback when a required dependency is missing
- no mutation or write behavior change
- no Button 2 route implementation change beyond import timing

## 9. Fail-Closed Handling
- missing lazy dependency must return explicit route-local error only when that route is invoked
- operation_id route collection must not require unrelated lazy dependencies
- missing lazy dependency must not return success
- missing lazy dependency must not mutate data

## 10. Required Future Test Gates
- app.py import smoke with narrow operation_id bridge allowlist
- operation_id endpoint-binding pytest gate
- Button 3 controlled preview path pytest gate
- Button 3 auto result source yield live executor route pytest gate
- route-local missing-dependency fail-closed tests for lazy imports if practical
- no post-test drift check with PYTHONDONTWRITEBYTECODE=1

## 11. Required Invariant Gates
- token digest unchanged
- token consume unchanged
- authorization independence preserved
- operation_id remains metadata-only
- mutation suppression preserved
- no queue, database, customer-PDF, learning, or calibration writes
- no hidden Button 2 behavior activation
- no silent feature disabling
- no provider execution widening
- no Button 1 behavior change

## 12. Future Execution Sequence
- create readiness gate first
- then implement only in a clean controlled source and bridge path
- patch app.py only
- run import smoke before pytest
- run locked pytest gates
- check no post-test drift
- commit and tag only if all gates pass
- update bridge only after source implementation is locked and reviewed

## 13. Stop Conditions
- app.py diff changes behavior beyond import timing
- operation_id tests still require Button 2 imports
- lazy import swallows errors silently
- missing dependency returns success
- any mutation or write invariant changes
- any out-of-scope Button 2 implementation occurs
- any new dependency introduced outside design scope
- pytest collection still fails from app.py import surface
- post-test drift
- dirty source or bridge branch

## 14. Planning Verdict
APP_IMPORT_ISOLATION_LAZY_LOAD_IMPLEMENTATION_PLAN_READY_FOR_READINESS_GATE_ONLY
