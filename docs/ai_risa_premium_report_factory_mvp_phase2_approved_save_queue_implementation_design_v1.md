# AI-RISA Premium Report Factory MVP Phase 2 Approved Save Queue Implementation Design v1

Status: Planning artifact (docs-only)
Slice: ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-implementation-design-v1
Date: 2026-05-01
Mode: Phase 2 implementation design only

## 1. Implementation Scope

This document defines a docs-only implementation design for Phase 2 approved
save queue behavior.

In-scope implementation planning intent:
- Phase 2 approved save queue only
- operator-approved save from already-previewed matchups
- upcoming fight queue display
- no PDF generation
- no result lookup
- no learning/calibration update
- preserve Phase 1 preview behavior

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/ai_risa_premium_report_factory_mvp_phase2_approved_save_queue_design_v1.md
- docs/ai_risa_premium_report_factory_mvp_phase2_approved_save_queue_design_review_v1.md

## 3. Proposed Backend Touchpoints

Planned backend touchpoints for a future implementation slice:
- queue storage helper
- approved-save endpoint
- queue summary/list endpoint
- audit helper if existing project pattern supports it
- focused backend tests

Touchpoint boundary:
- no mutation behavior change outside approved selected-row save flow
- no token digest semantic change
- no token consume semantic change
- no approved-result pipeline behavior change
- no global ledger behavior change

## 4. Proposed Dashboard Touchpoints

Planned dashboard touchpoints for a future implementation slice:
- selection checkbox per previewed matchup
- Select All
- Save Selected to Upcoming Fight Queue
- Upcoming Fight Queue window
- saved status display
- validation warning/error display

## 5. Proposed Approved-Save Endpoint

- POST /api/premium-report-factory/queue/save-selected

## 6. Proposed Queue List Endpoint

- GET /api/premium-report-factory/queue

## 7. Proposed Save Request Contract

Proposed request envelope:
- event_preview
- selected_matchup_previews
- operator_approval
- source_reference
- notes

## 8. Proposed Save Response Contract

Proposed response envelope:
- ok
- generated_at
- accepted_count
- rejected_count
- saved_matchups
- rejected_matchups
- queue_summary
- warnings
- errors

## 9. Proposed saved_matchup Fields

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

## 10. Proposed Queue Behavior

Planned Phase 2 queue behavior:
- save only selected rows
- require explicit operator_approval true
- reject needs_review rows unless future override is separately designed
- preserve source_reference
- deterministic IDs
- deterministic duplicate handling
- queue renders saved upcoming fights
- no PDF/report/result/learning action in Phase 2

## 11. Proposed Persistence Boundary

Planned persistence boundary:
- local-only queue file or local JSON store if existing project pattern supports it
- no external cloud database
- no global ledger overwrite
- no approved-result pipeline write
- append-only audit preferred if existing pattern supports it

## 12. Report Readiness Score Model

Planned deterministic readiness model:
- deterministic simple score only
- data completeness
- event date present
- both fighters present
- source_reference present
- promotion present
- missing-data risk
- no predictive scoring

## 13. Operator Workflow

Planned operator flow:
- paste event card
- preview matchups
- select one/many/all valid matchups
- click Save Selected to Upcoming Fight Queue
- saved fights appear in queue window
- use queue later for report-generation phase

## 14. Test Plan

Required tests for future implementation slice:
- preview still works unchanged
- no save happens on page load
- save requires explicit operator_approval
- selected valid matchups are saved
- needs_review rows are rejected
- source_reference is preserved
- duplicate save is deterministic
- queue endpoint lists saved fights
- no PDF/result/learning controls exist
- backend regression remains green

## 15. Safety/Governance Guardrails

Required guardrails:
- no automatic web scraping
- no automatic save from preview
- no save without operator approval
- no token consume
- no approved-result write
- no global ledger overwrite
- no scoring rewrite
- no report generation
- no result comparison
- no self-learning

## 16. Explicit Non-Goals

Out of scope in this implementation design artifact:
- no PDF report generation
- no real result lookup
- no accuracy comparison
- no calibration learning
- no web discovery
- no external cloud database
- no payment/customer billing
- no automatic global database write without approval

## 17. Implementation Readiness Verdict

The AI-RISA Premium Report Factory MVP Phase 2 approved save queue
implementation design is approved only as a docs-only planning artifact. Actual
implementation remains blocked until a separate Phase 2 implementation slice is
explicitly opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token digest
semantics, token consume semantics, mutation behavior, scoring logic,
approved-result pipeline behavior, global ledger behavior, batch behavior,
prediction behavior, intake parser behavior, or report-generation behavior were
changed in this slice.