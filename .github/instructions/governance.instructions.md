# AI-RISA Governance Copilot Instructions

## 1. Governance Identity
This file governs AI-RISA repository governance, release boundaries, approval gates, staged-set discipline, checkpoint protection, and operator sovereignty.

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

## 4. Operator Sovereignty
The operator is the final authority.

Copilot may assist, propose, draft, inspect, test, and summarize.

Copilot may not:

- approve its own work
- merge its own work
- elevate authority
- authorize customer release
- authorize production launch
- authorize learning activation
- bypass approval gates

## 5. Authorization Gate Rules
Separate gates are required for:

- implementation authority
- mutation authority
- customer release authority
- production launch authority
- automated delivery authority
- learning activation authority
- calibration write authority
- GCID write authority
- accuracy-ledger write authority

One gate does not imply another.

## 6. Design and Review Document Boundary
Design docs define future intent only.

Review docs lock evidence only.

Readiness docs report readiness only.

Proof docs prove a slice only.

None of these automatically authorize:

- runtime changes
- customer release
- production launch
- automated delivery
- learning activation
- persistent database writes
- ledger writes

## 7. Button 3 Governance Boundary
Button 3 is fail-closed.

Preview proof is not mutation authority.

Result comparison is not learning authority.

Accuracy review is not calibration authority.

Controlled learning requires verified evidence, operator approval, audit record, and rollback path where applicable.

## 8. Staged-Set Control
Before staging, inspect git status.

Stage only files explicitly permitted by the current slice.

Verify staged files with:

git diff --cached --name-status

Do not stage unrelated workspace changes.

Do not clean, reset, stash, discard, or overwrite unrelated work unless explicitly authorized.

## 9. Locked Checkpoint Protection
Locked commits, tags, proofs, review locks, release gates, evidence packs, and internal-only decisions must not be rewritten, weakened, or reinterpreted.

A later slice may supersede a checkpoint only through explicit documented authority.

## 10. Commit and Tag Discipline
Commit only the approved slice.

Do not tag unless the current slice explicitly requires a tag.

Do not force push.

Do not amend prior commits unless explicitly authorized.

Stop after the final report.

## 11. Instruction Integrity Gate
Instruction and review-governance files are protected governance files.

Protected files include:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

Feature slices must not change runtime code and instruction/review governance files together.

Instruction changes require separate human/operator review.

## 12. Customer and Public Release Prohibition
No customer release may occur while:

CUSTOMER_RELEASE_AUTHORIZED=NO

No public publishing may occur while:

PUBLIC_PUBLISHING_AUTHORIZED=NO

No production launch may occur while:

PRODUCTION_LAUNCH_AUTHORIZED=NO

Internal technical readiness is not customer release authority.

## 13. Learning and Mutation Prohibition
No learning activation may occur while:

LEARNING_ACTIVATION_AUTHORIZED=NO

No automated delivery may occur while:

AUTOMATED_DELIVERY_AUTHORIZED=NO

No persistent mutation may occur unless the current slice explicitly grants mutation authority and identifies the exact files, endpoints, ledgers, or database targets.

## 14. Governance Test Discipline
Run only validation requested by the current slice.

Do not expand into broad tests unless authorized.

If a governance validation fails, stop and report the exact blocker.

## 15. Final Rule
When authority is unclear, contradictory, stale, missing, or too broad, stop and request a narrower slice.