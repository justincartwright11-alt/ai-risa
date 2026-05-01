# AI-RISA Premium Report Factory MVP Phase 1 Manual Event-Card Intake Release Manifest v1

Status: Released (docs-only manifest)
Slice: ai-risa-premium-report-factory-mvp-phase1-intake-release-manifest-v1
Date: 2026-05-01
Mode: Release manifest only

## 1. Release Name

AI-RISA Premium Report Factory MVP Phase 1 Manual Event-Card Intake Preview
Release Manifest v1

## 2. Release Purpose

Record and lock the released scope, commit/tag governance chain, validation
evidence, boundaries, and stop-point constraints for the Phase 1 preview-only
manual intake foundation.

## 3. Commit/Tag Chain

1. Phase 1 intake design:
- commit: 2394827
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-design-v1

2. Phase 1 intake design review:
- commit: 9b16bf9
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-design-review-v1

3. Phase 1 intake implementation design:
- commit: bcde147
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-implementation-design-v1

4. Phase 1 intake implementation design review:
- commit: 8918a8b
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-implementation-design-review-v1

5. Phase 1 intake implementation:
- commit: e7cbba9
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-implementation-v1

6. Phase 1 intake final review:
- commit: 87e6538
- tag: ai-risa-premium-report-factory-mvp-phase1-intake-final-review-v1

## 4. Files Changed In The Implementation

- operator_dashboard/app.py
- operator_dashboard/test_app_backend.py

## 5. Locked Behavior

Preview-only endpoint:
- POST /api/premium-report-factory/intake/preview

Endpoint accepts:
- raw_card_text
- event_name
- event_date
- promotion
- location
- source_reference
- notes

Endpoint returns:
- ok
- generated_at
- event_preview
- matchup_previews
- parse_warnings
- errors

event_preview includes:
- event_name
- event_date
- promotion
- location
- source_reference
- notes
- raw_card_text_preserved

matchup_previews include:
- temporary_matchup_id
- fighter_a
- fighter_b
- bout_order
- weight_class
- ruleset
- source_reference
- parse_status
- parse_notes

Locked parsing/preview semantics:
- raw_card_text is preserved exactly
- missing event_date warns, not fails
- incomplete rows are marked needs_review
- duplicate lines are deterministic
- temporary_matchup_id values are deterministic
- endpoint is preview-only
- no save/apply/write behavior added
- no persistent storage write added
- no global ledger write added
- no approved-result pipeline write added
- no token consume behavior added
- no report generation added
- no result comparison added
- no learning/calibration update added

## 6. Validation Evidence

- compile PASS
- focused Phase 1 intake tests PASS, 6 tests
- direct endpoint probe PASS
- backend regression PASS, 215 tests
- final git clean PASS
- runtime artifacts excluded

## 7. Release Boundaries

- preview-only intake
- no save/apply
- no database write
- no automatic web lookup
- no PDF generation
- no result lookup
- no calibration/learning update
- no global database write

## 8. Rollback Anchors

- implementation commit: e7cbba9
- final review commit: 87e6538

## 9. Operator Acceptance Statement

Operator acceptance confirms the released endpoint is suitable for manual
preview-only event-card intake and parsing visibility, with no save/apply
mutation path enabled in this phase. Operator workflow remains paste, review,
and manual source-text correction only.

## 10. Final Release Verdict

The AI-RISA Premium Report Factory MVP Phase 1 manual event-card intake preview
implementation is released as a preview-only manual intake foundation. The stop
point is valid. Any future save/apply, report-generation, result-lookup,
calibration, database-write, dashboard expansion, or web-discovery behavior
must begin with a separate docs-only design slice.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake behavior, or report generation behavior were changed
in this slice.
