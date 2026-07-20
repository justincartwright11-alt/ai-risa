# AI-RISA Review Doctrine

## 1. Purpose
REVIEW.md governs AI-RISA review discipline, human/operator authority, advisory review limits, evidence requirements, release review boundaries, and instruction-change review.

## 2. Relationship to Global Instructions
REVIEW.md is subordinate to:

.github/copilot-instructions.md

and must align with:

AGENTS.md
.github/instructions/governance.instructions.md
.github/instructions/security.instructions.md
.github/instructions/tests.instructions.md
.github/instructions/docs.instructions.md

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Human Operator Authority
The human/operator is the final review authority.

Copilot, AI reviewers, browser agents, test agents, and security agents may provide advisory evidence only.

No agent may approve:

- its own work
- customer release
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes
- privileged workflow changes

## 5. Review Types
Review types:

- Slice Review
- Governance Review
- Security Review
- Test Review
- PDF Visual QA Review
- Button 1 Source Review
- Button 2 Report Review
- Button 3 Accuracy and Learning Review
- Instruction Integrity Review
- Release Review

## 6. Advisory Review Rule
Copilot review is advisory.

Security review is advisory.

Browser evidence is advisory.

Test pass is evidence, not authority.

Preview proof is evidence, not release permission.

A review may identify blockers, risks, or recommendations, but cannot grant authority by itself.

## 7. Evidence Requirements
A valid review must preserve where applicable:

- slice ID
- baseline commit
- files changed
- tests or validations run
- pass/fail result
- exact blocker if failed
- customer release status
- release scope
- mutation authority status
- learning authority status
- commit SHA if committed
- remote sync status if pushed

## 8. Instruction Change Review
Instruction and review-governance files are protected governance files.

Protected files include:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

Instruction changes require separate review.

Feature slices must not change runtime code and instruction/review governance files together.

## 9. Button 1 Review Boundary
Button 1 review must verify:

- source traceability
- fighter identity evidence
- event identity evidence
- uncertainty notes
- no silent queue/database save
- operator approval before permanent save

## 10. Button 2 Review Boundary
Button 2 review must verify:

- internal draft status
- report version status
- source-map preservation
- confidence and uncertainty notes
- PDF visual QA when applicable
- no automatic customer delivery
- no customer release without explicit approval

## 11. Button 3 Review Boundary
Button 3 review must verify:

- official result source traceability
- fighter identity match
- event identity match
- prediction/result linkage
- accuracy classification
- structural/right-reason review
- fail-closed non-mutation
- no automatic learning
- no ledger/calibration/GCID writes without explicit authority

## 12. Security Review Boundary
Security review must check where applicable:

- prompt integrity
- untrusted input containment
- secrets
- file/path safety
- upload safety
- API endpoint safety
- authentication
- authorization
- customer data exposure
- report delivery boundary

Security review findings do not authorize release by themselves.

## 13. Release Review Boundary
Customer release requires explicit customer release authority.

Production launch requires explicit production launch authority.

Automated delivery requires explicit automated delivery authority.

Learning activation requires explicit learning activation authority.

Internal readiness does not equal customer release.

## 14. Review Decision Labels
Use these labels:

- APPROVED_FOR_INTERNAL_REVIEW_ONLY
- APPROVED_FOR_NEXT_INTERNAL_SLICE
- HOLD_FOR_BLOCKER
- BLOCKED
- REJECTED
- SUPERSEDED
- CUSTOMER_RELEASE_NOT_AUTHORIZED
- PRODUCTION_LAUNCH_NOT_AUTHORIZED
- LEARNING_ACTIVATION_NOT_AUTHORIZED

## 15. No Self-Approval
The agent or tool that produced a change may not be the final approver of that change.

Human/operator approval remains final.

## 16. Staged-Set Discipline
Review must confirm staged files match the approved slice.

Use:

git diff --cached --name-status

Do not stage unrelated workspace changes.

## 17. Final Rule
When review authority is unclear, stop and request a narrower review slice.