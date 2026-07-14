# AI-RISA Structured Contract Pilot Batch 2 Planning Lock v1

## 1. Purpose
Define and lock the Pilot Batch 2 execution plan to validate that structured-contract ingestion and normalized-scoring behavior generalize beyond a single-fight proof while preserving AI-RISA safety boundaries.

## 2. Current Locked Baseline
- Button 2 emits structured_prediction.
- Button 3 consumes structured_prediction.
- Button 3 exposes structural_evidence_preview.
- Button 3 exposes method_round_normalization_preview.
- Single-fight normalized rerun proof is locked for Zhang Weili vs Yan Xiaonan (UFC 300), improving from partial to hit.
- Learning policy changed: NO.
- Protected writes: 0.

## 3. Why Batch 2 Is Needed
Single-fight proof confirms pathway capability but does not establish multi-fight consistency. Batch 2 is required to verify repeatability of identity integrity, structured prediction handoff, normalized scoring explainability, and safety invariants across additional clean fights.

## 4. Batch 2 Success Criteria
- Structured-contract handoff is present and valid for each fight.
- Normalized scoring preview is present and explainable for each fight.
- Structural evidence preview is present for each fight.
- Identity continuity is clean across event/date/source fields.
- Protected write boundaries remain intact for all runs.
- Learning policy remains unchanged.

## 5. Batch 2 Fight-Selection Rules
- Use only clean event-scoped fight identity.
- No mismatched event/date/source identity.
- Each fight must include scheduled_rounds.
- Recommended selection: start with 3 fights first, not 5.

## 6. Minimum Fight Count
- Minimum clean fights: 3.

## 7. Maximum Fight Count
- Maximum clean fights: 5.

## 8. Required Identity Fields
Each fight run must provide and preserve:
- fight_id
- event_name
- event_date
- fighter_a
- fighter_b
- source_url
- source_tier
- promotion

## 9. Required Structured Prediction Fields
Each fight must prove Button 2 structured_prediction is present with:
- contract_version
- predicted_winner
- predicted_method
- predicted_round
- confidence
- structural_reasoning
- tactical_pathway
- evidence_notes

## 10. Required Normalized Scoring Fields
Each fight must prove Button 3 returns:
- method_round_normalization_preview present
- predicted_method_normalized
- actual_method_normalized
- predicted_round_normalized
- actual_round_normalized
- scheduled_rounds echoed
- full_distance_resolved flag
- method_score and round_score explainable

## 11. Required Protected-Write Checks
For each fight, all must remain zero/false:
- protected writes total = 0
- customer release count = 0
- auto learning count = 0
- learning policy changed = NO
- mutation/write flags remain false across preview path

## 12. Required Stop Conditions
- Stop immediately if any identity mismatch is detected.
- Stop immediately if structured_prediction is missing.
- Stop immediately if method_round_normalization_preview is missing.
- Stop immediately if structural_evidence_preview is missing.
- Stop immediately if any protected write, customer release, or auto-learning signal is non-zero.
- Do not require every fight to be hit.
- Do require method/round scoring explainability for every fight.

## 13. Cost-Control Rules
- Execute Batch 2 in controlled expansion.
- Run one fight first, then stop for review.
- Expand only after review confirms invariants remain intact.
- No full-batch run in a single step.
- No code changes in planning lock execution.

## 14. Recommended Next Slice
- pilot-batch-2-fight-1-structured-normalized-proof-v1

## Required Conclusion
Pilot Batch 2 should test whether the structured-contract and normalized-scoring upgrades generalize beyond the single Zhang Weili vs Yan Xiaonan proof while preserving AI-RISA’s non-mutating, operator-governed safety boundaries. The next execution slice should run only one Batch 2 fight first, then stop for review before expanding to additional fights.
