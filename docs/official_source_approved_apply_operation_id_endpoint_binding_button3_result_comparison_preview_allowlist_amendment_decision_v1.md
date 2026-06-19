# Official Source Approved Apply Operation ID Endpoint Binding Button 3 Result Comparison Preview Allowlist Amendment Decision v1

## 1. Purpose
Record a docs-only governance decision to amend the controlled bridge allowlist by one bounded Button 3 preview file, `operator_dashboard/button3_result_comparison_preview_v1.py`, after a route-invocation blocker was isolated to that file only.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint 5ed2a41
- tag official-source-approved-apply-operation-id-endpoint-binding-app-import-isolation-lazy-load-implementation-review-and-proof-v1

## 3. Bridge Checkpoint
- worktree C:\risa-opid-pr-bridge-v3
- branch opid-pr-bridge-operation-id-v3
- base origin/master
- base commit 3782a8a
- base tag v100-release-pipeline-restored
- current 45-file allowlist payload remains uncommitted

## 4. Current Bridge Rerun Status
- clean bridge v3 created from origin/master
- 45 approved allowlist files copied
- allowlist-only diff passed
- import smoke passed
- first locked pytest gate failed during Button 3 result-comparison route invocation
- no commit/tag/push/PR occurred

## 5. Failed Route/Test Area
- operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
- app.py lazy-loads operator_dashboard.button3_result_comparison_preview_v1 during Button 3 result-comparison route invocation

## 6. Blocker
- ModuleNotFoundError: No module named 'operator_dashboard.button3_result_comparison_preview_v1'

## 7. Dependency Review Findings
- operator_dashboard/button3_result_comparison_preview_v1.py exists and is tracked in source
- missing from bridge v3
- missing from origin/master
- present on origin/opid-controlled-integration-v1-short
- history includes governed preview path lineage, including commit 9069050
- only import is standard-library typing
- no project-local downstream dependencies
- no Button 2 dependency expansion
- no conflict with Button 2 exclusions

## 8. Scope Decision
- bounded one-file Button 3 allowlist amendment
- no Button 2 files admitted
- no Gate1/global/Button1/Button2 expansion admitted
- no queue/database/customer-PDF/learning/calibration writes admitted
- no provider execution expansion admitted

## 9. Amended Bridge Allowlist Addition
- operator_dashboard/button3_result_comparison_preview_v1.py

## 10. Updated Bridge Allowlist Count
- prior allowlist: 45 files
- amended allowlist: 46 files

## 11. Required Future Bridge Rerun Gates
- verify source clean at this decision checkpoint
- verify bridge v3 state or recreate clean bridge v4 if needed
- copy exactly amended 46-file allowlist
- enforce allowlist-only diff
- import smoke including operator_dashboard.app
- locked pytest gate 1
- locked pytest gate 2
- no post-test drift
- commit/tag/push/PR only if all gates pass

## 12. Blocked Actions
- no direct copying in this docs slice
- no bridge commit in this docs slice
- no bridge push in this docs slice
- no PR in this docs slice
- no merge/rebase/cherry-pick/stash pop
- no Button 2 expansion

## 13. Decision
BUTTON3_RESULT_COMPARISON_PREVIEW_ALLOWLIST_AMENDMENT_APPROVED_AS_BOUNDED_ONE_FILE_DECISION

## 14. Safe Next Action
- rerun controlled bridge using amended 46-file allowlist
- preferably use a fresh bridge v4 from origin/master if bridge v3 remains dirty/uncommitted