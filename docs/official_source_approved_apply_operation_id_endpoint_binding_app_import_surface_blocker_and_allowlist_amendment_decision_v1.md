# Official Source Approved Apply Operation ID Endpoint Binding App Import Surface Blocker And Allowlist Amendment Decision v1

## 1. Purpose
Record a docs-only governance decision that the current controlled bridge allowlist is blocked by the real `app.py` import surface, and define formal next options without any additional bridge copying.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint 2497084
- tag official-source-approved-apply-operation-id-endpoint-binding-controlled-orchestrator-dependency-bridge-implementation-readiness-gate-v1

## 3. Bridge Checkpoint
- worktree C:\risa-opid-pr-bridge-v2
- branch opid-pr-bridge-operation-id-v2
- base origin/master
- base commit 3782a8a
- base tag v100-release-pipeline-restored
- copied 39-file allowlist remains uncommitted

## 4. Execution History Summary
- bridge v2 created cleanly from origin/master
- 39 approved allowlist files copied in one controlled operation
- allowlist-only diff passed
- corrected import smoke passed
- first locked pytest gate failed during collection
- no commit/tag/push/PR occurred

## 5. Current Pytest Blocker
- initial missing module: operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview
- downstream: operator_dashboard.local_ai_orchestrator_gate1_token_check

## 6. App.py Import Surface Inventory Result
Satisfied by bridge:
- local_ai_orchestrator_input_context_pack.py
- local_ai_orchestrator_readonly_runtime_context_loader.py
- local_ai_orchestrator_job_schema.py

Missing from bridge v2 and origin/master:
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

## 7. Downstream Dependency Expansion
- local_ai_orchestrator_gate1_token_check.py
- local_ai_orchestrator_preview_runner.py
- global_fighter_known_records_source_pack_preview.py
- additional Button2 route/render/PDF/delivery chain files

## 8. Governance Conflict
- previous bridge design excluded Button 2 artifacts
- app.py import surface now requires Button 2-related modules for test collection
- continuing with the existing allowlist would be misleading and incomplete
- opportunistic copying remains prohibited

## 9. Decision
STOP_CURRENT_BRIDGE_IMPLEMENTATION_PENDING_APP_IMPORT_SURFACE_DECISION

## 10. Two Formal Next Options
Option A - Redesign or guard import path:
- isolate or lazy-load app.py imports so operation_id tests do not require unrelated Button 2/global/orchestrator modules during collection
- requires separate design, review, readiness gate, and implementation plan
- preserves narrower operation_id PR scope

Option B - Scope expansion:
- formally approve a much larger import-closed bridge allowlist covering app.py import surface and downstream Button 2/global/orchestrator dependencies
- requires new full inventory, design, review, readiness gate, and implementation plan
- PR must not claim narrow operation_id-only scope

## 11. Blocked Actions
- no further bridge copying
- no bridge commit
- no bridge push
- no PR creation
- no merge
- no rebase
- no cherry-pick
- no stash pop/apply

## 12. Safe Next Recommendation
Prefer Option A: docs-only app.py import isolation or lazy-load design for operation_id tests.

Rationale:
- preserves narrow operation_id endpoint-binding scope
- avoids importing Button 2 chain into this PR

## 13. Final Verdict
APP_IMPORT_SURFACE_BLOCKS_CURRENT_CONTROLLED_BRIDGE_ALLOWLIST
