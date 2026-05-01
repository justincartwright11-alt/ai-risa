# AI-RISA Premium Report Factory MVP Phase 1 Intake Dashboard Panel Design v1

Status: Planning boundary (docs-only)
Slice: ai-risa-premium-report-factory-mvp-phase1-intake-dashboard-panel-design-v1
Date: 2026-05-01
Mode: Dashboard panel design only

## 1. Purpose

Define the first visible Premium Report Factory panel for dashboard usage while
keeping behavior preview-only and non-mutating.

Design goals:
- make Phase 1 Premium Report Factory visible in the dashboard
- allow the operator to paste/write event-card text
- allow preview of extracted Fighter A vs Fighter B matchups
- keep workflow preview-only

## 2. Current Backend Capability

Current backend endpoint:
- POST /api/premium-report-factory/intake/preview

Current boundary:
- preview-only
- no save/apply/write behavior
- no PDF generation
- no result lookup
- no learning update

## 3. Proposed Dashboard Panel Title

- Premium Report Factory - Event Card Intake Preview

## 4. Proposed Button

- Preview Event Card

## 5. Proposed Input Fields

- raw_card_text
- event_name
- event_date
- promotion
- location
- source_reference
- notes

## 6. Proposed Output Window

- event_preview
- matchup_previews
- parse_warnings
- errors

## 7. Matchup Table Fields

- temporary_matchup_id
- fighter_a
- fighter_b
- bout_order
- weight_class
- ruleset
- source_reference
- parse_status
- parse_notes

## 8. Safety Boundary

- no save button in this phase
- no global database write
- no PDF generation
- no result search
- no self-learning
- no batch action
- preview only

## 9. Operator Workflow

- paste event-card text
- fill optional event metadata
- press Preview Event Card
- inspect extracted matchups
- manually correct source text if needed
- future phase will add save/rank/report actions

## 10. Future Path

- Phase 1 panel implementation
- Phase 2 approved save and queue
- Phase 3 PDF report builder
- Phase 4 result comparison center
- Phase 5 approved calibration learning

## 11. Test Plan For Future Implementation

- panel exists
- button calls preview endpoint
- input fields are present
- matchup preview renders
- warnings/errors render
- no save/write controls exist
- backend regression remains green

## 12. Explicit Non-Goals

- no web scraping
- no automatic event discovery
- no database save
- no global ledger write
- no PDF generation
- no result comparison
- no self-learning
- no customer billing

## 13. Final Design Verdict

Approved only as a docs-only dashboard design boundary. Implementation remains
blocked until a separate implementation-design and implementation slice are
opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake behavior, or report-generation behavior were changed
in this slice.
