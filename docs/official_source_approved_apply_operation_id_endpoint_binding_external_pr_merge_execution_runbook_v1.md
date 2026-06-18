# Official Source Approved Apply Operation ID Endpoint Binding External PR Merge Execution Runbook v1

## 1) Runbook Scope
This runbook defines the external PR merge execution process for the locked operation_id endpoint-binding chain.

Scope controls:
- Docs-only governance slice.
- No production code or test modifications.
- No merge/cherry-pick/rebase in this slice.
- No stash pop/apply.
- Original dirty worktree excluded.
- No behavior changes across endpoint, mutation, token digest, token consume, authorization, UI, scoring, batch, dashboard, ledger, prediction, intake, learning, calibration, queue, database, or provider paths.

## 2) Clean Release Branch Source
- Worktree: C:\risa-opid-int-v1
- Branch: opid-controlled-integration-v1-short
- Commit: 8d076f0
- Tag: official-source-approved-apply-operation-id-endpoint-binding-reviewer-signoff-record-v1

## 3) Final Governance Chain
- d94e17b design
- cb119ed design review
- edc7142 implementation readiness gate
- 846ac40 implementation plan
- 69511a0 implementation
- 08aaaac implementation proof
- a02a0c8 release readiness gate
- c4099bc merge/handoff plan
- b7b1287 clean target handoff execution
- 9f61020 post-handoff verification and merge proof
- e2d9ca5 controlled integration execution
- ad61745 merge-readiness proof
- a82143e downstream controlled merge preflight
- 0790ec3 downstream controlled merge planning/execution gate
- 6953aa2 controlled downstream merge action proof
- 53f390c clean-release PR handoff packet
- 8d076f0 reviewer signoff record

## 4) Required Final Pre-Merge Command Order
1. Verify branch and tag.
2. Verify clean status.
3. Verify allowlist diff.
4. Rerun 78-test gate with `PYTHONDONTWRITEBYTECODE=1`.
5. Verify no post-test drift.
6. Verify merge target is clean.
7. Verify no stash pop/apply.
8. Verify original dirty worktree is not used.

## 5) Exact Test Commands
1. `python -m pytest operator_dashboard/test_button3_apply_operation_id_endpoint_binding_v1.py operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py -q`
2. `python -m pytest operator_dashboard/test_button3_auto_result_source_yield_live_executor_flask_route_v1.py -q`

## 6) Approved PR Payload
- operator_dashboard/app.py
- operator_dashboard/test_button3_apply_operation_id_endpoint_binding_v1.py
- All operation_id governance/proof/runbook docs in the locked chain.

## 7) Excluded PR Payload
- Original dirty worktree.
- Stash contents.
- Button 2 artifacts.
- Live proof JSON artifacts.
- pycache files.
- Dashboard/template/provider files.
- Scoring/batch/ledger/prediction/intake files outside locked operation_id chain.
- Unrelated dirty-tree files.

## 8) Abort Matrix
- Abort if target tree is dirty.
- Abort if branch/tag mismatch occurs.
- Abort if unexpected file outside allowlist appears.
- Abort if 78-test gate fails.
- Abort if post-test drift appears.
- Abort if token digest drift appears.
- Abort if token consume drift appears.
- Abort if authorization semantics drift.
- Abort if mutation/write behavior changes.
- Abort if dashboard/provider/Button 2 contamination appears.
- Abort if stash is popped/applied.
- Abort if original dirty worktree is used.

## 9) Reviewer Signoff Dependency
- Required signoff record checkpoint: 8d076f0.
- Decision at that checkpoint: GO_FOR_REVIEW_ONLY.
- This is not direct merge authorization.

## 10) Final Runbook Verdict
EXTERNAL_PR_MERGE_EXECUTION_RUNBOOK_READY_FOR_CLEAN_PR_PROCESS_ONLY
