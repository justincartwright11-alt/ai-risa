# AI-RISA Premium Report Factory MVP Phase 2 Approved Save Queue Design v1

Status: Planning boundary (docs-only)
Slice: ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-design-v1
Date: 2026-05-01
Mode: Phase 2 design only

## 1. Phase 2 Purpose

Define the Phase 2 design for converting Phase 1 previewed event-card matchups
into an operator-approved upcoming fight queue while preserving Phase 1
preview-only behavior.

Design intent:
- convert Phase 1 previewed event-card matchups into an operator-approved upcoming fight queue
- allow the operator to select one, many, or all previewed matchups
- save only after explicit operator approval
- prepare fights for later report generation
- preserve Phase 1 preview-only behavior

## 2. Current Phase 1 Baseline

Current locked baseline:
- visible Advanced Dashboard panel exists
- operator can paste/write event-card text
- Preview Event Card button calls POST /api/premium-report-factory/intake/preview
- event_preview and matchup_previews render
- no save/write/apply/report/result/learning controls exist in Phase 1

## 3. Proposed Phase 2 Workflow

Proposed operator workflow:
- paste/write event card
- preview extracted matchups
- operator reviews matchup rows
- operator selects one, many, or all matchups
- operator clicks approved save
- selected matchups are saved to an upcoming fight queue
- saved queue is shown in a selectable window
- saved fights become eligible for later report generation phase

## 4. Proposed Dashboard Additions

Planned Phase 2 surface additions:
- Select checkbox per matchup
- Select All
- Save Selected to Upcoming Fight Queue
- Upcoming Fight Queue window
- saved status display
- validation warnings/errors display

## 5. Proposed Data Model

Proposed queue/save data fields:
- event_id
- matchup_id
- fighter_a
- fighter_b
- event_name
- event_date
- promotion
- location
- source_reference
- bout_order
- weight_class
- ruleset
- report_readiness_score
- report_status
- result_status
- accuracy_status
- queue_status
- created_at
- approved_by_operator
- approval_timestamp

## 6. Proposed Save Behavior

Proposed Phase 2 save behavior:
- explicit operator approval required
- no automatic save from preview
- deterministic IDs
- duplicate handling must be deterministic
- source_reference must be preserved
- incomplete rows remain blocked or needs_review
- append-only audit row preferred
- no hidden global write

## 7. Proposed Queue Behavior

Proposed queue behavior:
- queue displays saved upcoming fights
- selectable one/many/all
- shows readiness state
- shows source reference
- shows report_status
- no PDF generation in Phase 2
- no result lookup in Phase 2
- no learning update in Phase 2

## 8. Safety And Governance Guardrails

Required guardrails:
- no automatic web scraping
- no automatic database write from preview
- no PDF generation
- no result search
- no approved-result pipeline mutation
- no global ledger overwrite
- no token consume
- no self-learning
- no customer billing
- no batch automation beyond selected approved rows

## 9. Future Implementation Test Plan

Required tests for future implementation slices:
- preview remains unchanged
- selected matchup save requires explicit action
- no save happens on page load
- incomplete matchup cannot be silently saved
- source_reference preserved
- duplicate selected rows handled deterministically
- queue renders saved fights
- no PDF/result/learning controls added
- backend regression remains green

## 10. Explicit Non-Goals

Out of scope for this Phase 2 design note:
- no PDF report generation
- no real result lookup
- no accuracy comparison
- no calibration learning
- no web discovery
- no external cloud database
- no payment/customer billing
- no automatic global database write without approval

## 11. Final Design Verdict

Phase 2 is approved only as a docs-only design boundary. Implementation remains
blocked until separate implementation-design and implementation slices are
opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake parser behavior, or report-generation behavior were
changed in this slice.