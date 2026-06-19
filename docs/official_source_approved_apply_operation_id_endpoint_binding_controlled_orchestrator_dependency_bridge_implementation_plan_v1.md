# Official Source Approved Apply Operation ID Endpoint Binding Controlled Orchestrator Dependency Bridge Implementation Plan v1

## 1. Purpose
Plan the future controlled bridge implementation for the wider local-AI-orchestrator and Button 1 dependency cluster without copying files, modifying bridge payload, pushing, or creating a PR in this slice.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint 2b8a527
- tag official-source-approved-apply-operation-id-endpoint-binding-controlled-orchestrator-dependency-bridge-design-review-v1

## 3. Bridge Target
- bridge worktree should be recreated cleanly or reset from origin/master
- bridge branch: opid-pr-bridge-operation-id-v1 or a new clean replacement branch
- base: origin/master
- known base commit: 3782a8a
- known base tag: v100-release-pipeline-restored

## 4. Why Implementation Planning Is Required
- normal PR from opid-controlled-integration-v1-short to master failed twice
- bridge branch exposed wider orchestrator and Button 1 dependency cluster
- one-file copying is banned
- full import-closed allowlist must be approved before any future copying

## 5. Full Proposed Future Bridge Allowlist
1. button3_auto_result_source_yield_live_executor_preview.py
2. button3_improved_source_yield_engine.py
3. operator_dashboard/app.py
4. operator_dashboard/test_button3_apply_operation_id_endpoint_binding_v1.py
5. operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
6. operator_dashboard/test_button3_auto_result_source_yield_live_executor_flask_route_v1.py
7. operator_dashboard/local_ai_orchestrator_input_context_pack.py
8. operator_dashboard/local_ai_orchestrator_job_schema.py
9. operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
10. operator_dashboard/button1_auto_discovery_readiness_ranking_v1.py
11. operator_dashboard/button1_live_source_provider_orchestrator_v1.py
12. operator_dashboard/button1_approved_provider_config_registration_v1.py
13. operator_dashboard/button1_config_registration_to_orchestrator_registry_adapter_v1.py
14. operator_dashboard/button1_provider_adapter_execution_gate_v1.py
15. operator_dashboard/approved_combat_sport_source_registry.py
16. operator_dashboard/button1_approved_provider_config_validator_v1.py
17. all locked operation_id governance, proof, runbook, checklist, blocker, design, and review documents

## 6. Explicit Exclusions
- Button 2 artifacts
- live proof JSON artifacts
- pycache files
- unrelated dashboard, template, and provider expansion
- scoring, batch, ledger, prediction, and intake files outside the approved bridge cluster
- unrelated dirty-tree files
- stash contents
- original dirty worktree

## 7. Future Bridge Preparation Sequence
1. verify source branch is clean
2. remove or abandon dirty partial bridge worktree if necessary
3. create a clean bridge worktree from origin/master
4. copy the full import-closed allowlist in one controlled operation
5. verify diff is allowlist-only before running tests
6. run tests with PYTHONDONTWRITEBYTECODE=1
7. verify no post-test drift
8. commit and tag only if all gates pass
9. push only after commit and tag and clean status
10. create PR only after push succeeds

## 8. Required Test Gates
1. python -m pytest operator_dashboard/test_button3_apply_operation_id_endpoint_binding_v1.py operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py -q
2. python -m pytest operator_dashboard/test_button3_auto_result_source_yield_live_executor_flask_route_v1.py -q
3. import smoke test for local_ai_orchestrator_readonly_runtime_context_loader
4. import smoke test for Button 1 provider and orchestrator cluster
5. no post-test drift check

## 9. Required Invariant Gates
- token digest unchanged
- token consume unchanged
- authorization independence preserved
- mutation suppression preserved
- operation_id remains metadata-only
- no queue, database, customer-PDF, learning, or calibration writes
- no provider execution widening unless separately approved
- no Button 1 behavior change unless separately approved

## 10. Stop Conditions
- dirty source branch
- dirty or contaminated bridge branch
- out-of-allowlist file appears
- missing allowlist file
- failed import smoke test
- failed pytest gate
- post-test drift
- new dependency appears outside approved cluster
- pycache or runtime artifact appears
- mutation or write invariant drift
- branch or tag mismatch
- push failure
- PR creation failure

## 11. Implementation Planning Verdict
CONTROLLED_ORCHESTRATOR_DEPENDENCY_BRIDGE_IMPLEMENTATION_PLAN_READY_FOR_READINESS_GATE_ONLY
