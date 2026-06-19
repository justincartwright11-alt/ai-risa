# Official Source Approved Apply Operation ID Endpoint Binding App Import Isolation Lazy-Load Design v1

## 1. Purpose
Design a narrow app.py import isolation and lazy-load strategy so operation_id endpoint-binding tests can collect without importing unrelated Button 2, global, or orchestrator chains.

This is design-only. It does not edit app.py, edit tests, copy files, or modify bridge payload.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint 783d63e
- tag official-source-approved-apply-operation-id-endpoint-binding-app-import-surface-blocker-and-allowlist-amendment-decision-v1

## 3. Problem Statement
- bridge v2 passed corrected import smoke
- pytest collection imports operator_dashboard/app.py
- app.py imports unrelated Gate1, global, Button1, Button2, and Button3 modules at module load time
- this forces operation_id tests to require a much larger Button 2/global chain
- this conflicts with the narrow operation_id bridge scope and prior Button 2 exclusions

## 4. Design Objective
- preserve narrow operation_id endpoint-binding scope
- allow operation_id tests to collect without requiring unrelated Button 2/global/orchestrator imports
- avoid widening bridge allowlist into Button 2 chain
- keep runtime behavior unchanged unless the affected route or function is actually invoked

## 5. Proposed Strategy
- move non-essential heavy imports from app.py top-level into the specific route or function that needs them
- keep operation_id endpoint-binding imports explicit and minimal
- preserve existing route behavior by importing dependencies lazily at call time
- fail closed if a lazily imported dependency is missing when its route is invoked
- do not silently disable features
- do not mutate data
- do not alter authorization or token behavior

## 6. Candidate Imports for Lazy Loading
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

## 7. Imports That May Remain Top-Level for Current Bridge
- local_ai_orchestrator_input_context_pack.py
- local_ai_orchestrator_readonly_runtime_context_loader.py
- local_ai_orchestrator_job_schema.py
- approved operation_id endpoint-binding dependencies

## 8. Non-Goals
- no Button 2 implementation
- no Button 2 bridge expansion
- no provider execution widening
- no Button 1 behavior change
- no queue, database, customer-PDF, learning, or calibration writes
- no route behavior rewrite beyond import timing
- no mutation or write expansion

## 9. Test Design
- app.py import smoke should pass with only narrow operation_id bridge allowlist
- operation_id endpoint-binding tests should collect and run
- routes using lazy imports should still fail closed if dependencies are absent
- existing routes should retain behavior when dependencies are present
- no post-test drift with PYTHONDONTWRITEBYTECODE=1

## 10. Invariants
- token digest unchanged
- token consume unchanged
- authorization independence preserved
- operation_id remains metadata-only
- mutation suppression preserved
- no queue, database, customer-PDF, learning, or calibration writes
- no hidden Button 2 behavior activation
- no silent feature disabling

## 11. Risk Assessment
- lazy imports can hide missing dependencies until route invocation
- route-level fail-closed handling must be explicit
- tests must cover import-time collection and route invocation where applicable
- design must not make operation_id endpoint depend on unrelated route modules

## 12. Stop Conditions for Future Implementation
- app.py diff changes behavior beyond import timing
- operation_id tests require Button 2 imports
- lazy import swallows errors silently
- missing dependency returns success
- any mutation or write invariant changes
- any out-of-scope Button 2 route implementation occurs

## 13. Design Verdict
APP_IMPORT_ISOLATION_LAZY_LOAD_DESIGN_READY_FOR_REVIEW_ONLY
