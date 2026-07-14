# AI-RISA Single Rerun Structured Contract Proof Review Lock v1

## 1. Review Purpose
Lock the review for the single structured-contract rerun proof slice and freeze findings before next diagnosis work.

## 2. Baseline Problem
The prior closed-loop path depended on Button 2 PDF-text extraction, which produced weak prediction-field quality for downstream Button 3 inputs.

## 3. Structured-Contract Improvement Chain
Button 2 now emits a structured prediction contract from generation context, and Button 3 consumes that contract directly, exposing structured prediction context and structural evidence preview in preview-only mode.

## 4. Rerun Target
- Fight: Zhang Weili vs Yan Xiaonan
- Event: UFC 300
- Event identity match: YES

## 5. Proof Artifact
- Artifact: ops/validation_runs/pilot_fight_4_structured_contract_rerun_proof_v1.json
- Proof run status: completed
- Improvement verdict: improved

## 6. Old vs New Comparison
- Old prediction source: actual_system_output_pdf_text
- New prediction source: button2_structured_prediction_contract
- Old method: Unknown
- New method: Decision
- Old round: Unknown
- New round: Full Distance

## 7. Accuracy Result
- Accuracy outcome: partial

## 8. Structural Evidence Result
- Old structural evidence score: 0.0
- New structural evidence preview score: 1.0
- Structural evidence state: supported

## 9. Protected-Write Result
- Learning policy changed: NO
- Protected writes: 0
- Customer release count: 0
- Auto learning count: 0

## 10. Product Finding
The structured-contract path improved Button 2 to Button 3 input quality under the real closed-loop rerun target while preserving operator-governed non-mutation boundaries.

## 11. Remaining Limitation
The rerun did not prove full accuracy improvement because the outcome remained partial.

## 12. Next Recommended Slice
method-round-normalization-diagnosis-v1

## 13. Stop Condition
This review lock closes the single structured-contract rerun proof slice. No additional reruns, policy changes, or write-path expansions are included in this lock.

## Required Conclusion
The structured-contract upgrade improved Button 2 to Button 3 input quality without changing prediction policy, learning policy, customer release behavior, or protected-write boundaries. The rerun did not prove full accuracy improvement because the outcome remained partial, but it did prove that the prior PDF-text extraction weakness has been materially reduced.
