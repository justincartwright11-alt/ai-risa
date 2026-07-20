# GitHub Default Branch Change Authorization Review v1

## 1. Purpose
This document reviews the authorization design for changing the GitHub repository default branch from master to ai-risa-mainline.

## 2. Review Boundary
This is docs-only review.

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

## 4. Source Design Reviewed
Reference:

- docs/github_default_branch_change_authorization_design_v1.md

Confirm:

DESIGN_DECISION=DESIGN_READY_FOR_OPERATOR_AUTHORIZATION_REVIEW_ONLY

## 5. Source Precheck Reviewed
Reference:

- docs/github_actions_default_branch_alignment_precheck_v1.md

Confirm:

CURRENT_BRANCH=ai-risa-mainline

REPOSITORY_DEFAULT_BRANCH=master

DEFAULT_BRANCH_MISMATCH_CONFIRMED=YES

WORKFLOW_VIEW_BLOCKER_CONFIRMED=YES

## 6. Current Observed State
Current command evidence:

- current local branch: ai-risa-mainline
- repository default branch: master
- workflow file has local uncommitted changes: NO
- gh workflow view copilot-code-review.yml still returns 404: YES
- gh authentication is available: YES

## 7. Problem Statement Review
The problem is correctly stated:

The advisory workflow exists on ai-risa-mainline, but the repository default branch is master.

Manual workflow discovery remains blocked because the workflow is not visible from the current default branch.

This is a default-branch discovery issue, not proven YAML failure.

## 8. Proposed Change Review
The proposed future default branch change is:

master -> ai-risa-mainline

This review does not perform the change.

## 9. Operator Authorization Requirement Review
The design requires explicit future authorization fields:

GITHUB_DEFAULT_BRANCH_CHANGE_AUTHORIZED=YES

AUTHORIZED_NEW_DEFAULT_BRANCH=ai-risa-mainline

AUTHORIZED_OLD_DEFAULT_BRANCH=master

MERGE_AUTHORIZED=NO

BRANCH_DELETE_AUTHORIZED=NO

CUSTOMER_RELEASE_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 10. Safety Preconditions Review
The design requires future execution preconditions:

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

## 11. Non-Goal Review
Future execution must not:

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

## 12. Risk Review
The design identifies risks:

- default branch setting affects GitHub UI defaults
- future pull requests may target ai-risa-mainline
- branch protection expectations may need later review
- automation discovery may change
- collaborators may need default-branch awareness
- master should not be deleted in this chain

## 13. Post-Change Verification Review
Future execution verification must include:

- gh repo view --json nameWithOwner,defaultBranchRef
- gh workflow view copilot-code-review.yml

Expected future result:

REPOSITORY_DEFAULT_BRANCH=ai-risa-mainline

WORKFLOW_VIEW_BLOCKER_CONFIRMED=NO

## 14. Review Decision
APPROVED_FOR_OPERATOR_AUTHORIZATION_RECORD

## 15. Recommended Next Slice
Recommended next slice if clean:

github_default_branch_change_operator_authorization_record_v1

That later slice records explicit operator authorization only.

The actual repository setting change still requires a separate execution slice after the operator authorization record.

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