# AI-RISA Premium Report Factory MVP Phase 1 Manual Event-Card Intake Implementation Design v1

Status: Planning artifact (docs-only)
Slice: ai-risa-premium-report-factory-mvp-phase1-intake-implementation-design-v1
Date: 2026-05-01
Mode: Phase 1 implementation design only

## 1. Implementation Scope

This document defines a docs-only implementation design plan for Phase 1 manual
or paste-based event-card intake preview behavior.

In-scope planning intent:
- Phase 1 preview-only manual/paste event-card intake
- no save/apply/write behavior
- no PDF/report generation
- no result lookup
- no learning/calibration update

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/ai_risa_premium_report_factory_mvp_phase1_manual_event_card_intake_design_v1.md
- docs/ai_risa_premium_report_factory_mvp_phase1_manual_event_card_intake_design_review_v1.md

## 3. Proposed Backend Touchpoints

Planned touchpoints for a future implementation slice:
- parser/helper module or helper function
- preview endpoint only
- focused backend tests
- no persistent storage touchpoint

Design intent notes:
- Parsing should be isolated in helper logic to keep endpoint logic minimal.
- Endpoint shape should remain preview-only and non-mutating.
- Test additions should focus on deterministic parse and boundary behavior only.

## 4. Proposed Preview Endpoint

- POST /api/premium-report-factory/intake/preview

Endpoint role in future implementation:
- accept manual/pasted event-card text and optional event metadata
- return normalized preview envelope with warnings/errors
- perform no save/apply/write actions

## 5. Proposed Request Contract

- raw_card_text
- event_name
- event_date
- promotion
- location
- source_reference
- notes

## 6. Proposed Response Contract

- ok
- generated_at
- event_preview
- matchup_previews
- parse_warnings
- errors

## 7. Proposed event_preview Fields

- event_name
- event_date
- promotion
- location
- source_reference
- notes
- raw_card_text_preserved

## 8. Proposed matchup_preview Fields

- temporary_matchup_id
- fighter_a
- fighter_b
- bout_order
- weight_class
- ruleset
- source_reference
- parse_status
- parse_notes

## 9. Parsing Behavior

Planned parse behavior requirements:
- preserve original text
- never invent missing fighters
- deterministic temporary_matchup_id
- duplicate lines handled deterministically
- incomplete rows marked needs_review
- missing metadata yields warnings, not writes
- all output deterministic

Parse compliance guidance:
- preview output must be reproducible for identical input
- missing or partial metadata must remain non-fatal where possible
- parse warnings should communicate data quality gaps without mutation side effects

## 10. Operator Workflow

Planned Phase 1 operator flow:
- paste/write card
- preview parsed event and matchups
- inspect warnings/errors
- manually correct source text if needed
- no save button in Phase 1

## 11. Test Plan

Required tests for a future implementation slice:
- clean card parses into event_preview and matchup_previews
- incomplete matchup marked needs_review
- duplicate line handling deterministic
- missing event_date returns warning
- source_reference preserved
- no save/write/storage occurs
- backend regression remains green

## 12. Boundaries and Guardrails

Phase 1 hard guardrails:
- no web scraping
- no database write
- no approved-result pipeline write
- no global ledger write
- no token consume
- no report generation
- no result comparison
- no self-learning

Additional safety boundary:
- no token digest semantics change
- no mutation behavior change
- no scoring behavior change
- no dashboard behavior change

## 13. Explicit Non-Goals

- no production implementation in this slice
- no endpoint activation in this slice
- no persistence layer work in this slice
- no workflow automation beyond manual preview modeling
- no batch orchestration
- no prediction workflow expansion
- no intake write path enablement
- no report factory output generation

## 14. Implementation Readiness Verdict

The AI-RISA Premium Report Factory MVP Phase 1 manual event-card intake
implementation design is approved only as a planning artifact. Actual
implementation remains blocked until a separate Phase 1 implementation slice is
explicitly opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake behavior, or report generation behavior were changed
in this slice.
