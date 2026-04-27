# Post-Ledger-Apply Accuracy Validation Freeze (2026-04-27)

## Checkpoint
- Name: post-ledger-accuracy-freeze
- Prior gate: LEDGER_APPLY_ACCEPTED
- Prior gate: ACCURACY_DASHBOARD_VALIDATION_PASSED

## Applied Rows
- Rows applied to ledger: 7
- Ledger file: ops/accuracy/accuracy_ledger.json

## Updated Fight IDs
1. abdul_rakhman_yakhyaev_vs_brendson_ribeiro
2. ethyn_ewing_vs_rafael_estevam
3. renato_moicano_vs_chris_duncan
4. isaiah_badato_vs_retsu_sashida_prediction
5. isannuea_sor_sasiwat_vs_khunpon_aekmuangnon_prediction
6. payakrut_suajantokmuaythai_vs_ikko_ota_prediction
7. tomyamkoong_bhumjaithai_vs_bejenuta_maximus_prediction

## Validation Endpoint Results
- /api/system/health: HTTP 200, ok:true
- /api/accuracy/comparison-summary: HTTP 200, ok:true
- /api/accuracy/signal-breakdown: HTTP 200, ok:true
- /api/accuracy/method-round-breakdown: HTTP 200, ok:true
- /api/accuracy/confidence-calibration: HTTP 200, ok:true
- /api/accuracy/error-patterns: HTTP 200, ok:true
- /api/accuracy/signal-coverage: HTTP 200, ok:true
- /api/accuracy/structural-signal-backfill-planner: HTTP 200, ok:true

## Comparison Summary Totals
- total_compared: 17
- winner_hits: 7
- winner_misses: 10
- overall_accuracy_pct: 41.18
- method_hits: 8 of 17 method-available

## Signal Coverage Summary
- total predictions: 31
- resolved predictions: 17
- unresolved predictions: 14

## Planner Eligibility Counts
- READY_FOR_BACKFILL: 0
- BLOCKED_NEEDS_SOURCE_VALUES: 16
- UNRESOLVED_RESULT_PENDING: 10
- REQUIRES_ENGINE_RERUN: 0

## Scope Integrity Statements
- Prediction files were unchanged during ledger apply and dashboard validation checkpoints.
- Structural backfill remains globally blocked because READY_FOR_BACKFILL = 0.

## Next Allowed Paths
- Approval-gated MEDIUM-priority official-result lookup.
- Official evidence schema-extension planning.
- Result-resolution monitoring.

## Forbidden Unless Explicitly Approved
- No structural backfill apply.
- No prediction regeneration.
- No report generation.
- No Batch 2 processing.
- No MEDIUM-priority ledger updates without lookup/review/apply gates.

## Hold State
- Checkpoint frozen. Hold before opening new lookup or schema work.
