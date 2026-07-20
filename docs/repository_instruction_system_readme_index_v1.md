# AI-RISA Repository Instruction System Index v1

## 1. Purpose
This document indexes the AI-RISA repository instruction system for future internal development work.

## 2. Index Boundary
This is a docs-only index.

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

## 4. Instruction System Inventory
The repository instruction system inventory is:

- .github/copilot-instructions.md — global Copilot governance and slice law
- .github/instructions/button1.instructions.md — fight discovery, queue review, operator-approved save
- .github/instructions/button2.instructions.md — premium report generation, PDF rendering, visual QA
- .github/instructions/button3.instructions.md — result comparison, accuracy review, controlled learning
- .github/instructions/governance.instructions.md — release boundaries, authority gates, checkpoint protection
- .github/instructions/tests.instructions.md — targeted validation, failure classification, rerun limits
- .github/instructions/security.instructions.md — prompt integrity, containment, secrets, file/path safety
- .github/instructions/docs.instructions.md — docs-only discipline, review locks, readiness audits
- AGENTS.md — agent authority, one-writer rule, browser-agent limits
- REVIEW.md — human/operator review authority, advisory review limits, evidence requirements

## 5. Practical Use Map
- General repo work → .github/copilot-instructions.md
- Fight discovery / queue work → .github/instructions/button1.instructions.md
- Premium report / PDF work → .github/instructions/button2.instructions.md
- Results / accuracy / learning review work → .github/instructions/button3.instructions.md
- Release gates / authority questions → .github/instructions/governance.instructions.md
- Validation / targeted tests → .github/instructions/tests.instructions.md
- Prompt integrity / source safety / secrets / delivery safety → .github/instructions/security.instructions.md
- Docs-only slices / review locks / readiness audits → .github/instructions/docs.instructions.md
- Agent roles / one-writer rule / browser-agent limits → AGENTS.md
- Human/operator review discipline → REVIEW.md

## 6. Hierarchy Summary
Operating hierarchy:

Global Copilot Instructions
→ Path-Specific Instructions
→ AGENTS.md
→ REVIEW.md
→ Current Slice Prompt
→ Operator Approval

The narrower rule controls when it is more restrictive.

No file may expand release, learning, mutation, or customer authority beyond the current approved slice.

## 7. Protected Files
Protected governance files are:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

This index does not create GEMINI.md, CLAUDE.md, or workflow files.

## 8. Current Review Status
Reference: docs/repository_instruction_integrity_review_v1.md

REVIEW_DECISION=APPROVED_FOR_NEXT_INTERNAL_SLICE

AUTHORITY_CONFLICT_FOUND=NO

CUSTOMER_RELEASE_AUTHORIZED=NO

RELEASE_SCOPE_DECISION=INTERNAL_ONLY

## 9. Future Internal Slice Order
Recommended next internal slices:

1. repository_instruction_system_readme_index_v1
2. local_instruction_smoke_check_v1
3. optional_copilot_review_workflow_design_v1
4. optional_security_review_workflow_design_v1
5. optional_workflow_creation_only_after_design_review_v1

No workflow automation should be created before a separate design-and-review slice.

## 10. Slice Integrity
DOCS_CHANGED=YES
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY