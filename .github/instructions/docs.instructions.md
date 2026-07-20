# AI-RISA Docs Copilot Instructions

## 1. Docs Instruction Identity
This file governs AI-RISA documentation changes, docs-only slices, design notes, review locks, readiness audits, evidence records, release gates, and documentation staged-set discipline.

## 2. Global Authority
This file is subordinate to .github/copilot-instructions.md.

The global AI-RISA development law still applies: one narrow slice, exact permitted files, one validation run, git diff/status review, commit, stop.

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Docs-Only Rule
Docs-only means documentation only.

A docs-only slice may not modify:

- runtime code
- tests
- PDF templates
- generated PDFs
- data files
- database schema
- customer delivery logic
- learning logic
- production settings

## 5. Design Document Boundary
Design documents define future intent only.

A design document does not authorize:

- implementation
- mutation
- database writes
- ledger writes
- learning activation
- customer release
- production launch
- automated delivery

## 6. Review Lock Boundary
Review locks preserve evidence and decision status only.

A review lock does not authorize:

- customer delivery
- production launch
- learning activation
- runtime changes
- permanent writes

## 7. Readiness Audit Boundary
Readiness audits report current readiness only.

Internal technical readiness is not customer release authority.

Customer release requires a separate explicit release gate.

## 8. Evidence and Proof Document Boundary
Evidence docs and proof docs prove only the specific slice they describe.

They do not expand authority beyond the approved slice.

Preview proof is not production permission.

## 9. Version and Supersession Rules
Do not silently supersede locked docs.

If a new document supersedes an older document, it must say so explicitly.

Historical records must not be rewritten unless explicitly authorized.

## 10. Release Language Discipline
Do not use language that implies customer launch, public release, production launch, automated delivery, or learning activation unless the current slice explicitly authorizes that status.

## 11. Button Documentation Boundaries
Button 1 docs must not authorize silent queue/database save.

Button 2 docs must not authorize customer delivery or public publishing.

Button 3 docs must not authorize learning, ledger writes, calibration writes, or GCID mutation.

## 12. Citation and Source Discipline
When docs refer to source evidence, preserve source names, timestamps, commit hashes, file paths, and uncertainty notes where available.

Do not invent verification.

Do not treat style examples as fact-verified evidence.

## 13. Staged-Set Discipline
Stage only the named docs instruction file or named documentation files in the current slice.

Do not stage unrelated workspace changes.

Verify with:

git diff --cached --name-status

## 14. Final Rule
When documentation authority is unclear, stop and request a narrower documentation slice.