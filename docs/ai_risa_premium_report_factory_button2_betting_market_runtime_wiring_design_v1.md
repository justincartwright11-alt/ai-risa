# AI RISA Premium Report Factory - Button 2 Betting Market Runtime Wiring Design

Slice: ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only design

## Baseline

1. Starting baseline commit: 16c3768f89191993a9fca4aa405b529246ef3258
2. Branch: next-dashboard-polish
3. Working tree baseline: clean
4. Remote baseline: verified
5. Active repo work at slice start: none

## Goal

Design Button 2 runtime wiring for betting-market intelligence as an optional analyst layer inside premium reports, without creating betting automation and without changing customer-ready gates.

## Scope

In scope:

1. Button 2 only.
2. Design only. No implementation in this slice.
3. Runtime wiring design for optional betting-market intelligence fields.
4. Additive API response model for betting-market outputs.
5. Optional UI/presentation design for betting-market readiness and inclusion controls.
6. Missing-data degradation model that preserves core report generation.

Out of scope:

1. No Button 1 changes.
2. No Button 3 changes.
3. No live odds fetching in this slice.
4. No automatic wagering, staking, execution, or bet placement.
5. No user-specific financial advice.
6. No guaranteed-profit language.
7. No writes.
8. No learning/calibration changes.
9. No changes to approval gates.
10. No changes to readiness/sparse/combat-intelligence gates.
11. No changes to PDF feature-flag behavior.

## Betting-Market Engine Pack Design (Button 2)

Design for ten analytical engines (contract-first, no live execution in this slice):

1. Odds Ingestion Engine
- Purpose: normalize static/attached odds snapshots when provided.
- This slice: design contract only; no live feed.

2. Implied Probability Engine
- Purpose: derive implied probabilities from normalized odds input.
- This slice: deterministic formula design only.

3. Fair Price Engine
- Purpose: estimate fair line/price from report model outputs.
- This slice: contract for additive fair-price estimate only.

4. Market Edge Engine
- Purpose: compare implied probabilities vs fair-price estimate.
- This slice: produce analytical edge summary only.

5. Prop Market Engine
- Purpose: optional notes for prop-oriented angles based on existing analysis signals.
- This slice: optional notes only; no recommendation execution.

6. Volatility Grade Engine
- Purpose: classify volatility regime (low/medium/high/unstable).
- This slice: deterministic grade vocabulary only.

7. Round-Band Betting Path Engine
- Purpose: describe hypothetical round-band pathways tied to scenario logic.
- This slice: analytical path text only.

8. Pass / No-Bet Condition Engine
- Purpose: declare explicit conditions where no bet should be taken.
- This slice: mandatory output whenever betting fields are present.

9. Market Movement Watch Engine
- Purpose: define watch triggers for line movement significance.
- This slice: contract-only trigger definitions; no live polling.

10. Betting Risk Disclaimer Engine
- Purpose: attach mandatory risk disclaimer language.
- This slice: mandatory output whenever betting fields are present.

## Output Field Design (Additive)

Additive Button 2 output fields to design:

1. betting_market_status
2. odds_source_status
3. implied_probability
4. fair_price_estimate
5. market_edge_summary
6. prop_market_notes
7. volatility_grade
8. round_band_betting_path
9. pass_no_bet_conditions
10. betting_risk_disclaimer
11. betting_engine_contributions
12. betting_missing_inputs

Field semantics:

1. betting_market_status
- Values: unavailable | partial | ready
- Missing data degrades this status only; core report flow remains intact.

2. odds_source_status
- Values: absent | stale | snapshot_attached | verified_snapshot
- No live-source assurance implied in this slice.

3. implied_probability
- Optional numeric/object payload derived from odds snapshot only.

4. fair_price_estimate
- Optional analytical estimate tied to report model outputs.

5. market_edge_summary
- Optional descriptive summary of analytical edge comparison.

6. prop_market_notes
- Optional analyst notes; no guarantees, no execution advice.

7. volatility_grade
- Optional bounded vocabulary (low, medium, high, unstable).

8. round_band_betting_path
- Optional scenario-aligned path summary.

9. pass_no_bet_conditions
- Required whenever any betting content is present.

10. betting_risk_disclaimer
- Required whenever any betting content is present.

11. betting_engine_contributions
- Optional traceability object/list showing which engines contributed output.

12. betting_missing_inputs
- Optional list describing missing market inputs.

## Governance Constraints

Hard requirements:

1. Betting outputs are analytical only.
2. Risk disclaimer is mandatory when betting fields are present.
3. Pass/no-bet conditions are mandatory when betting fields are present.
4. No guaranteed-profit claims.
5. No auto-place bets, auto-stakes, or wagering execution.
6. No change to prediction/customer_ready gates.
7. No blocking of normal reports unless operator explicitly chooses betting-analyst mode.
8. Missing betting data degrades betting_market_status only and must not break core report generation.

## Runtime Wiring Design (Button 2)

### 1) Report Assembly Integration Point

Wire betting-market enrichment after existing readiness/sparse/combat-intelligence gate evaluation and before final section serialization for optional betting content.

Order:

1. Run existing report pipeline and preserve current gates unchanged.
2. Evaluate operator-selected report mode (standard vs betting-analyst optional mode).
3. If betting mode is not selected, omit betting section outputs entirely.
4. If betting mode is selected, compute betting engine outputs from available static inputs.
5. Attach additive betting fields to response/report context.
6. Enforce mandatory disclaimer + pass/no-bet fields when betting fields are present.

### 2) Missing Data Behavior

1. If odds/market inputs are missing, set betting_market_status=unavailable.
2. Populate betting_missing_inputs with missing components.
3. Do not generate placeholder claims pretending market certainty.
4. Continue core report generation unchanged.

### 3) Safety Boundary

1. No write paths added.
2. No gate bypass.
3. No modifications to approval state logic.
4. No effect on non-betting report mode outputs.

## UI Design (Button 2)

Design requirements:

1. Show betting-market readiness separately from report readiness.
2. Betting section is optional and clearly labeled as analyst-only.
3. Missing odds/market data shows "betting market unavailable".
4. No fabricated placeholder betting claims.
5. Operator can see whether betting content is included before PDF export.
6. Existing readiness and customer-ready controls remain primary and unchanged.

Suggested UI indicators:

1. Betting Readiness badge (`unavailable`/`partial`/`ready`).
2. Betting Content Included toggle/state (display only in this slice).
3. Betting Disclaimer preview snippet.
4. Pass/No-Bet Conditions preview line.

## API Design (Additive Only)

Rules:

1. Preserve all existing Button 2 response keys unchanged.
2. Betting fields are additive and optional.
3. Betting output appears only when relevant mode/inputs are present.
4. No live market fetch support in this slice.
5. Future live odds integration requires a separate design/review/implementation lane.

Example additive payload fragment (conceptual):

- betting_market_status: "unavailable"
- odds_source_status: "absent"
- implied_probability: null
- fair_price_estimate: null
- market_edge_summary: null
- prop_market_notes: []
- volatility_grade: null
- round_band_betting_path: null
- pass_no_bet_conditions: ["No verified odds snapshot attached"]
- betting_risk_disclaimer: "Analytical content only. No wagering advice or guaranteed outcomes."
- betting_engine_contributions: []
- betting_missing_inputs: ["odds_snapshot", "market_line_context"]

## Validation Plan

Implementation-phase validation must prove:

1. Betting-market fields are additive only.
2. Reports without betting data still generate normally.
3. Missing odds produce betting_market_status=unavailable.
4. Betting disclaimer always appears when betting fields are present.
5. Pass/no-bet conditions always appear when betting fields are present.
6. Existing Button 2 readiness/sparse/combat tests remain green.
7. Existing Button 1 ranking tests remain green.
8. Existing Button 3 tests remain green.
9. No runtime artifacts are committed.

Recommended test layers:

1. Engine contract tests for all ten betting-market engines.
2. API response tests for additive-only optional fields.
3. Mode-selection tests (standard vs betting-analyst mode).
4. Missing-input degradation tests.
5. Governance assertion tests (disclaimer/pass-no-bet mandatory when betting fields present).
6. Cross-button anti-drift regression tests.

## Risks and Guardrails

Primary risks:

1. Betting outputs being misread as guarantees.
2. Scope creep into execution advice or auto-betting behavior.
3. Gate coupling that accidentally impacts customer-ready outputs.
4. Placeholder market claims when real inputs are absent.

Guardrails:

1. Mandatory betting disclaimer + pass/no-bet conditions.
2. Strict additive-only output policy.
3. Explicit separation of betting readiness from report readiness.
4. Missing-input behavior must degrade betting_market_status only.
5. Preserve existing gate logic and feature-flag behavior unchanged.

## Design Verdict

READY FOR DESIGN REVIEW.

This slice is docs-only and defines boundaries for optional betting-market intelligence wiring without introducing runtime behavior changes.

## Next Safe Slice

ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-review-v1
