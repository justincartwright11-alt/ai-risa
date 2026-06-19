# Official Source Approved Apply Operation ID Endpoint Binding Controlled Orchestrator Dependency Bridge Design v1

## 1. Purpose
Define a design-only, controlled bridge strategy for the wider local-AI-orchestrator and Button 1 dependency cluster exposed by the operation_id PR bridge attempt.

This design does not copy files, does not modify bridge payload, and does not execute implementation.

## 2. Source Checkpoint and Bridge Checkpoint
- Source worktree: C:\risa-opid-int-v1
- Source branch: opid-controlled-integration-v1-short
- Source checkpoint: 8738049
- Source tag: official-source-approved-apply-operation-id-endpoint-binding-pr-bridge-wider-orchestrator-dependency-blocker-decision-v1
- Bridge worktree: C:\risa-opid-pr-bridge-v1
- Bridge branch: opid-pr-bridge-operation-id-v1
- Bridge base: origin/master
- Bridge base commit: 3782a8a
- Bridge base tag: v100-release-pipeline-restored

## 3. Why This Design Exists
A normal PR from opid-controlled-integration-v1-short to master failed twice because GitHub reported no shared history. A bridge branch from origin/master was created. During bridge expansion, a wider orchestrator dependency cluster surfaced, making one-file opportunistic copying unsafe.

## 4. Failure Chain from Original PR to Bridge Dependency Expansion
1. Clean source branch prepared with approved operation_id endpoint-binding payload and governance artifacts.
2. External PR creation to master failed twice due no shared history.
3. Bridge branch created from origin/master.
4. Narrow dependency copying began to satisfy import failures for locked tests.
5. Additional dependencies surfaced in sequence.
6. Loader dependency introduced a wider Button 1 and orchestrator cluster.
7. Inventory confirmed multiple required files are missing from origin/master.
8. Governance decision: stop one-file expansion and move to controlled bridge design.

## 5. Cluster Inventory Summary
Known cluster files missing from origin/master:
1. operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
2. operator_dashboard/button1_auto_discovery_readiness_ranking_v1.py
3. operator_dashboard/button1_live_source_provider_orchestrator_v1.py
4. operator_dashboard/button1_approved_provider_config_registration_v1.py
5. operator_dashboard/button1_config_registration_to_orchestrator_registry_adapter_v1.py
6. operator_dashboard/button1_provider_adapter_execution_gate_v1.py

Second-order dependencies:
1. operator_dashboard/approved_combat_sport_source_registry.py
2. operator_dashboard/button1_approved_provider_config_validator_v1.py
3. operator_dashboard/local_ai_orchestrator_job_schema.py

Already present in bridge allowlist from previous attempts:
1. operator_dashboard/app.py
2. operator_dashboard/test_button3_apply_operation_id_endpoint_binding_v1.py
3. operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
4. operator_dashboard/test_button3_auto_result_source_yield_live_executor_flask_route_v1.py
5. button3_auto_result_source_yield_live_executor_preview.py
6. button3_improved_source_yield_engine.py
7. operator_dashboard/local_ai_orchestrator_input_context_pack.py
8. operator_dashboard/local_ai_orchestrator_job_schema.py
9. operation_id governance, proof, runbook, checklist, and blocker documents

## 6. Proposed Controlled Bridge Boundary
Proposed boundary for future controlled bridge slice:
- Include only the minimum import-closed cluster needed to allow app import and locked operation_id and Button 3 gates to run.
- Restrict scope to import closure of the loader path and explicitly named dependencies.
- Forbid unrelated feature expansion, UI/dashboard wiring changes, and provider behavior redesign.
- Preserve operation_id scope objective: additive endpoint-binding behavior with governance invariants.

## 7. Files Eligible for a Future Controlled Bridge Slice
Eligibility is review-only until explicit approval is granted.

Primary cluster candidates:
1. operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
2. operator_dashboard/button1_auto_discovery_readiness_ranking_v1.py
3. operator_dashboard/button1_live_source_provider_orchestrator_v1.py
4. operator_dashboard/button1_approved_provider_config_registration_v1.py
5. operator_dashboard/button1_config_registration_to_orchestrator_registry_adapter_v1.py
6. operator_dashboard/button1_provider_adapter_execution_gate_v1.py

Second-order cluster candidates:
1. operator_dashboard/approved_combat_sport_source_registry.py
2. operator_dashboard/button1_approved_provider_config_validator_v1.py
3. operator_dashboard/local_ai_orchestrator_job_schema.py

Previously allowlisted payload remains in-scope only as already staged for bridge diagnostics, not as approval for further widening.

## 8. Files Explicitly Excluded
- Any files outside the approved full cluster allowlist for the future controlled slice.
- Any Button 2 artifacts, dashboard/template/provider files not required by import closure.
- Any pycache artifacts.
- Any live proof JSON artifacts.
- Any scoring, batch, ledger, prediction, or intake files outside approved import closure.
- Any runtime mutation wiring or behavior changes not separately approved.

## 9. Required Preconditions Before Any Future Copying
1. Source branch clean.
2. Bridge branch recreated cleanly from origin/master or reset to known clean base.
3. Full cluster allowlist approved before copying.
4. No one-file opportunistic dependency expansion.
5. Tests defined before copying.
6. No bridge push or PR until all gates pass.

## 10. Required Test Gates
1. operation_id endpoint-binding tests.
2. Button 3 controlled preview path tests.
3. Button 3 auto result source yield live executor route tests.
4. Orchestrator dependency cluster import smoke tests if present.
5. No post-test drift check with PYTHONDONTWRITEBYTECODE=1.

## 11. Mutation and Write Invariants
- Preserve metadata-only operation_id behavior.
- Preserve token digest and token consume behavior.
- Preserve authorization independence.
- Preserve mutation suppression and write suppression in preview paths.
- No queue or database writes introduced by dependency bridge slice.
- Preserve audit and provenance traceability.

## 12. Stop Conditions
Stop future controlled bridge execution immediately if any condition occurs:
1. Any file outside approved full cluster allowlist appears.
2. Any required gate fails.
3. Any post-test drift appears.
4. Any mutation or write invariant drifts.
5. Any new dependency outside approved cluster appears.
6. Bridge target is not clean base.
7. Evidence of contamination from unrelated tracks.

## 13. Risk Assessment
- Current dependency cluster is wider than the narrow operation_id bridge intent.
- Continued one-file copying creates uncontrolled subsystem ingestion risk.
- Missing-on-master cluster breadth increases merge and regression risk.
- Controlled boundary and pre-approved cluster inventory reduce risk and preserve governance.

## 14. Design Verdict
CONTROLLED_ORCHESTRATOR_DEPENDENCY_BRIDGE_DESIGN_READY_FOR_REVIEW_ONLY

## Blocked Actions for This Design Slice
1. No copying from this design slice.
2. No bridge commit.
3. No bridge push.
4. No PR creation.
5. No merge.
6. No runtime mutation widening.
7. No Button 1 behavior change unless separately approved.
