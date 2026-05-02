# AI RISA Premium Report Factory - Button 2 Premium PDF Visual Intelligence Layout Upgrade Post-Freeze Smoke

Slice: ai-risa-premium-report-factory-button2-premium-pdf-visual-intelligence-layout-upgrade-post-freeze-smoke-v1
Date: 2026-05-02
Type: docs-only post-freeze smoke

## Baseline

1. Baseline commit: f46c1c9
2. Baseline tag: ai-risa-premium-report-factory-button2-premium-pdf-visual-intelligence-layout-upgrade-implementation-v1
3. Starting git status: clean

## Smoke Method

Executed a live route smoke through the Flask application runtime using the actual Button 2 API endpoints and PDF exporter.

Smoke path:

1. Seeded temporary Button 2 queue records for legacy-layout draft, visual-layout draft, and linked-analysis customer-ready paths.
2. Called Button 2 generate endpoint with feature flag off and on.
3. Extracted generated PDF text with `pypdf` to verify layout headings.
4. Called Button 1 and Button 3 drift endpoints.
5. Removed generated PDFs and temporary queue file.
6. Restored runtime health log and verified `git status --short` clean.

## PASS/FAIL Table

| Check | Result | Evidence |
|---|---|---|
| 1. Legacy layout remains default when flag is off | PASS | status=200; report_quality_status=draft_only; extracted PDF contains `1. Cover Page`; does not contain `Traceability Appendix` or `Executive Intelligence` |
| 2. Visual-intelligence layout renders when flag is on | PASS | status=200; report_quality_status=draft_only; extracted PDF contains `Premium Cover`, `Executive Intelligence`, `Combat Dynamics`, `Scenario and Control`, `Traceability Appendix` |
| 3. Exported PDF contains premium cover / executive / combat / scenario / traceability headings | PASS | extracted visual-layout PDF also contains `Section Source Map` |
| 4. Button 2 report generation still respects approval gates | PASS | status=400; errors include `operator_approval_required` |
| 5. Readiness / sparse / combat-intelligence gates remain unchanged | PASS | blocked draft-disabled path returned `blocked_missing_analysis`, `customer_ready=false`, `sparse_completion_status=incomplete`, `readiness_gate_reason=missing_required_outputs_or_analysis`, `combat_content_status=partial`; linked-analysis path returned `customer_ready`, `analysis_source_type=analysis_json`, `sparse_completion_status=complete`, `readiness_gate_reason=all_required_outputs_present`, `combat_content_status=complete`, `missing_engine_outputs=0` |
| 6. No Button 1 / 3 behavior drift | PASS | `/api/phase1/upcoming-events`=200; `/api/accuracy/comparison-summary`=200; `/api/accuracy/confidence-calibration`=200; `/api/accuracy/structural-signal-backfill-planner`=200 |
| 7. No runtime artifacts are committed | PASS | generated PDFs removed; temporary queue file removed; runtime health log restored; final `git status --short` clean |

## Runtime Artifact Cleanup Result

PASS.

Cleanup actions completed after smoke:

1. Removed smoke-created PDF files from `ops/prf_reports`.
2. Removed temporary `ops/prf_queue/upcoming_fight_queue.json`.
3. Restored `ops/runtime_health_log.jsonl`.
4. Verified final git status clean.

## Verdict

PASS / safe for final review.
