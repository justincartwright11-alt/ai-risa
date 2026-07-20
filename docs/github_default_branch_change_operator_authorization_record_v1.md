# GitHub Default Branch Change Operator Authorization Record v1

## 1. Purpose
This document records explicit operator authorization for a future GitHub default branch settings change from master to ai-risa-mainline.

## 2. Record Boundary
This is a docs-only authorization record.

It does not authorize or perform:

- repository default branch change in this slice
- branch merge
- branch deletion
- branch rename
- pull request creation
- workflow modification
- additional workflow creation
- runtime changes
- test changes
- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Source Design and Review
Reference:

- docs/github_default_branch_change_authorization_design_v1.md
- docs/github_default_branch_change_authorization_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_OPERATOR_AUTHORIZATION_RECORD

## 5. Current Observed State
Current command evidence:

- current local branch: ai-risa-mainline
- repository default branch: master
- workflow path: .github/workflows/copilot-code-review.yml
- workflow file has local uncommitted changes: NO
- gh workflow view copilot-code-review.yml still returns 404: YES
- gh authentication is available: YES

## 6. Operator Authorization Record
Record exactly:

GITHUB_DEFAULT_BRANCH_CHANGE_AUTHORIZED=YES

AUTHORIZED_OLD_DEFAULT_BRANCH=master

AUTHORIZED_NEW_DEFAULT_BRANCH=ai-risa-mainline

MERGE_AUTHORIZED=NO

BRANCH_DELETE_AUTHORIZED=NO

CUSTOMER_RELEASE_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 7. Authorized Future Action
A later execution slice may change the repository default branch from master to ai-risa-mainline.

The authorized future command pattern is:

gh repo edit --default-branch ai-risa-mainline

Do not run that command in this slice.

## 8. Execution Preconditions for Later Slice
The later execution slice must confirm:

- gh auth status passes
- repository default branch is still master
- ai-risa-mainline exists on origin
- local active branch is ai-risa-mainline
- latest ai-risa-mainline commit is pushed
- workflow file exists on ai-risa-mainline
- no merge is required
- no branch deletion is required
- no workflow edit is required
- no customer release is implied
- no production launch is implied
- no learning activation is implied

## 9. Non-Goals Preserved
This authorization does not authorize:

- merging master and ai-risa-mainline
- reconciling unrelated histories
- deleting master
- renaming branches
- changing runtime code
- changing tests
- changing workflows
- customer release
- production launch
- learning activation

## 10. Post-Execution Verification Required Later
The later execution slice must verify:

- gh repo view --json nameWithOwner,defaultBranchRef
- gh workflow view copilot-code-review.yml

Expected after successful execution:

REPOSITORY_DEFAULT_BRANCH=ai-risa-mainline

WORKFLOW_VIEW_BLOCKER_CONFIRMED=NO

## 11. Authorization Decision
OPERATOR_AUTHORIZATION_RECORDED_FOR_EXECUTION_SLICE

## 12. Recommended Next Slice
Recommended next slice:

github_default_branch_change_execution_v1

The next slice may execute the default branch setting change only within the authorization and non-goals recorded here.

## 13. Slice Integrity
DOCS_CHANGED=YES
DEFAULT_BRANCH_CHANGED=NO
MERGE_PERFORMED=NO
PR_CREATED=NO
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY