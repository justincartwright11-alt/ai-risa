# AI-RISA Premium Report Factory MVP Scope Design v1

Status: Draft narrowing boundary (docs-only)
Slice: ai-risa-premium-report-factory-mvp-scope-design-v1
Date: 2026-05-01
Mode: MVP scope design only

## 1. MVP Purpose

Define the smallest sellable Premium Report Factory workflow while keeping global
database expansion and learning ambitions staged, controlled, and non-automatic.

MVP intent:
- Deliver a minimal commercially usable report workflow.
- Preserve trust through manual approval and traceability.
- Prevent premature automation risk in discovery, writes, and learning.

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/ai_risa_premium_report_factory_workflow_design_v1.md
- docs/ai_risa_premium_report_factory_workflow_design_review_v1.md

## 3. Recommended MVP Boundary

MVP includes:
- Manual/paste event-card intake.
- One selectable upcoming fight list.
- One report-readiness ranking score.
- Manual-approved save to local/global database surfaces.
- PDF generation from selected fights only if existing report-generation path already supports it.

MVP excludes automation in this phase:
- No automatic web write.
- No automatic result write.
- No automatic self-learning.

## 4. MVP Button 1 Boundary

Button: Find This Week's Fight Cards

MVP behavior:
- Paste/manual upcoming event card intake.
- Optional read-only web scout only if already available.
- Extract Fighter A vs Fighter B matchups.
- Compute report-readiness ranking.
- Require operator approval before save.

## 5. MVP Button 2 Boundary

Button: Build Premium PDF Reports

MVP behavior:
- Select one or many report-ready fights.
- Generate premium PDF reports using existing report-generation surfaces only.
- Export customer-ready files.
- Record report status.

## 6. MVP Button 3 Boundary

Button: Find Results + Compare Accuracy

MVP behavior:
- Manual or read-only result lookup.
- Compare actual outcomes against existing analysis/report outputs.
- Update accuracy only through approved-result pipeline controls.
- Show accuracy/readiness views only.
- No automatic learning updates.

## 7. MVP Windows

- Upcoming Fight Queue
- Report Builder
- Result Comparison Queue
- Accuracy Snapshot

## 8. Data Model Minimum

Minimum MVP fields:
- event_id
- matchup_id
- fighter_a
- fighter_b
- event_date
- promotion
- source_reference
- report_readiness_score
- report_status
- result_status
- accuracy_status

## 9. Excluded From MVP

- Automatic full web scraping
- Automatic global writes
- Automatic report selling/billing
- External cloud database
- Automatic self-learning
- Batch scoring without approval

## 10. Future Phases

- Web discovery
- Global database expansion
- PDF commercial packaging
- Result automation
- Calibration dashboard
- Approved learning loop

## 11. Risks and Guardrails

Primary risks:
- Scope creep into automation before quality proof.
- Uncontrolled data ingestion affecting ranking/report trust.
- Learning drift if approval gates are bypassed.

Required guardrails:
- Keep manual approval gates for save/apply steps.
- Preserve read-only or manual-first result handling.
- Restrict MVP to existing report-generation paths.
- Maintain approved-result pipeline as the only accuracy-update path.
- Enforce test-gated implementation slices before release progression.

## 12. Implementation Readiness Verdict

The AI-RISA Premium Report Factory MVP scope is approved only as a docs-only
narrowing artifact.

Implementation remains blocked until a separate implementation-design slice is
explicitly opened and test-gated.

## Freeze Compliance Record

This artifact is docs-only.
No code, tests, endpoint behavior, dashboard frontend behavior, token semantics,
mutation behavior, scoring logic, approved-result pipeline behavior, global ledger
behavior, batch behavior, prediction behavior, intake behavior, or report-generation
behavior were changed in this slice.
