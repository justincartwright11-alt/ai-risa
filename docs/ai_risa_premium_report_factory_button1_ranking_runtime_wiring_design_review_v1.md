# AI RISA Premium Report Factory - Button 1 Ranking Runtime Wiring Design Review

Slice: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-review-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only design review

## Design Reference

- Design doc: docs/ai_risa_premium_report_factory_button1_ranking_runtime_wiring_design_v1.md
- Design commit: 18de33a
- Design tag: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-v1
- Review type: docs-only; no runtime changes introduced in this slice

## Scope Confirmation

Reviewed scope:

1. Button 1 only. ✓
2. Design-only slice — no implementation included. ✓
3. Ranking scaffold contracts in `prf_ranking_scaffold.py` are the authoritative source of truth. ✓
4. Additive-only API field design. ✓
5. Advisory-only UI indicator model. ✓
6. Approval-gated save boundary preserved unchanged. ✓

Out-of-scope items confirmed absent:

1. No Button 2 changes. ✓
2. No Button 3 changes. ✓
3. No global database writes. ✓
4. No learning/calibration updates. ✓
5. No automatic queue save or auto-selection logic. ✓
6. No customer PDF generation. ✓
7. No approval-gate bypass. ✓

## Design Review Findings

### Finding 1 — Scaffold Contract Anchor

The design correctly anchors runtime wiring to the existing seven engine contracts in `prf_ranking_scaffold.py`:

- `ranking.fight_readiness`
- `ranking.report_value`
- `ranking.customer_priority`
- `ranking.event_card_priority`
- `ranking.betting_interest`
- `ranking.commercial_sellability`
- `ranking.analysis_confidence`

No duplicate scoring schema is proposed outside the scaffold. The design requirement is satisfiable as written.

Status: CLEAR

### Finding 2 — API Additive-Only Discipline

Ten additive fields are defined for discovery and parse-preview row objects:

1. fight_readiness_score
2. report_value_score
3. customer_priority_score
4. event_card_priority_score
5. betting_interest_score
6. commercial_sellability_score
7. analysis_confidence_score
8. composite_ranking_score
9. ranking_bucket
10. ranking_reasons

Plus three optional diagnostics: `ranking_validation_ok`, `ranking_missing_inputs`, `ranking_contract_version`.

Existing response keys are preserved unchanged. Additive-only discipline is explicit and enforceable. No mutation of existing contract fields is proposed.

Status: CLEAR

### Finding 3 — Determinism

Design specifies:

1. Same input row payload always produces the same output.
2. Scaffold-defined weights are the only composite weighting source.
3. Tie-breaking under sort is deterministic.
4. Fallback for missing inputs produces a safe deterministic low-confidence category.

These requirements are sufficient for implementation to produce verifiable, repeatable test results. No stochastic or learned weighting is introduced.

Status: CLEAR

### Finding 4 — Approval Gate and Save Boundary

The save flow boundary section makes the following constraints explicit:

1. Operator approval is required before save.
2. Ranking does not auto-select rows.
3. Ranking does not auto-save rows.
4. Only operator-selected rows are written through the existing approved-save boundary.

No mechanism is proposed that would allow ranking output to bypass or defer the approval gate. The boundary is unchanged.

Status: CLEAR

### Finding 5 — Fallback Safety

Design specifies that missing ranking inputs:

1. Must not break discovery or preview responses.
2. Produce safe fallback score defaults.
3. Produce explicit `ranking_reasons` entries flagging the missing inputs.
4. Allow rows to remain operator-selectable and reviewable.
5. Fall back to a deterministic low-confidence `ranking_bucket`.

This prevents ranking enrichment failures from propagating to the broader Button 1 discovery and preview surfaces.

Status: CLEAR

### Finding 6 — Cross-Button Anti-Drift

Design is scoped exclusively to Button 1 surfaces: discovery response wiring and parse-preview response wiring. No design element references Button 2 or Button 3 logic paths. Existing Button 2 and Button 3 tests must remain green and are listed explicitly in the validation plan.

Status: CLEAR

### Finding 7 — Validation Plan Adequacy

Validation plan covers five required proof points and recommends five test layers:

Proof points:
1. Discovery response carries additive ranking fields.
2. Parse-preview response carries additive ranking fields.
3. Composite ranking is deterministic.
4. Missing data falls back safely without breaking existing flows.
5. Existing save flow remains approval-gated.

Test layers:
1. Ranking adapter unit tests (per-engine scoring + fallback).
2. Contract tests (score ranges + required keys).
3. Endpoint tests (additive-only response behavior).
4. Cross-button anti-drift tests.
5. Post-freeze smoke with runtime artifact cleanup proof.

Plan is complete and sufficient for implementation-phase acceptance criteria.

Status: CLEAR

## Implementation Guardrails Carried Forward

The following constraints are binding for the implementation slice:

1. Consume existing `prf_ranking_scaffold.py` contracts; do not create a parallel scoring schema.
2. API ranking fields are additive-only on row objects; existing keys are immutable.
3. Ranking output is advisory only; no auto-select and no auto-save.
4. Approval gate is mandatory and unchanged for queue save.
5. Discovery and parse-preview are the only wiring surfaces; no other Button 1 surfaces are in scope.
6. No Button 2 or Button 3 code paths are modified.
7. No writes, no learning/calibration updates, no PDF generation in the implementation slice.
8. Post-freeze smoke and runtime artifact cleanup are required before implementation lock.

## Clarifications for Implementation Slice

The following questions should be resolved at implementation start to prevent ambiguity:

1. **Ranking adapter location**: New file or inline in the discovery/preview handler? Recommendation: new adapter module (`prf_ranking_adapter.py`) for testability and isolation.
2. **Bucket thresholds**: Exact composite score thresholds for each `ranking_bucket` tier must be agreed before implementation and locked in the adapter.
3. **Reason code vocabulary**: Exact `ranking_reasons` string vocabulary must be defined and kept stable across test runs to satisfy determinism requirements.
4. **Missing-input score defaults**: Per-engine safe defaults for missing inputs must be defined explicitly (e.g., `0`, `50`, or engine-specific minimums per scaffold contract).
5. **Optional diagnostic field inclusion policy**: Whether `ranking_validation_ok`, `ranking_missing_inputs`, and `ranking_contract_version` are always present or conditionally included must be decided before endpoint tests are written.

## Verdict

**APPROVED FOR IMPLEMENTATION HANDOFF.**

All seven findings are CLEAR. Design is coherent, additive-only, approval-safe, deterministic, and correctly bounded to Button 1. No blocking concerns identified.

The five clarifications above are advisory; none block approval. They must be resolved at implementation-slice start before code is written.

## Next Safe Slice

ai-risa-premium-report-factory-button1-ranking-runtime-wiring-implementation-v1
