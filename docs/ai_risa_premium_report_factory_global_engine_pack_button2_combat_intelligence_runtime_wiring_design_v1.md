# AI RISA Premium Report Factory - Global Engine Pack Button 2 Combat Intelligence Runtime Wiring Design

Slice: ai-risa-premium-report-factory-global-engine-pack-button2-combat-intelligence-runtime-wiring-design-v1
Date: 2026-05-02
Type: docs-only runtime wiring design

## Baseline

1. Starting HEAD: 735f81e
2. Runtime baseline lineage: 3c09356
3. Validation posture: 16/16 PASS
4. Current state: demo-safe, docs-only HEAD, no active runtime edits

## Goal

Design Button 2 runtime wiring for Combat Intelligence / Fighters Analytics outputs so customer-ready premium PDFs include deeper AI-RISA analysis content, not only readiness and sparse-completion quality gates.

## Scope

In scope:

1. Button 2 only.
2. Design only (no implementation in this slice).
3. Combat Intelligence engine-output attachment design into premium report content assembly.
4. Additive API and UI visibility design for engine contributions and populated/missing combat content.
5. Customer-ready gate interaction with combat content completeness.

Out of scope:

1. No Button 1 changes.
2. No Button 3 changes.
3. No global database writes.
4. No learning/calibration updates.
5. No betting-market runtime wiring.
6. No billing behavior.
7. No automatic customer PDF without operator approval.

## Engines To Wire First

1. Tactical Keys Engine
2. Decision Structure Engine
3. Energy Use / Energy Economy Engine
4. Fatigue Failure Point Engine
5. Mental Condition Engine
6. Collapse Trigger Engine
7. Deception and Unpredictability Engine
8. Dominance / Danger Zone Engine
9. Round-Band Projection Engine
10. Scenario Tree / Method Pathways Engine

## Premium Sections Affected

1. Headline Prediction
2. Executive Summary
3. Matchup Snapshot
4. Decision Structure
5. Energy Use and Gas Tank Projection
6. Fatigue Failure Points
7. Mental Condition
8. Collapse Triggers
9. Deception and Unpredictability
10. Round-by-Round Control Shifts
11. Scenario Tree / Method Pathways
12. Risk Warnings
13. Operator Notes

Note:
The existing content model has section-level structure that can also include operator-visible metadata rows. This slice treats the above list as required combat-intelligence-targeted sections for customer-ready quality decisions.

## 1) Existing Button 2 Content Assembly Flow

Current high-level flow:

1. Operator selects queued matchup records.
2. Generate request requires operator approval.
3. Content bundle is assembled per matchup using linked analysis when available, with draft fallback behavior controlled by allow_draft.
4. Readiness and sparse-completion gates decide customer-ready, draft-only, or blocked outcomes.
5. API returns generated/rejected rows and gate reasons.

Design issue to solve:

Current flow proves quality gating, but combat-intelligence depth is not yet explicitly wired and surfaced as first-class engine contributions by section.

## 2) Combat Attachment Point In Assembly

Attach Combat Intelligence wiring inside per-matchup content assembly after source resolution and before final readiness/candidate customer-ready decision.

Attachment sequence:

1. Resolve source preference (linked analysis record first; generated internal draft second).
2. Build normalized combat engine-output envelope for the 10 engines.
3. Map engine outputs into targeted premium report sections.
4. Record section population status and engine contribution status.
5. Run readiness + sparse checks using assembled section content and prediction fields.
6. Apply customer-ready gate decision with combat-content completeness constraints.

## 3) Engine-To-Section Mapping Plan

Primary mapping:

1. Tactical Keys Engine -> Headline Prediction, Executive Summary, Matchup Snapshot, Operator Notes
2. Decision Structure Engine -> Decision Structure, Scenario Tree / Method Pathways, Risk Warnings
3. Energy Use / Energy Economy Engine -> Energy Use and Gas Tank Projection, Round-by-Round Control Shifts, Risk Warnings
4. Fatigue Failure Point Engine -> Fatigue Failure Points, Round-by-Round Control Shifts, Risk Warnings
5. Mental Condition Engine -> Mental Condition, Collapse Triggers, Risk Warnings
6. Collapse Trigger Engine -> Collapse Triggers, Scenario Tree / Method Pathways, Risk Warnings
7. Deception and Unpredictability Engine -> Deception and Unpredictability, Matchup Snapshot, Risk Warnings
8. Dominance / Danger Zone Engine -> Matchup Snapshot, Round-by-Round Control Shifts, Executive Summary
9. Round-Band Projection Engine -> Round-by-Round Control Shifts, Headline Prediction, Scenario Tree / Method Pathways
10. Scenario Tree / Method Pathways Engine -> Scenario Tree / Method Pathways, Headline Prediction, Executive Summary

Cross-section composition rules:

1. Headline Prediction composes Tactical Keys + Round-Band Projection + Scenario Tree outputs.
2. Executive Summary composes Tactical Keys + Dominance/Danger Zone + Scenario Tree outputs.
3. Risk Warnings composes Decision Structure + Energy + Fatigue + Mental + Collapse + Deception outputs.
4. Operator Notes records source provenance and unresolved gaps.

## 4) Source Preference and Draft Handling

Source order must be deterministic:

1. Linked analysis record content is preferred over generated internal draft content.
2. Internal generated draft content is used only when linked analysis is absent and allow_draft is true.
3. Internal generated draft content must be explicitly labeled as draft-only.

Draft restrictions:

1. Internal draft content cannot be promoted to customer_ready solely by combat section population.
2. If analysis_source_type is generated_internal_draft, final customer_ready remains false and quality status remains draft_only.
3. readiness_gate_reason remains deterministic (internal_draft_requires_operator_review).

## 5) Customer-Ready Gate Rules With Combat Wiring

Customer-ready must be blocked when any of the following is true:

1. Required combat-targeted sections are missing.
2. Required combat-targeted sections contain placeholder/unavailable text.
3. Required prediction/sparse fields are incomplete.
4. Required combat engine outputs are missing for mandatory sections.

Customer-ready may pass only when:

1. Operator approval is true.
2. Required sections are present and populated with non-placeholder content.
3. Required combat engine outputs are present for mandatory section set.
4. Sparse-completion passes.
5. Source is approved for customer-ready path (linked analysis, not internal draft-only fallback).

## 6) Placeholder/Unavailable Blocking Rules

Placeholder and unavailable text remains hard-blocking for customer-ready path.

Blocking examples include markers such as:

1. unavailable
2. prediction unavailable
3. tbd / placeholder
4. engine output missing

Design requirement:

Combat mapping may enrich sections but must not bypass existing placeholder detection and readiness blockers.

## 7) Additive API Fields (Per Matchup Result)

Additive fields to return in generated/rejected rows:

1. combat_engine_contributions
- Object keyed by engine name with contribution state and target sections.

2. populated_sections
- Array of section names successfully populated with non-placeholder content.

3. missing_engine_outputs
- Array of engine names or engine-section requirements missing for customer-ready eligibility.

4. combat_content_status
- Enum-like string: complete, partial, or missing_critical.

5. section_source_map
- Object keyed by section name describing source type and contributing engines.

Contract rule:

These fields are additive only; existing response keys are preserved unchanged.

## 8) UI Visibility Plan (Button 2)

Button 2 generation results UI should add visibility rows/cards for:

1. Which engines contributed content.
2. Which premium sections were populated.
3. Which engines/sections are missing.
4. Combat content status (complete/partial/missing_critical).
5. Section source map per section (linked_analysis vs generated_internal_draft).

UI behavior constraints:

1. Visibility only; no automatic writes.
2. No silent customer-ready promotion.
3. Existing readiness and sparse reasons remain displayed.

## 9) Non-Goals (Explicit)

1. No Button 1 ranking runtime wiring.
2. No Button 3 accuracy/calibration runtime wiring.
3. No betting market runtime wiring.
4. No global DB writes.
5. No learning updates.
6. No billing updates.

## 10) Validation Plan

Validation must prove:

1. Known complete analysis maps into all required combat sections.
2. Missing combat engine output blocks customer_ready.
3. Internal draft remains draft_only.
4. Unavailable placeholders remain blocked.
5. Existing Button 2 readiness/sparse tests remain green.
6. Existing scaffold tests remain green.
7. No Button 1 behavior drift.
8. No Button 3 behavior drift.

Recommended validation layers:

1. Mapping-level tests for engine-to-section contribution contracts.
2. Builder-level tests for combat_content_status and missing_engine_outputs.
3. API-level tests for additive fields and customer-ready block reasons.
4. Post-freeze smoke for live route behavior and runtime artifact cleanup.

## 11) Risks and Guardrails

Primary risks:

1. Over-constraining customer_ready because section mapping is stricter than source availability.
2. Inconsistent section composition when multiple engines contribute to one section.
3. UI confusion if section_source_map is not deterministic.

Guardrails:

1. Deterministic source preference and reason strings.
2. Additive fields only; preserve existing contracts.
3. Keep draft-only override hard and explicit.
4. Keep readiness and sparse gates authoritative.

## Design Verdict

READY FOR DESIGN REVIEW.

This design is Button 2 only and preserves hard safety constraints:

1. No Button 1/3 runtime changes.
2. No write expansion.
3. No learning/calibration drift.
4. No customer-ready output without approval + readiness + sparse + combat completeness + source compliance.
