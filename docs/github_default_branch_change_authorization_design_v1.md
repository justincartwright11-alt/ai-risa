# GitHub Default Branch Change Authorization Design v1

## 1. Purpose
This document designs the authorization path for changing the GitHub repository default branch from master to ai-risa-mainline.

## 2. Design Boundary
This is docs-only design.

It does not authorize:

- repository default branch change
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
- repository settings changes

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Source Precheck
Reference:

- docs/github_actions_default_branch_alignment_precheck_v1.md

CURRENT_BRANCH=ai-risa-mainline

REPOSITORY_DEFAULT_BRANCH=master

DEFAULT_BRANCH_MISMATCH_CONFIRMED=YES

WORKFLOW_VIEW_BLOCKER_CONFIRMED=YES

## 5. Problem Statement
The active AI-RISA development branch is ai-risa-mainline.

The repository default branch is master.

The advisory workflow exists on ai-risa-mainline.

Manual workflow discovery is blocked because the workflow is not visible from the current default branch.

## 6. Proposed Default Branch Change
Design only.

Proposed future setting change:

master -> ai-risa-mainline

This document does not perform that change.

## 7. Required Operator Authorization
The exact authorization that must be given before any future settings change is:

GITHUB_DEFAULT_BRANCH_CHANGE_AUTHORIZED=YES

AUTHORIZED_NEW_DEFAULT_BRANCH=ai-risa-mainline

AUTHORIZED_OLD_DEFAULT_BRANCH=master

MERGE_AUTHORIZED=NO

BRANCH_DELETE_AUTHORIZED=NO

CUSTOMER_RELEASE_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 8. Safety Preconditions
Before changing default branch, a future slice must confirm:

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

## 9. Explicit Non-Goals
The future branch-change slice must not:

- merge master and ai-risa-mainline
- reconcile unrelated histories
- delete master
- rename branches
- change runtime code
- change tests
- change workflows
- create customer release authority
- create production launch authority
- create learning authority

## 10. Risk Review
Risks:

- default branch setting affects GitHub UI defaults
- future pull requests may target ai-risa-mainline
- branch protection expectations may need later review
- automation discovery may change
- collaborators may need to know the active default branch
- old master may still exist and should not be deleted in this slice chain

## 11. Expected Benefit
Changing the default branch to ai-risa-mainline should align GitHub repository defaults with the active AI-RISA development branch and allow the advisory workflow to be discoverable for manual dispatch.

## 12. Future Execution Method
Design only.

A future execution slice may use GitHub CLI only if explicitly authorized.

Future command pattern may be:

gh repo edit --default-branch ai-risa-mainline

Do not run that command in this slice.

## 13. Post-Change Verification Design
After a future authorized default branch change, the next slice should verify:

- gh repo view --json nameWithOwner,defaultBranchRef
- gh workflow view copilot-code-review.yml

Expected future result:

REPOSITORY_DEFAULT_BRANCH=ai-risa-mainline

WORKFLOW_VIEW_BLOCKER_CONFIRMED=NO

## 14. Review Decision
DESIGN_READY_FOR_OPERATOR_AUTHORIZATION_REVIEW_ONLY

## 15. Recommended Next Slice
Recommended next slice:

github_default_branch_change_authorization_review_v1

Only after that review, and only after explicit operator approval, may a later execution slice change the default branch.

## 16. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
DEFAULT_BRANCH_CHANGED=NO
MERGE_PERFORMED=NO
PR_CREATED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY