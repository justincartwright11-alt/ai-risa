# GitHub Actions Default Branch Alignment Precheck v1

## 1. Purpose
This document records a read-only precheck for the GitHub Actions default-branch workflow discovery blocker.

## 2. Precheck Boundary
This is docs-only and read-only.

It does not authorize:

- repository default branch change
- branch merge
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

## 4. Observed Blocker
gh workflow view copilot-code-review.yml returned HTTP 404 workflow not found on the default branch

## 5. Current Branch and Default Branch
- current local branch: ai-risa-mainline
- repository default branch from gh repo view: master
- default branch different from ai-risa-mainline: YES

## 6. Workflow File Location
- workflow path: .github/workflows/copilot-code-review.yml
- exists locally: YES
- committed on ai-risa-mainline: YES
- local path has uncommitted changes: NO

## 7. Cause Assessment
The manual dispatch observation is blocked because GitHub Actions manual workflow discovery requires the workflow file to be visible from the repository default branch.

Do not treat this as a YAML failure unless evidence shows the workflow file is malformed.

## 8. Remediation Options
Option A -- Change repository default branch to ai-risa-mainline.

- Advantage: aligns GitHub Actions discovery with the active AI-RISA branch.
- Risk: repository settings change; requires explicit operator approval.

Option B -- Keep default branch unchanged and separately expose workflow on default branch.

- Advantage: avoids default-branch settings change.
- Risk: dangerous if histories are unrelated; must not merge blindly.

Option C -- Do nothing and leave manual dispatch observation blocked.

- Advantage: no settings or branch risk.
- Risk: workflow cannot be manually observed from current state.

## 9. Recommended Next Slice
Recommended next slice:

github_default_branch_change_authorization_design_v1

Only if the operator wants to make ai-risa-mainline the repository default branch.

Do not change the default branch without separate explicit operator authorization.

## 10. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY