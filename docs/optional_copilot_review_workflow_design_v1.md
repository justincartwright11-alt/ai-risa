# Optional Copilot Review Workflow Design v1

## 1. Purpose
This document designs a possible future Copilot review workflow for AI-RISA.

This is design-only and does not create workflow automation.

## 2. Design Boundary
This document does not authorize:

- workflow file creation
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

## 4. Source Governance Dependencies
This design depends on:

- .github/copilot-instructions.md
- .github/instructions/governance.instructions.md
- .github/instructions/security.instructions.md
- .github/instructions/tests.instructions.md
- AGENTS.md
- REVIEW.md
- docs/local_instruction_smoke_check_v1.md

## 5. Review Workflow Objective
The future workflow objective would be to:

- provide advisory review comments
- detect scope drift
- detect protected-file changes
- detect missing release-boundary language
- detect unsafe authority escalation
- detect broad file changes
- detect possible secrets or unsafe delivery changes
- support human/operator review

The workflow must not approve, merge, release, deploy, deliver, or activate learning.

## 6. Proposed Trigger Design
Design only. Do not implement.

Proposed future triggers may include:

- pull request opened
- pull request synchronized
- pull request reopened
- manual workflow dispatch

Direct push review may be considered later, but must be reviewed separately because it can increase noise and cost.

## 7. Proposed Permission Boundary
Design only. Do not implement.

Future workflow permissions should be least-privilege.

The workflow should not receive write authority beyond what is required for advisory review comments.

The workflow must not receive secrets unless a separate security design explicitly authorizes them.

## 8. Protected File Detection
Future workflow should flag changes to:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

Protected-file changes require separate instruction-integrity review.

## 9. Authority Escalation Detection
Future workflow should flag language or changes that imply:

- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes
- agent self-approval
- agent self-merge
- preview proof becoming production permission
- design docs becoming implementation authority

## 10. Button-Specific Review Checks
Future advisory review should check:

Button 1:

- no silent queue/database save
- source traceability preserved
- operator approval required

Button 2:

- no automatic customer delivery
- report source map preserved
- PDF visual QA gate preserved

Button 3:

- fail-closed behaviour preserved
- preview paths remain non-mutating
- no hidden learning
- no unauthorized ledger, calibration, or GCID writes

## 11. Security Review Checks
Future advisory review should check:

- prompt integrity
- untrusted input containment
- file/path safety
- upload safety
- API endpoint safety
- auth/authorization boundaries
- customer data exposure
- report delivery boundary
- secrets or credentials

## 12. Cost and Noise Control
Future workflow must avoid excessive usage.

Design controls:

- run only on pull requests or manual dispatch unless separately approved
- avoid broad repository analysis
- focus on changed files
- skip generated artifacts where appropriate
- treat review as advisory, not a blocker unless a human/operator decides

## 13. Required Human Review
A human/operator must review the workflow design before any workflow file is created.

A human/operator must approve:

- workflow creation
- workflow permissions
- protected-file handling
- review scope
- cost controls
- security boundaries

## 14. Future Implementation Gate
Before creating any workflow file, require a separate slice:

optional_copilot_review_workflow_design_review_v1

Then, only if approved, a later workflow-creation slice may create:

.github/workflows/copilot-code-review.yml

This current slice does not create that file.

## 15. Review Decision
DESIGN_READY_FOR_INTERNAL_REVIEW_ONLY

Do not use:

- APPROVED_FOR_WORKFLOW_CREATION
- APPROVED_FOR_PRODUCTION
- CUSTOMER_RELEASE_APPROVED

## 16. Slice Integrity
DOCS_CHANGED=YES
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
WORKFLOW_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY