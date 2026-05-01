# AI-RISA Premium Report Factory MVP Phase 1 Intake Dashboard Panel Implementation Design v1

Status: Planning artifact (docs-only)
Slice: ai-risa-premium-report-factory-mvp-phase1-intake-dashboard-panel-implementation-design-v1
Date: 2026-05-01
Mode: Dashboard panel implementation design only

## 1. Implementation Scope

This document defines a docs-only implementation design for adding the first
visible Premium Report Factory intake panel to the dashboard surface without
expanding backend behavior.

In-scope planning intent:
- visible dashboard panel only
- connect to existing preview endpoint:
  - POST /api/premium-report-factory/intake/preview
- preview-only
- no save/apply/write
- no PDF generation
- no result lookup
- no learning/calibration update

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/ai_risa_premium_report_factory_mvp_phase1_intake_dashboard_panel_design_v1.md
- docs/ai_risa_premium_report_factory_mvp_phase1_intake_dashboard_panel_design_review_v1.md

## 3. Proposed Dashboard Touchpoints

Planned touchpoints for a future implementation slice:
- advanced dashboard template or existing dashboard template pattern
- existing JavaScript/fetch pattern if present
- backend/render tests
- no new backend endpoint

Touchpoint boundary:
- reuse existing endpoint contract only
- avoid backend behavior changes in panel implementation
- keep rendering and fetch behavior deterministic

## 4. Proposed Panel Title

- Premium Report Factory - Event Card Intake Preview

## 5. Proposed Button

- Preview Event Card

## 6. Proposed Input Fields

- raw_card_text
- event_name
- event_date
- promotion
- location
- source_reference
- notes

## 7. Proposed Output Sections

- event_preview
- matchup_previews
- parse_warnings
- errors

## 8. Proposed Matchup Table Fields

- temporary_matchup_id
- fighter_a
- fighter_b
- bout_order
- weight_class
- ruleset
- source_reference
- parse_status
- parse_notes

## 9. Proposed Panel Behavior

- operator pastes/writes card text
- operator fills optional metadata
- operator clicks Preview Event Card
- panel calls existing preview endpoint
- panel renders event preview
- panel renders matchup table
- panel renders parse warnings and errors
- panel exposes no save/write/apply/report/result/learning controls

## 10. Failure And Edge-State Handling

Planned handling states:
- empty raw_card_text
- missing event_date warning
- incomplete matchups marked needs_review
- endpoint error displayed without breaking panel
- no matchups found displayed as preview warning/state

UI behavior expectations:
- never hide backend warning/error payloads
- keep panel operable after request failure
- preserve operator ability to edit source text and retry preview

## 11. Safety/Governance Guardrails

- no hidden save controls
- no global database write
- no global ledger write
- no approved-result pipeline write
- no token consume
- no PDF/report generation
- no result comparison
- no learning/calibration update
- no customer billing

## 12. Future Implementation Test Plan

- panel exists
- input fields exist
- Preview Event Card button exists
- button/fetch targets /api/premium-report-factory/intake/preview
- result window exists
- matchup table render path exists
- warnings/errors render path exists
- no save/write/apply controls exist
- existing Phase 1 endpoint tests remain green
- backend regression remains green

## 13. Explicit Non-Goals

- no backend endpoint changes
- no preview contract changes
- no write/mutation path introduction
- no queue/save/report controls in this phase
- no web discovery integration
- no billing/entitlement surface changes

## 14. Implementation Readiness Verdict

The AI-RISA Premium Report Factory MVP Phase 1 intake dashboard panel
implementation design is approved as a docs-only planning artifact. Actual
dashboard implementation remains blocked until a separate implementation slice
is explicitly opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake behavior, or report-generation behavior were changed
in this slice.
