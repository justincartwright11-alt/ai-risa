# AI RISA Premium Report Factory - Button 3 Accuracy Calibration Runtime Wiring Design

Slice: ai-risa-premium-report-factory-button3-accuracy-calibration-runtime-wiring-design-v1
Date: 2026-05-03
Branch: next-dashboard-polish
Type: docs-only design

## Baseline

- Starting commit: 6407935
- Starting full commit: 64079353936fe292ce3e442090bcddefab812cea
- Baseline state: CLOSED / ARCHIVED / STABLE / DEMO-READY
- Active repo work at start: none

## Design Goal

Design Button 3 runtime wiring for:

1. Accuracy comparison
2. Result verification
3. Report-outcome scoring
4. Operator-approved calibration recommendations

This slice is design-only. No implementation code changes are in scope.

## Scope Lock

### In Scope

1. Button 3 runtime wiring design only
2. Additive output contract design
3. Engine-level responsibilities and interfaces
4. Governance and approval-gate rules
5. UI and API design contract for operator workflow
6. Validation plan for future implementation/review slices

### Out of Scope

1. No implementation in this slice
2. No Button 1 changes
3. No Button 2 changes
4. No automatic learning
5. No automatic calibration write
6. No global database write in this slice
7. No customer PDF generation
8. No betting behavior
9. No permanent learning/calibration update without operator approval

## Runtime Wiring Architecture (Design)

Button 3 runtime wiring is structured as a read/analyze/propose flow with a strict approval gate:

1. Ingest prediction artifact + official result inputs
2. Compare prediction vs official outcome
3. Segment accuracy by confidence and context
4. Score winner/method/round + section-level report accuracy
5. Produce calibration recommendations as proposals only
6. Produce pattern-memory update proposals as proposals only
7. Emit learning gate status as approval-required
8. Return additive response fields with full audit metadata

No writes occur in this runtime wiring path.

## Engine Design

### 1) Result Comparison Engine

Purpose:
- Align prediction record with official result record and compute direct match signals.

Inputs:
- prediction_report_id or local_result_key
- predicted winner/method/round
- official winner/method/round + source metadata

Outputs:
- result_comparison_status
- official_result_source_status
- predicted_winner_match
- method_match
- round_match

Rules:
- Missing official result does not fail request; returns unresolved status.
- Source confidence and verification flags are preserved in status fields.

### 2) Accuracy Segment Engine

Purpose:
- Segment prediction quality by confidence and context bands.

Inputs:
- prediction confidence
- outcome match signals
- optional contextual tags (card position, ruleset, etc.)

Outputs:
- confidence_accuracy_band

Rules:
- Banding must be deterministic and versioned.
- Segmenting is analytical and does not change model weights.

### 3) Prediction Outcome Scoring Engine

Purpose:
- Compute overall prediction outcome score using weighted winner/method/round signals.

Inputs:
- predicted_winner_match
- method_match
- round_match
- scoring rubric version

Outputs:
- overall_report_accuracy_score

Rules:
- Scoring rubric must be transparent and auditable.
- No score-based auto-learning behavior.

### 4) Method / Round Accuracy Engine

Purpose:
- Evaluate method and round specificity accuracy independently from winner.

Inputs:
- predicted method/round
- official method/round

Outputs:
- method_match
- round_match

Rules:
- Explicitly distinguish exact, partial, unresolved states.
- Missing official subfields degrade to unresolved, not hard failure.

### 5) Report Section Accuracy Engine

Purpose:
- Score report sections against verified outcome signals and post-event evidence.

Inputs:
- section-level prediction claims
- official outcome facts
- section rubric version

Outputs:
- section_accuracy_scores

Rules:
- Section scoring is additive metadata only.
- No direct overwrite of original report content.

### 6) Calibration Recommendation Engine

Purpose:
- Generate candidate calibration actions from observed error patterns.

Inputs:
- outcome scoring summaries
- confidence-band deltas
- section error distribution

Outputs:
- calibration_recommendations

Rules:
- Recommendations are proposals only in this path.
- No automatic calibration writes.

### 7) Pattern Memory Update Proposal Engine

Purpose:
- Propose memory pattern adjustments derived from repeated mismatches.

Inputs:
- normalized mismatch signatures
- recurrence counts
- source reliability signals

Outputs:
- pattern_memory_update_proposals

Rules:
- Proposal output only; no memory mutations in this path.
- Each proposal includes rationale and confidence.

### 8) Operator-Approved Learning Gate Engine

Purpose:
- Enforce explicit approval requirement before any permanent learning/calibration update.

Inputs:
- operator approval signal
- generated proposals
- policy controls

Outputs:
- learning_gate_status
- learning_gate_reason
- operator_approval_required

Rules:
- Default state is approval required.
- No silent learning, no auto-apply, no implicit approvals.

## Button 3 Additive Output Fields (Design Contract)

The following fields are added to Button 3 responses without removing or renaming existing keys:

1. result_comparison_status
2. official_result_source_status
3. predicted_winner_match
4. method_match
5. round_match
6. confidence_accuracy_band
7. section_accuracy_scores
8. overall_report_accuracy_score
9. calibration_recommendations
10. pattern_memory_update_proposals
11. learning_gate_status
12. learning_gate_reason
13. operator_approval_required

### Field Intent and Nullability Policy (Design)

- result_comparison_status: required string, one of ready/unresolved/partial/error-safe.
- official_result_source_status: required string describing source verification state.
- predicted_winner_match: nullable bool or tri-state string for unresolved cases.
- method_match: nullable bool or tri-state string for unresolved cases.
- round_match: nullable bool or tri-state string for unresolved cases.
- confidence_accuracy_band: nullable object/string when confidence unavailable.
- section_accuracy_scores: required list/object, empty when section scoring not possible.
- overall_report_accuracy_score: nullable numeric when unresolved.
- calibration_recommendations: required list, possibly empty.
- pattern_memory_update_proposals: required list, possibly empty.
- learning_gate_status: required string; default approval_required.
- learning_gate_reason: required string with deterministic policy reason.
- operator_approval_required: required bool, true by default for any apply action.

## Governance Design

### Allowed

1. Search
2. Compare
3. Analyze
4. Score
5. Propose updates

### Forbidden Without Approval

1. Permanent result writes
2. Calibration updates
3. Pattern memory updates
4. Any prediction-weight changes

### Required Controls

1. No silent learning
2. No automatic changes to prediction weights
3. No overwriting existing results without review
4. All changes auditable with actor/time/reason/proposal-id
5. Any future apply action must check operator approval

## UI Design Contract (Button 3)

Button 3 should present distinct sections:

1. Official Result Comparison Panel
- Show official source status and winner/method/round matches.

2. Prediction-vs-Result Accuracy Panel
- Show confidence band and overall score.

3. Report Section Accuracy Panel
- Show section-level scores with unresolved indicators where applicable.

4. Calibration Recommendations Panel
- Show recommendation proposals only, not applied changes.

5. Proposed Learning Updates Panel
- Show pattern memory proposals separately from applied updates.

6. Operator Approval Panel
- Explicit control required before any apply flow in future slices.

UI must clearly separate:
- Proposed
- Approved
- Applied

This slice only designs proposed state behavior.

## API Design Contract

1. Additive response fields only
2. Preserve existing Button 3 response keys and behaviors
3. Existing accuracy endpoints remain stable
4. Future apply endpoint must be separate and approval-gated

### Candidate Read Endpoint Behavior (Design)

- Existing summary/comparison endpoints append designed fields where relevant.
- Unresolved official result returns unresolved state, not HTTP failure.
- Error-safe behavior returns partial analytical response where possible.

### Future Apply Endpoint Requirement (Design)

- Separate endpoint namespace
- Requires explicit operator approval payload
- Emits immutable audit record for each applied change
- Must reject apply requests when approval signal absent

## Validation Plan for Implementation Slice

1. Result comparison returns additive accuracy fields.
2. Missing official result returns unresolved status, not failure.
3. Calibration recommendations are proposals only.
4. No learning update occurs without operator approval.
5. Existing Button 1 ranking tests remain green.
6. Existing Button 2 readiness/combat/PDF/betting tests remain green.
7. Existing Button 3 tests remain green.
8. No runtime artifacts committed.

## Risks and Mitigations

1. Risk: Hidden write path introduced during wiring.
- Mitigation: explicit no-write contract checks and approval-gate tests.

2. Risk: Existing Button 3 response contracts regress.
- Mitigation: additive-only schema policy and compatibility tests.

3. Risk: Recommendation logic interpreted as auto-apply.
- Mitigation: strict proposal labeling and operator_approval_required=true default.

4. Risk: Official result gaps cause hard failures.
- Mitigation: unresolved/partial status model and graceful degradation.

## Acceptance Criteria for Design Review

1. Scope lock is explicit and complete.
2. All 8 engines are fully defined with purpose/inputs/outputs/rules.
3. All 13 additive output fields are designed with policy intent.
4. Governance constraints prevent silent learning and unauthorized writes.
5. UI contract separates proposed vs applied updates.
6. API contract preserves existing Button 3 stability.
7. Validation plan maps directly to testable behaviors.

## Next Safe Slice

ai-risa-premium-report-factory-button3-accuracy-calibration-runtime-wiring-design-review-v1
