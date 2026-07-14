# AI-RISA Pilot Batch 2 Summary Lock v1

## 1. Summary purpose
Lock the minimum Pilot Batch 2 completion summary after three clean event-scoped validation fights, confirming structured-contract continuity, normalized-scoring explainability, structural evidence support, and non-mutating safety boundary integrity.

## 2. Planning reference
- Planning lock: docs/structured_contract_pilot_batch_2_planning_lock_v1.md
- Minimum fight count required: 3
- Maximum fight count allowed: 5
- Minimum fight count completed: 3

## 3. Completed fight list
1. Kayla Harrison vs Holly Holm (UFC 300)
2. Bo Nickal vs Cody Brundage (UFC 300)
3. Zhang Weili vs Yan Xiaonan (UFC 300)

## 4. Fight 1 result
- Fight: Kayla Harrison vs Holly Holm
- Proof artifact: ops/validation_runs/pilot_batch_2_fight_1_structured_normalized_proof_v1.json
- Accuracy outcome: partial
- Winner score: hit
- Method score: miss
- Round score: miss
- Structural evidence state: supported
- Structural evidence score: 1.0
- Protected writes: 0

## 5. Fight 2 result
- Fight: Bo Nickal vs Cody Brundage
- Proof artifact: ops/validation_runs/pilot_batch_2_fight_2_structured_normalized_proof_v1.json
- Accuracy outcome: partial
- Winner score: hit
- Method score: miss
- Round score: miss
- Structural evidence state: supported
- Structural evidence score: 1.0
- Protected writes: 0

## 6. Fight 3 result
- Fight: Zhang Weili vs Yan Xiaonan
- Proof artifact: ops/validation_runs/pilot_batch_2_fight_3_structured_normalized_proof_v1.json
- Accuracy outcome: hit
- Winner score: hit
- Method score: hit
- Round score: hit
- Structural evidence state: supported
- Structural evidence score: 1.0
- Protected writes: 0

## 7. Aggregate structured-contract result
- Clean event-scoped identity: 3/3
- scheduled_rounds present: 3/3
- Button 2 structured_prediction present: 3/3
- Button 3 structured_prediction accepted: 3/3

## 8. Aggregate normalized-scoring result
- method_round_normalization_preview present: 3/3
- Winner scores: 3 hit
- Method scores: 1 hit, 2 miss
- Round scores: 1 hit, 2 miss

## 9. Aggregate structural-evidence result
- structural_evidence_preview present: 3/3
- structural_evidence supported: 3/3
- structural_evidence_score=1.0: 3/3

## 10. Aggregate safety result
- Learning policy changed: NO
- Protected writes: 0
- Customer release count: 0
- Auto learning count: 0

## 11. Accuracy distribution
- Accuracy outcomes: 2 partial, 1 hit

## 12. Product finding
Batch 2 minimum validation established repeatable structured handoff and explainable normalized scoring across three clean UFC 300 fights while maintaining supported structural evidence and strict non-mutating boundaries.

## 13. Remaining limitation
Accuracy distribution remains mixed (2 partial, 1 hit), so behavioral validation is complete for this minimum batch but outcome precision variance remains expected fight-to-fight.

## 14. Recommended next slice
batch-2-closeout-tag-readiness-check-v1

## 15. Stop condition
Stop after this summary lock. Do not run additional fights and do not modify code, JSON evidence, learning policy, or protected-write pathways in this slice.

## Required conclusion
Pilot Batch 2 minimum validation passed. The structured-contract and normalized-scoring upgrades generalized across three clean event-scoped UFC 300 fights while preserving non-mutating safety boundaries. The batch proved repeatable structured handoff, explainable normalized scoring, supported structural evidence, and zero protected writes. Accuracy distribution remained mixed, which is acceptable because Batch 2 was designed to validate system behavior and scoring explainability, not force every fight to be correct.
