# AI RISA Premium Report Factory - Global Engine Pack Button 2 Combat Intelligence Runtime Wiring Design Review

Slice: ai-risa-premium-report-factory-global-engine-pack-button2-combat-intelligence-runtime-wiring-design-review-v1
Date: 2026-05-02
Type: docs-only design review
Design under review: 5019f74
Design tag under review: ai-risa-premium-report-factory-global-engine-pack-button2-combat-intelligence-runtime-wiring-design-v1

## Review Verdict

APPROVED for implementation design handoff.

The design is sufficiently scoped, safety-preserving, and consistent with the archived baseline constraints and the existing Button 2 readiness/sparse gate architecture.

## Review Coverage

Reviewed areas:

1. Existing Button 2 content assembly flow and combat attachment points.
2. 10-engine wiring plan and engine-to-section mapping for premium report composition.
3. Source-priority design (linked-analysis-first, internal draft second).
4. Customer-ready gate interaction with combat completeness, readiness, and sparse completion.
5. Placeholder and unavailable-text blocking rules.
6. Additive API contract fields and backward compatibility posture.
7. Operator UI visibility for contributed engines, populated sections, and missing outputs.
8. Non-goals and isolation constraints (Button 1/3 unchanged).
9. Validation strategy and anti-drift coverage.

## Findings

### 1) Scope correctness: PASS

The design is Button 2 only and explicitly excludes Button 1/3 changes, betting runtime wiring, global DB writes, learning/calibration updates, and billing behavior.

### 2) Mapping completeness posture: PASS

The design provides first-pass deterministic mapping from 10 combat engines into targeted premium sections, including cross-section composition responsibilities.

### 3) Runtime safety posture: PASS

Customer-ready path remains constrained by approval + readiness + sparse completion + combat completeness + source compliance. Internal draft remains non-customer-ready.

### 4) API compatibility posture: PASS

New response fields are additive only:

1. combat_engine_contributions
2. populated_sections
3. missing_engine_outputs
4. combat_content_status
5. section_source_map

No existing keys are removed or renamed.

### 5) Operator explainability posture: PASS

The design exposes sufficient diagnostics for runtime decisions by showing contributing engines, populated sections, missing outputs, content status, and section-source provenance.

### 6) Validation adequacy: PASS

Validation plan covers complete-analysis pass path, missing-combat-output blocking, draft-only safety, placeholder blocking, existing readiness/sparse test preservation, scaffold regression, and cross-button drift checks.

## Required Implementation Guardrails (Carry Forward)

1. Keep all response changes additive; do not rename/remove existing Button 2 keys.
2. Preserve operator approval gate behavior exactly.
3. Preserve draft-only override behavior for generated_internal_draft source.
4. Keep placeholder/unavailable detection as hard-blocking for customer-ready.
5. Emit deterministic reason fields for blocked and draft-only outcomes.
6. Preserve Button 1 and Button 3 runtime behavior with no side effects.
7. Keep betting-market wiring out of this chain.
8. Do not introduce global DB writes, learning, calibration, or billing changes.

## Clarifications for Implementation Slice

1. Define mandatory combat section set for customer_ready in one central contract object.
2. Normalize engine keys and section names before writing section_source_map.
3. Ensure missing_engine_outputs differentiates engine-level absence vs section-level unmet requirement.
4. Keep combat_content_status deterministic:
- complete when mandatory combat requirements are satisfied.
- partial when non-mandatory enrichment is missing.
- missing_critical when customer-ready mandatory requirements are missing.
5. Ensure section_source_map always indicates linked_analysis vs generated_internal_draft source per populated section.

## Design-Review Conclusion

The design in 5019f74 is accepted as implementation-ready with mandatory guardrails above.

This review slice performs no implementation work.

## Next Safe Slice

ai-risa-premium-report-factory-global-engine-pack-button2-combat-intelligence-runtime-wiring-implementation-v1
