# AI RISA Premium Report Factory - Button 2 Betting Market Runtime Wiring Design Review

Slice: ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-review-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only design review

## Design Reference

- Design doc: docs/ai_risa_premium_report_factory_button2_betting_market_runtime_wiring_design_v1.md
- Design commit: 61528a9
- Design tag: ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-v1
- Review scope: docs-only; no runtime changes in this slice

## Scope Confirmation

In-scope confirmation:

1. Button 2 only. PASS
2. Design-only slice. PASS
3. Optional betting-market analyst layer. PASS
4. Additive-only field design. PASS
5. Separate betting-readiness vs report-readiness model. PASS

Out-of-scope confirmation:

1. No Button 1 changes. PASS
2. No Button 3 changes. PASS
3. No live odds fetching. PASS
4. No wagering/staking execution. PASS
5. No writes. PASS
6. No learning/calibration changes. PASS
7. No readiness/sparse/combat gate changes. PASS
8. No PDF feature-flag changes. PASS

## Design Review Findings

### Finding 1 - Governance Safety Framing

The design cleanly frames betting outputs as analytical-only and explicitly prohibits guaranteed-profit language, auto-betting behavior, and user-specific financial execution advice. It also requires both disclaimer and pass/no-bet outputs when betting content is present.

Status: CLEAR

### Finding 2 - Runtime Boundary Isolation

The proposed integration point is after existing readiness/sparse/combat-intelligence evaluation and before final section serialization. This ordering preserves current gating behavior and minimizes risk of coupling betting fields to customer-ready decisions.

Status: CLEAR

### Finding 3 - Additive API Discipline

The 12 betting fields are defined as optional additive outputs with preservation of existing Button 2 response keys. This is consistent with non-breaking API evolution and current lane constraints.

Status: CLEAR

### Finding 4 - Missing-Data Degradation

Missing odds/market inputs degrade betting_market_status and populate betting_missing_inputs while allowing core report generation to continue. This matches the goal of optional analyst layer behavior.

Status: CLEAR

### Finding 5 - Operator UX Safety

The design separates betting readiness from report readiness and requires explicit indication of whether betting content is included before export. It also specifies "betting market unavailable" instead of placeholder claims when data is missing.

Status: CLEAR

### Finding 6 - Testability and Verification

Validation plan is complete and suitable for implementation-phase gating: additive-field checks, unavailable behavior checks, disclaimer/pass-no-bet invariants, cross-button anti-drift checks, and runtime artifact hygiene checks.

Status: CLEAR

### Finding 7 - Live-Data Scope Lock

Design explicitly defers live odds integration into a separate future design/review/implementation lane, preventing silent scope expansion in this runtime-wiring slice.

Status: CLEAR

## Clarifications Locked for Implementation Start

The following clarifications should be resolved at the start of implementation and treated as locked inputs:

1. Betting mode selector contract
- Define exact field name and enum in Button 2 request payload used to opt into betting-analyst mode.

2. Disclaimer template policy
- Define one canonical disclaimer template plus optional strict variants; disallow free-form per-request disclaimer mutation.

3. Pass/no-bet minimum rule set
- Define a minimum deterministic set of no-bet triggers required whenever betting fields are present.

4. Volatility grade rubric
- Lock deterministic thresholds/rules for low, medium, high, unstable to avoid drift across runs.

5. Engine contribution schema
- Lock `betting_engine_contributions` shape (`[{engine_id, status, contribution_summary}]` or equivalent) before endpoint tests.

6. Nullability policy
- Lock per-field nullability for all 12 betting fields under unavailable/partial/ready states.

7. Language policy guard
- Add deterministic content guard to reject or rewrite phrases that imply certainty or guaranteed returns.

## Implementation Guardrails Carried Forward

Binding constraints for the next slice:

1. Betting outputs remain analytical-only.
2. Disclaimer is mandatory whenever any betting field is present.
3. Pass/no-bet conditions are mandatory whenever any betting field is present.
4. No guaranteed-profit language.
5. No auto-betting behavior or execution paths.
6. No modification to customer_ready, readiness, sparse, or combat-intelligence gates.
7. No Button 1 or Button 3 runtime changes.
8. Additive-only response changes.
9. Missing data must degrade betting_market_status only.
10. No writes and no calibration/learning side effects.

## Verdict

APPROVED FOR IMPLEMENTATION HANDOFF.

All review findings are CLEAR and the design is sufficiently constrained for safe implementation under the listed guardrails and clarifications.

## Next Safe Slice

ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-implementation-v1
