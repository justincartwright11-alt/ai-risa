# GitHub Actions Instruction System Final Internal Lock v1

## 1. Purpose
This document is the final internal lock for the AI-RISA repository instruction system and optional Copilot advisory workflow.

## 2. Lock Boundary
This is a docs-only internal lock.

It does not authorize:

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

## 4. Instruction System Lock
The instruction system exists and is internally locked:

- .github/copilot-instructions.md
- .github/instructions/button1.instructions.md
- .github/instructions/button2.instructions.md
- .github/instructions/button3.instructions.md
- .github/instructions/governance.instructions.md
- .github/instructions/tests.instructions.md
- .github/instructions/security.instructions.md
- .github/instructions/docs.instructions.md
- AGENTS.md
- REVIEW.md

## 5. Instruction Integrity Evidence
Reference:

- docs/repository_instruction_integrity_review_v1.md

Confirm:

AUTHORITY_CONFLICT_FOUND=NO

REVIEW_DECISION=APPROVED_FOR_NEXT_INTERNAL_SLICE

## 6. Instruction Index Evidence
Reference:

- docs/repository_instruction_system_readme_index_v1.md

The instruction system is indexed for internal use.

## 7. Local Smoke Check Evidence
Reference:

- docs/local_instruction_smoke_check_v1.md

Confirm:

LOCAL_USE_STATUS=READY_FOR_INTERNAL_COPILOT_USE

AUTHORITY_ESCALATION_FOUND=NO

## 8. Advisory Workflow Design Chain
Reference:

- docs/optional_copilot_review_workflow_design_v1.md
- docs/optional_copilot_review_workflow_design_review_v1.md
- docs/optional_copilot_review_workflow_creation_review_v1.md

Confirm:

- workflow is advisory-only
- review is advisory-only
- no customer release authority
- no production launch authority
- no learning activation authority

## 9. Advisory Workflow File Lock
Reference:

- .github/workflows/copilot-code-review.yml

Confirm:

- workflow exists
- workflow is discoverable
- workflow uses workflow_dispatch
- workflow does not use pull_request_target
- workflow is advisory-only
- workflow requires no secrets
- workflow grants no merge, deployment, delivery, release, or learning authority

## 10. Default Branch Alignment Lock
Reference:

- docs/github_default_branch_change_execution_v1.md
- docs/github_default_branch_change_execution_review_v1.md

Confirm:

REPOSITORY_DEFAULT_BRANCH=ai-risa-mainline

WORKFLOW_VIEW_BLOCKER_CONFIRMED=NO

MERGE_PERFORMED=NO

PR_CREATED=NO

WORKFLOW_CHANGED=NO

## 11. Manual Dispatch Observation Lock
Reference:

- docs/optional_copilot_review_workflow_manual_dispatch_observation_v1.md
- docs/optional_copilot_review_workflow_observation_review_v1.md

Confirm:

WORKFLOW_RUN_ID=29728631649

WORKFLOW_RUN_CONCLUSION=success

WORKFLOW_ADVISORY_ONLY_CONFIRMED=YES

REVIEW_DECISION=APPROVED_FOR_INTERNAL_ADVISORY_WORKFLOW_OBSERVATION_LOCK

## 12. Current Verification State
Current command evidence:

- current local branch: ai-risa-mainline
- repository default branch: ai-risa-mainline
- workflow discovery status: discoverable
- workflow run conclusion for 29728631649: success
- workflow file local uncommitted change status: NO LOCAL CHANGES

Expected:

CURRENT_BRANCH=ai-risa-mainline

REPOSITORY_DEFAULT_BRANCH=ai-risa-mainline

WORKFLOW_VIEW_BLOCKER_CONFIRMED=NO

WORKFLOW_RUN_CONCLUSION=success

WORKFLOW_CHANGED=NO

## 13. Authority Confirmation
Confirm:

- customer release remains unauthorized
- public publishing remains unauthorized
- production launch remains unauthorized
- automated delivery remains unauthorized
- learning activation remains unauthorized
- calibration writes remain unauthorized
- GCID writes remain unauthorized
- accuracy-ledger writes remain unauthorized
- human/operator approval remains final

## 14. Final Internal Lock Decision
INTERNAL_ADVISORY_WORKFLOW_AND_INSTRUCTION_SYSTEM_LOCKED

## 15. Recommended Next Slice
Recommended next slice:

resume_ai_risa_internal_build_priority_selection_v1

AI-RISA may now resume internal build prioritization under the new instruction and advisory workflow system.

## 16. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY