# AI RISA Premium Report Factory - Button 1 Ranking Runtime Demo Readiness Validation Note

Slice: ai-risa-premium-report-factory-button1-ranking-runtime-demo-readiness-validation-note-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only demo-readiness validation note

## Baseline Under Validation

1. Baseline branch: next-dashboard-polish
2. Baseline commit: cc49892
3. Baseline full commit: cc49892cddff773486031fffa7665e943ed841bb
4. Baseline tag: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-archive-lock-v1
5. Baseline state: clean, remote-verified, archived

## Strict Demo-Readiness Checks

1. git status --short is clean: PASS
- Evidence: no output from git status --short at start of validation.

2. HEAD is cc49892: PASS
- Evidence: git rev-parse --short HEAD returned cc49892.

3. archive-lock tag points at HEAD: PASS
- Evidence: git rev-parse --short ai-risa-premium-report-factory-button1-ranking-runtime-wiring-archive-lock-v1 returned cc49892.

4. root dashboard returns HTTP 200: PASS
- Evidence: GET / returned status 200.

5. Button 1 label is present: PASS
- Evidence: root HTML contains Button 1 label variant (Find & Build Fight Queue or Find and Build Fight Queue).

6. Button 2 label is present: PASS
- Evidence: root HTML contains Generate Premium PDF Reports.

7. Button 3 label is present: PASS
- Evidence: root HTML contains Find Results & Improve Accuracy.

8. Button 1 preview endpoint returns HTTP 200: PASS
- Evidence: POST /api/premium-report-factory/intake/preview returned status 200.

9. Button 1 preview row includes additive ranking fields: PASS
- Evidence: row contains all required ranking fields and diagnostics:
  - fight_readiness_score
  - report_value_score
  - customer_priority_score
  - event_card_priority_score
  - betting_interest_score
  - commercial_sellability_score
  - analysis_confidence_score
  - composite_ranking_score
  - ranking_bucket
  - ranking_reasons
  - ranking_validation_ok
  - ranking_missing_inputs
  - ranking_contract_version

10. Existing preview fields remain unchanged: PASS
- Evidence: row retains temporary_matchup_id, fighter_a, fighter_b, bout_order, weight_class, ruleset, source_reference, parse_status, parse_notes.

11. Ranking output is deterministic: PASS
- Evidence: repeated preview calls with identical payload produced identical composite_ranking_score and ranking_reasons.

12. Save flow approval gate remains intact: PASS
- Evidence: POST /api/premium-report-factory/queue/save-selected with empty payload returned a non-success response and saved_count=0.

13. Button 2 behavior has no drift: PASS
- Evidence: POST /api/operator/compare-with-result returned status 200.

14. Button 3 behavior has no drift: PASS
- Evidence: GET /api/accuracy/comparison-summary returned 200; GET /api/accuracy/confidence-calibration returned 200.

15. no runtime artifacts are committed: PASS
- Evidence: working tree remains clean after validation run.

## Validation Summary

All 15 strict demo-readiness checks passed from baseline cc49892.

## Verdict

PASS.

Safe to demo from cc49892 lineage.
