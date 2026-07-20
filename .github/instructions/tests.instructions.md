# AI-RISA Tests Copilot Instructions

## 1. Tests Instruction Identity
This file governs AI-RISA test execution, validation discipline, failure classification, rerun limits, and test-related staged-set control.

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

## 4. Targeted Test Rule
Run only the tests named by the current slice.

Do not expand into:

- full pytest suite
- broad dashboard tests
- broad integration tests
- broad regression tests
- unrelated Button 1 / Button 2 / Button 3 tests

unless the current slice explicitly authorizes that expansion.

## 5. One Validation Run Rule
Run the requested validation once.

If it passes, stop testing.

If it fails, read the failure and classify the blocker.

Do not keep rerunning the same failing test without an actual repair.

## 6. Failure Classification Rule
Classify failures as one of:

- stale test harness
- changed function signature
- renamed route/helper
- implementation regression
- missing guard
- fixture/environment issue
- dependency issue
- unrelated pre-existing failure
- unknown

## 7. Blocker Rule
A failing targeted test becomes the exact blocker.

The final report must identify:

- failing test path
- failure classification
- first exact blocker
- last completed stage

Do not hide or soften a failed targeted test.

## 8. Repair Boundary
Repair only files explicitly permitted by the current slice.

If the slice is tests-only, do not modify runtime code.

If runtime repair is required but not authorized, stop and return BLOCKED.

Do not fix unrelated lint, formatting, whitespace, or tests unless explicitly authorized.

## 9. Rerun Rule After Repair
After a repair, rerun only:

- the originally failing targeted test
- any companion test explicitly named by the current slice

Do not expand into broad validation unless authorized.

## 10. Button-Specific Test Discipline
Button 1 tests must preserve source verification, queue approval, and no silent save.

Button 2 tests must preserve internal drafts, PDF render gates, visual QA, report versioning, and delivery blocking.

Button 3 tests must preserve official-result preview, non-mutation, accuracy review, fail-closed behaviour, and no automatic learning.

## 11. Governance Test Discipline
Governance validation must verify release boundaries, staged-set control, locked checkpoint protection, and no unauthorized authority escalation.

## 12. Test Output Reporting
Final reports must include:

- tests run
- results
- failure classification if applicable
- files changed
- whether code/test/docs/data/PDF changed
- customer release status
- release scope status
- commit SHA if committed
- remote sync status if pushed

## 13. Staged-Set Discipline
Stage only files changed by the current test slice.

Do not stage unrelated workspace changes.

Use:

git diff --cached --name-status

before committing.

## 14. Final Rule
When test authority is unclear, or a failure requires broader repair than the slice allows, stop and request a narrower repair slice.