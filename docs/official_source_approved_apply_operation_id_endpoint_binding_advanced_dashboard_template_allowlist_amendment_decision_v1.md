# Official Source Approved Apply Operation ID Endpoint Binding Advanced Dashboard Template Allowlist Amendment Decision v1

## 1. Purpose
Record a docs-only governance decision to amend the controlled bridge allowlist by one bounded template file, `operator_dashboard/templates/advanced_dashboard.html`, after a root route blocker was isolated to that file only.

## 2. Source Checkpoint
- worktree C:\risa-opid-int-v1
- branch opid-controlled-integration-v1-short
- checkpoint e6162b4
- tag official-source-approved-apply-operation-id-endpoint-binding-root-template-allowlist-amendment-decision-v1

## 3. Bridge Checkpoint
- worktree C:\risa-opid-pr-bridge-v5
- branch opid-pr-bridge-operation-id-v5
- base origin/master
- base commit 3782a8a
- base tag v100-release-pipeline-restored
- copied 49-entry payload remains uncommitted

## 4. Current Bridge Rerun Status
- fresh bridge v5 created from origin/master
- 49-entry copied payload landed
- import smoke passed
- first locked pytest gate passed
- second locked pytest gate failed during advanced dashboard route rendering
- no commit/tag/push/PR occurred

## 5. Failed Route/Test Area
- operator_dashboard/test_button3_auto_result_source_yield_live_executor_flask_route_v1.py
- client.get("/advanced-dashboard") reached advanced dashboard route rendering

## 6. Blocker
- jinja2.exceptions.TemplateNotFound: advanced_dashboard.html

## 7. Dependency Review Findings
- app.py renders advanced_dashboard.html from template_folder="templates"
- required file is operator_dashboard/templates/advanced_dashboard.html
- file exists and is tracked in source
- file is missing from bridge v5
- file is missing from origin/master
- template has no url_for references
- template has no static references
- template has no extends/include references
- no additional static assets required for the locked pytest gate
- no Button 2 dependency expansion
- no Gate1/global/queue/database/learning conflict

## 8. Scope Decision
- bounded one-file template allowlist amendment
- no static directory admitted
- no template directory expansion admitted
- no Button 2 files admitted
- no Gate1/global/Button1→Button2 expansion admitted
- no queue/database/customer-PDF/learning/calibration writes admitted
- no provider execution expansion admitted

## 9. Amended Bridge Allowlist Addition
- operator_dashboard/templates/advanced_dashboard.html

## 10. Updated Copied Bridge Payload Count
- prior copied bridge list: 49 entries
- amended copied bridge list: 50 entries

## 11. Required Future Bridge Rerun Gates
- verify source clean at this decision checkpoint
- use a fresh bridge v6 from origin/master if bridge v5 remains dirty/uncommitted
- copy exactly amended 50-entry bridge list
- enforce copied-list-only diff
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
- no template directory expansion

## 13. Decision
ADVANCED_DASHBOARD_TEMPLATE_ALLOWLIST_AMENDMENT_APPROVED_AS_BOUNDED_ONE_FILE_DECISION

## 14. Safe Next Action
- rerun controlled bridge using amended 50-entry copied bridge list
- preferably use fresh bridge v6 from origin/master if bridge v5 remains dirty/uncommitted
