# AI-RISA Premium Report Factory MVP Phase 1 Manual Event-Card Intake Design v1

Status: Planning boundary (docs-only)
Slice: ai-risa-premium-report-factory-mvp-implementation-phase1-design-v1
Date: 2026-05-01
Mode: Phase 1 design only

## 1. Phase 1 Purpose

Define a manual/paste event-card intake model as the smallest first implementation
phase for MVP execution planning.

Phase 1 objectives:
- Support operator-entered upcoming fight cards.
- Extract Fighter A vs Fighter B matchup rows.
- Produce preview records only.
- Enforce no automatic web write.
- Enforce no database write in Phase 1 (writes deferred to Phase 4 approval flow).

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/ai_risa_premium_report_factory_workflow_design_v1.md
- docs/ai_risa_premium_report_factory_workflow_design_review_v1.md
- docs/ai_risa_premium_report_factory_mvp_scope_design_v1.md
- docs/ai_risa_premium_report_factory_mvp_scope_design_review_v1.md
- docs/ai_risa_premium_report_factory_mvp_implementation_design_v1.md
- docs/ai_risa_premium_report_factory_mvp_implementation_design_review_v1.md

## 3. Phase 1 Boundary

In-scope behavior:
- manual paste/write input only
- parse upcoming event card text
- normalize event/card fields
- normalize matchup rows
- preview only

Out-of-scope behavior for Phase 1:
- no save/apply
- no PDF generation
- no result lookup
- no learning/calibration update

## 4. Proposed Input Fields

- raw_card_text
- event_name
- event_date
- promotion
- location
- source_reference
- notes

## 5. Proposed Parsed Matchup Fields

- temporary_matchup_id
- fighter_a
- fighter_b
- bout_order
- weight_class
- ruleset
- source_reference
- parse_status
- parse_notes

## 6. Proposed Preview Response

- ok
- generated_at
- event_preview
- matchup_previews
- parse_warnings
- errors

## 7. Parse Rules

- Preserve original text.
- Never invent missing fighters.
- Mark incomplete rows as needs_review.
- Generate deterministic temporary IDs.
- Keep source_reference attached at event and matchup levels.

## 8. Operator Workflow

- Paste/write event card text.
- Preview extracted matchup rows.
- Manually correct source text if needed.
- Confirm only after preview is acceptable.
- Saving is not part of Phase 1.

## 9. Future Implementation Test Plan

Required tests for a future Phase 1 implementation slice:
- clean pasted card parses into event preview and matchup previews
- incomplete matchup is marked needs_review
- duplicate lines handled deterministically
- missing event date returns warning, not failure
- no write occurs
- backend regression remains green

## 10. Risks and Guardrails

Primary risks:
- parsing ambiguity in loosely formatted pasted cards
- accidental drift from preview-only into write behavior
- data quality risk from incomplete fighter/event text

Guardrails:
- enforce preview-only response in Phase 1
- require explicit needs_review labeling for incomplete rows
- require deterministic parsing and ID generation
- block write path exposure in Phase 1
- keep source_reference mandatory in preview contract

## 11. Explicit Non-Goals

- no web scraping
- no automatic official-source lookup
- no database save
- no report generation
- no result comparison
- no self-learning
- no batch automation

## 12. Phase 1 Implementation Readiness Verdict

Phase 1 manual event-card intake is approved only as a docs-only implementation
design boundary.

Actual implementation remains blocked until a separate Phase 1 implementation
slice is explicitly opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token semantics,
mutation behavior, scoring logic, approved-result pipeline behavior, global ledger
behavior, batch behavior, prediction behavior, intake behavior, or report-generation
behavior were changed in this slice.
