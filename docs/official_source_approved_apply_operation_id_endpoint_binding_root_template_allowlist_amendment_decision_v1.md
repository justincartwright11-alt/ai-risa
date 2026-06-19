# Official Source Approved Apply Operation ID Endpoint Binding Root Template Allowlist Amendment Decision v1

## 1. Purpose
Record a docs-only governance decision to amend the controlled bridge allowlist by one bounded template file, `operator_dashboard/templates/index.html`, after a root-route template-rendering blocker was isolated to that file only.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint c79c9eb
- tag official-source-approved-apply-operation-id-endpoint-binding-button3-result-comparison-preview-allowlist-amendment-decision-v1

## 3. Bridge Checkpoint
- worktree C:\risa-opid-pr-bridge-v4
- branch opid-pr-bridge-operation-id-v4
- base origin/master
- base commit 3782a8a
- base tag v100-release-pipeline-restored
- copied amended allowlist payload remains uncommitted

## 4. Current Bridge Rerun Status
- fresh bridge v4 created from origin/master
- amended payload copied
- import smoke passed
- first locked pytest gate failed during root route rendering
- no commit/tag/push/PR occurred

## 5. Failed Route/Test Area
- operator_dashboard/test_button3_result_comparison_controlled_preview_path_v1.py
- client.get("/") reached root route rendering

## 6. Blocker
- jinja2.exceptions.TemplateNotFound: index.html

## 7. Dependency Review Findings
- app.py uses Flask(__name__, template_folder="templates")
- root route renders index.html
- required file is operator_dashboard/templates/index.html
- file exists and is tracked in source
- file is missing from bridge v4
- file is missing from origin/master
- template has no url_for references
- template has no static references
- no additional static assets required for the locked pytest gate
- no Button 2 dependency expansion
- no Gate1/global/queue/database/learning conflict

## 8. Scope Decision
- bounded one-file template allowlist amendment
- no static directory admitted
- no Button 2 files admitted
- no Gate1/global/Button1/Button2 expansion admitted
- no queue/database/customer-PDF/learning/calibration writes admitted
- no provider execution expansion admitted

## 9. Amended Bridge Allowlist Addition
- operator_dashboard/templates/index.html

## 10. Updated Copied Bridge Payload Count
- prior copied bridge list: 47 entries
- amended copied bridge list: 48 entries

## 11. Required Future Bridge Rerun Gates
- verify source clean at this decision checkpoint
- use a fresh bridge v5 from origin/master if bridge v4 remains dirty/uncommitted
- copy exactly amended 48-entry bridge list
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
- no static asset expansion

## 13. Decision
ROOT_TEMPLATE_INDEX_ALLOWLIST_AMENDMENT_APPROVED_AS_BOUNDED_ONE_FILE_DECISION

## 14. Safe Next Action
- rerun controlled bridge using amended 48-entry copied bridge list
- preferably use fresh bridge v5 from origin/master if bridge v4 remains dirty/uncommitted
