# AI-RISA Premium Report Factory - Global Ranking, Betting, Generation, Fighters Analytics Engine Pack: Design v1

Date: 2026-05-02
Slice: ai-risa-premium-report-factory-global-ranking-betting-generation-fighters-analytics-engine-pack-design-v1
Scope: Docs-only design (no implementation)

## Design Goal

Define the next AI-RISA master engine pack so the Premium Report Factory can scale toward long-term v100 architecture while preserving the existing 3-button dashboard workflow and safety boundaries.

This design extends the already sealed Button 2 Real Analysis Content Engine baseline and introduces a structured engine-pack model for:

1. Fighters Analytics / Tszyu vs Nurja style analysis engines
2. Combat intelligence engines
3. Global database / global ledger engines
4. Ranking engines
5. Betting market engines
6. Generation engines

## Core Workflow Rule (Non-Negotiable)

These engines are workflow infrastructure, not standalone dashboard features.
They must remain behind the existing 3-button model:

1. Button 1: discovery, ranking, review, approval, global database/queue save
2. Button 2: real analysis content, betting intelligence, generation, customer-ready export
3. Button 3: result comparison, accuracy ledger, approved learning/calibration

Advanced Dashboard remains internal-only for diagnostics, overrides, debug controls, and v100 research controls.

## Baseline Dependency

This design is an extension layer on top of:

- Button 2 Real Analysis Content Engine implementation and archive lock baseline
- Existing 3-button UX and route contracts

No part of this design may regress current Button 1/2/3 behavior.

## Target Architecture (v100-Compatible)

## 1) Engine Registry and Orchestration Layer

Introduce a registry-driven engine topology:

- engine_id
- engine_group
- engine_version
- input_contract
- output_contract
- blocking_requirements
- quality_gates
- approval_gate_required
- audit_event_type

Execution model:

1. Build workflow context from approved records
2. Resolve required engines per button action and output target
3. Execute engines in deterministic dependency order
4. Collect normalized engine outputs
5. Enforce blocking/quality/approval gates
6. Allow promotion only if all required gates pass

## 2) Standard Engine Output Envelope

Every engine should produce a normalized envelope:

- engine_id
- engine_version
- status: complete | partial | blocked | failed
- confidence
- contributed_fields
- missing_required_fields
- provenance_refs
- debug_metrics
- generated_at

This enables:

- cross-engine explainability
- per-section provenance visibility
- customer-ready gate decisions
- consistent diagnostics in Advanced Dashboard

## 3) Button-Aligned Execution Placement

Button 1 placement:

- discovery engines
- ranking engines
- source provenance engine
- duplicate/conflict resolution engine
- global database write path only after operator approval

Button 2 placement:

- fighters analytics engines
- combat intelligence engines
- betting market engines
- generation engines
- customer-ready QA and export proof

Button 3 placement:

- result ledger updates
- accuracy ledger updates
- calibration ledger updates
- segment accuracy engines
- approved-only learning/calibration updates

## Engine Group Definitions

## A) Fighters Analytics / Tszyu vs Nurja Engines

Required engines:

- Tactical Keys Engine
- Dominance / Danger Zone Engine
- Pace / Pressure / Fatigue / Range Engine
- Early / Mid / Late Fight Projection Engine
- Stoppage Trigger Engine
- Scorecard Scenario Engine
- Win / Method Probability Engine
- Decision Structure Engine
- Energy Use Engine
- Fatigue Failure Point Engine
- Mental Condition Engine
- Collapse Trigger Engine
- Pressure Management Engine
- Energy Waste Engine
- Composure Under Stress Engine
- Predictability Under Stress Engine
- Late-Fight Decision Engine
- Sparse-Case Result Completion Engine

Button 2 mapping requirement:

These engines must feed all 14 premium report sections through deterministic section mapping. No required section may remain unavailable for customer-ready promotion.

Sparse-case completion requirement:

Before any final promotion path, sparse-case completion must fill:

- winner
- confidence
- method
- round
- debug metrics

## B) Global Database / Ledger Engines

Required engines:

- Global Fighter Database Engine
- Global Matchup Database Engine
- Global Event Card Database Engine
- Global Result Ledger Engine
- Global Report Ledger Engine
- Global Accuracy Ledger Engine
- Global Calibration Ledger Engine
- Duplicate / Conflict Resolution Engine
- Source Provenance Engine

Write safety model:

- all global writes are approval-gated
- auditable operation records required
- deterministic upsert rules required
- conflict resolution must record rationale and source lineage

## C) Ranking Engines

Required engines:

- Fight Readiness Ranking Engine
- Report Value Ranking Engine
- Customer Priority Ranking Engine
- Event Card Priority Ranking Engine
- Betting Interest Ranking Engine
- Commercial Sellability Ranking Engine
- Analysis Confidence Ranking Engine

Placement rule:

Ranking outputs are primary in Button 1 pre-save review and may be reused by Button 2 generation prioritization logic.

## D) Betting Market Engines

Required engines:

- Odds Ingestion Engine
- Implied Probability Engine
- Fair Price Engine
- Market Edge Engine
- Prop Market Engine
- Volatility Grade Engine
- Round-Band Betting Path Engine
- Pass / No-Bet Condition Engine
- Market Movement Watch Engine
- Betting Risk Disclaimer Engine

Governance rule:

Any betting-oriented output must include:

- risk disclaimer
- pass/no-bet conditions

If disclaimer/conditions are missing, customer-ready betting outputs are blocked.

## E) Generation Engines

Required engines:

- Premium PDF Generation Engine
- Event-Card Report Pack Generator
- Single-Matchup Report Generator
- Fighter Profile Generator
- Betting Analyst Brief Generator
- Broadcast Analyst Pack Generator
- Coach / Gym Scouting Report Generator
- Promoter / Manager Decision Brief Generator
- Visual Generation Engine
- Radar Metric Engine
- Round Heat Map Engine
- Control-Shift Graph Engine
- Method Probability Chart Engine
- Customer-Ready QA Engine
- Draft Watermark Engine
- Download / Export Proof Engine

Promotion rule:

- Customer-ready QA must pass all required content and safety checks
- Draft watermark must be applied to internal-only outputs
- Export proof must record deterministic artifact metadata

## F) Combat Intelligence Engines

Required engines:

- Fighter Architecture Engine
- Decision Structure Engine
- Energy Economy Engine
- Fatigue Failure Point Engine
- Mental Condition Engine
- Collapse Trigger Engine
- Deception and Unpredictability Engine
- Range Geography Engine
- Dominance Zone / Danger Zone Engine
- Tactical Keys Engine
- Round-Band Projection Engine
- Stoppage Sensitivity Engine
- Sparse-Case Result Completion Engine
- Confidence Quality Engine
- Volatility / Upset Lane Engine
- Scorecard Scenario Engine
- Method Probability Engine
- Pattern Memory Engine
- Fighter Embedding Similarity Engine
- Report Readiness Engine
- Visual Intelligence Engine
- Audience-Specific Output Engine
- Live Adaptation / Momentum Engine
- Accuracy Segment Engine
- Calibration Recommendation Engine

Placement note:

Combat intelligence outputs bridge Button 2 (content/generation) and Button 3 (accuracy/calibration diagnostics) through shared normalized envelopes.

## Governance and Safety Controls

Hard rules:

1. No uncontrolled writes.
2. No automatic customer PDF without operator approval.
3. No automatic learning/calibration updates without operator approval.
4. Global database writes require auditable operator approval.
5. Betting outputs must include risk disclaimer and pass/no-bet conditions.
6. Customer-ready reports cannot include unavailable placeholder sections.
7. Sparse-case completion must fill winner/confidence/method/round/debug metrics before final promotion.
8. Draft reports must remain clearly labeled as draft/internal only.
9. Existing Button 1/2/3 behavior must not be broken.

## Customer-Ready Promotion Contract

A report may be promoted to customer_ready only when all are true:

- operator approval present
- required engine outputs complete
- no unavailable placeholder sections in required report sections
- missing_required_fields is empty for required engines
- betting disclaimer and pass/no-bet condition included where betting outputs exist
- sparse-case completion gate satisfied where sparse data path is invoked

Otherwise:

- blocked_missing_analysis or blocked_missing_required_engine_output state is returned
- output can remain draft_only only if draft mode is explicitly enabled

## Dashboard and UX Placement

Button 1 UI should display:

- ranking stack outputs
- source provenance/conflict indicators
- approval state required before save

Button 2 UI should display:

- analysis source visibility
- engine contribution preview per report candidate
- blocking reasons for missing required engine outputs
- output mode distinctions: customer_ready | draft_only | blocked

Button 3 UI should display:

- result vs report comparisons
- accuracy segment summaries
- approval-gated calibration recommendations

Advanced Dashboard should display:

- engine diagnostics
- quality gates and block reasons
- override requests (approval gated)
- v100 research controls and debug traces

## Validation Plan

The design is accepted when the following are true in later implementation/testing slices:

1. Button 1 can rank discovered fights before save.
2. Button 1 can save approved fights to database/queue.
3. Button 2 can map Fighters Analytics engines into all 14 premium report sections.
4. Button 2 can generate customer-ready reports with no unavailable placeholder sections.
5. Button 2 can generate betting analyst brief outputs with fair price, market edge, volatility, and pass/no-bet conditions.
6. Button 2 can generate audience-specific outputs.
7. Sparse-case completion fills winner, confidence, method, round, and debug metrics.
8. Report preview shows which engines contributed content.
9. Missing required engine output blocks customer_ready status.
10. Button 3 can compare real results against reports and update accuracy ledgers.
11. Learning/calibration remains approval-gated.
12. Existing Button 1/2/3 tests remain green.

## Out of Scope for This Slice

- No backend code changes
- No frontend/template changes
- No route additions
- No test modifications
- No data migration
- No engine implementation

This slice is design-only and defines architecture, contracts, placement, and governance for subsequent design-review and implementation slices.