# Repository Instruction Integrity Review v1

## 1. Purpose
This document reviews the completed repository instruction system.

## 2. Review Boundary
This is a docs-only review.

It does not authorize:

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
- workflow automation

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Instruction Inventory
The repository instruction inventory is present and complete:

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

## 5. Hierarchy Review
The hierarchy is coherent:

Global Copilot Instructions
→ Path-Specific Instructions
→ AGENTS.md
→ REVIEW.md
→ Current Slice Prompt
→ Operator Approval

No conflicts were found in the hierarchy review.

## 6. Release Boundary Consistency Review
The reviewed files preserve:

INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 7. Button 1 Instruction Review
Button 1 instructions cover:

- fight discovery
- source verification
- identity resolution
- queue review
- operator-approved save
- no silent permanent save

## 8. Button 2 Instruction Review
Button 2 instructions cover:

- internal premium report generation
- report refresh/versioning
- source-map preservation
- PDF rendering
- visual QA
- no automatic customer delivery

## 9. Button 3 Instruction Review
Button 3 instructions cover:

- official-result verification
- prediction/result comparison
- accuracy review
- controlled learning review
- fail-closed non-mutation
- no hidden learning
- no unauthorized ledger/calibration/GCID writes

## 10. Governance Instruction Review
Governance instructions cover:

- operator sovereignty
- authorization gates
- staged-set control
- locked checkpoint protection
- instruction integrity gate
- no self-approval
- no release authority from design/review/readiness/proof docs

## 11. Tests Instruction Review
Tests instructions cover:

- targeted tests only
- one validation run rule
- blocker classification
- no broad test expansion
- no unrelated repair

## 12. Security Instruction Review
Security instructions cover:

- prompt integrity
- untrusted input containment
- secrets
- file/path safety
- upload safety
- endpoint safety
- customer data
- report delivery boundary

## 13. Docs Instruction Review
Docs instructions cover:

- docs-only means docs-only
- design docs do not authorize implementation
- review locks do not authorize release
- readiness audits do not authorize customer release
- evidence/proof docs do not create production authority

## 14. AGENTS.md Review
AGENTS.md covers:

- one write-authorized agent per worktree
- parallel agents read-only by default
- browser-agent limits
- review-agent limits
- stop conditions
- escalation rules
- no agent self-approval
- no self-merge

## 15. REVIEW.md Review
REVIEW.md covers:

- human/operator final authority
- advisory review rule
- review types
- evidence requirements
- instruction-change review
- release review boundaries
- no self-approval

## 16. Protected File Coverage
Protected files are defined as:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

This review does not create GEMINI.md, CLAUDE.md, or workflow files.

## 17. Authority Conflict Review
No file appears to authorize:

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

NO AUTHORITY CONFLICT FOUND

## 18. Review Decision
APPROVED_FOR_NEXT_INTERNAL_SLICE

## 19. Slice Integrity
DOCS_CHANGED=YES
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY