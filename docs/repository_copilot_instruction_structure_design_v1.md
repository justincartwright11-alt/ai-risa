# Repository Copilot Instruction Structure Design v1

## 1. Purpose
This document defines the future repository instruction file structure for AI-RISA. It is a design for future repository instruction files, not an implementation of them.

## 2. Release Boundary
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY
- CUSTOMER_RELEASE_AUTHORIZED=NO
- PUBLIC_PUBLISHING_AUTHORIZED=NO
- PRODUCTION_LAUNCH_AUTHORIZED=NO
- AUTOMATED_DELIVERY_AUTHORIZED=NO
- LEARNING_ACTIVATION_AUTHORIZED=NO

## 3. Source Governance Dependency
This design depends on `docs/ai_risa_github_build_operations_upgrade_layer_v1.md`.

The build-operations layer establishes the higher-order governance rules for exact slices, AI credit control, operator sovereignty, model routing, browser evidence gates, security review gates, prompt integrity, and instruction integrity.

## 4. Instruction Hierarchy
The instruction hierarchy is defined as:

Global Law
→ Path-Specific Instructions
→ Agent Operating Doctrine
→ Review Doctrine
→ Slice Prompt
→ Current Locked Gate

Narrower authority overrides broader authority.

## 5. Future File Structure
Future structure only:

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

THIS SLICE DOES NOT CREATE THESE FILES.

## 6. Global Copilot Instruction Purpose
The future `.github/copilot-instructions.md` file must define the global development law for AI-RISA, including:

- one-slice discipline
- no broad refactors
- no authority escalation
- no customer release
- no hidden learning
- no locked-checkpoint modification
- one validation run
- diff/status review
- commit
- stop

## 7. Button 1 Instruction Purpose
The future Button 1 instruction file must define the scope for:

- source verification
- fight discovery
- fight queue
- source trust
- operator approval before queue/database save
- no silent permanent writes
- no untrusted-source authority escalation

## 8. Button 2 Instruction Purpose
The future Button 2 instruction file must define the scope for:

- premium report generation
- internal drafts
- PDF visual QA
- source map preservation
- report versioning
- customer delivery blocked unless separately approved
- no automated send

## 9. Button 3 Instruction Purpose
The future Button 3 instruction file must define the scope for:

- official result comparison
- accuracy review
- controlled learning gate
- no hidden mutation
- no calibration write without approval
- fail-closed preview behaviour
- no customer-output release without authority

## 10. Governance Instruction Purpose
The future governance instruction file must define:

- release boundaries
- authorization gates
- operator sovereignty
- staged-set control
- commit/tag rules
- locked checkpoint protection

## 11. Tests Instruction Purpose
The future tests instruction file must define:

- targeted tests only
- no broad test expansion unless authorized
- one validation run unless failure requires rerun
- failed test must become exact blocker
- no unrelated repair

## 12. Security Instruction Purpose
The future security instruction file must define:

- prompt integrity
- file upload safety
- path handling
- secrets
- API endpoints
- authorization
- customer data
- advisory security review

## 13. Docs Instruction Purpose
The future docs instruction file must define:

- docs-only means docs-only
- no runtime changes
- no implementation authority from design docs
- no customer release from review docs
- preserve version authority

## 14. AGENTS.md Purpose
The future AGENTS.md file must define:

- agent authority doctrine
- one writer per worktree
- parallel agents read-only by default
- browser agents observe only
- stop conditions
- escalation rules
- no agent self-approval
- no agent self-merge

## 15. REVIEW.md Purpose
The future REVIEW.md file must define:

- human/operator review doctrine
- Copilot review is advisory
- security review is advisory
- instruction changes require separate human review
- human approval remains final

## 16. Instruction Integrity Gate
Feature slices may not change runtime code and instruction or review governance files together.

Protected files:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

## 17. Future Implementation Order
1. Create this design doc.
2. Later create `.github/copilot-instructions.md`.
3. Later create path-specific instruction files.
4. Later create AGENTS.md.
5. Later create REVIEW.md.
6. Later review instruction integrity.
7. Later consider workflow automation only after stable local use.

## 18. Acceptance Criteria
The design is accepted when it defines:

- full future instruction hierarchy
- future file structure
- global Copilot instruction purpose
- Button 1 instruction purpose
- Button 2 instruction purpose
- Button 3 instruction purpose
- governance instruction purpose
- tests instruction purpose
- security instruction purpose
- docs instruction purpose
- AGENTS.md purpose
- REVIEW.md purpose
- instruction integrity gate
- future implementation order
- internal-only status

## 19. Slice Integrity
- DOCS_CHANGED=YES
- CODE_CHANGED=NO
- TEST_CHANGED=NO
- DATA_CHANGED=NO
- PDF_CHANGED=NO
- CUSTOMER_RELEASE_AUTHORIZED=NO
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY