# AI-RISA Premium Report Factory - Global Ranking, Betting, Generation, Fighters Analytics Engine Pack Implementation Design v1

Status: Planning artifact (docs-only)
Slice: ai-risa-premium-report-factory-global-ranking-betting-generation-fighters-analytics-engine-pack-implementation-design-v1
Date: 2026-05-02
Mode: Implementation design only (no code changes)

## 1. Implementation Design Scope

Define a phased implementation design for the master engine pack introduced in design v1 and approved in design-review v1, while preserving the 3-button dashboard operating model.

This slice is implementation planning only. No backend/frontend/tests/data migration work is executed here.

## 2. Source Artifacts Reviewed

Reviewed design baselines:
- docs/ai_risa_premium_report_factory_global_ranking_betting_generation_fighters_analytics_engine_pack_design_v1.md
- docs/ai_risa_premium_report_factory_global_ranking_betting_generation_fighters_analytics_engine_pack_design_review_v1.md

Dependency baseline:
- Button 2 real analysis content engine archive lock chain (sealed)

## 3. Locked Implementation Boundary

This implementation design is constrained by the non-negotiable workflow model:

1. Button 1: discovery, ranking, provenance/conflict review, operator approval, queue/global save
2. Button 2: analytics + combat intelligence + betting intelligence + generation + export
3. Button 3: result comparison, accuracy ledgers, approval-gated learning/calibration

Advanced Dashboard remains internal-only for diagnostics, debug tooling, and v100 research controls.

## 4. Engine-Pack Implementation Phases (Planned)

## Phase 0 - Shared Contracts and Registry Foundation

Deliverables:
- engine registry schema definition
- standard engine output envelope contract
- engine dependency graph rules
- hard-block vs warning policy matrix
- audit-event schema for approval-gated writes

Gate to proceed:
- contract documentation approved
- deterministic dependency resolution documented

## Phase 1 - Button 1 Discovery/Ranking/Approval Integration

Engine families staged:
- ranking engines
- source provenance engine
- duplicate/conflict resolution engine
- global database staging adapters (approval-gated only)

Button 1 outcomes required:
- discovered fights can be ranked before save
- operator-approved rows can be saved with audit record
- no uncontrolled writes

Gate to proceed:
- save path remains explicit operator action
- existing Button 1 behavior remains backward compatible

## Phase 2 - Button 2 Fighters Analytics + Combat Intelligence Core

Engine families staged:
- fighters analytics engines
- combat intelligence engines
- sparse-case result completion engine

Button 2 outcomes required:
- deterministic mapping into all 14 premium sections
- no unavailable placeholders for customer-ready candidate path
- explicit engine-contribution visibility in preview payload

Gate to proceed:
- missing required engine output blocks customer_ready
- sparse-case completion includes winner/confidence/method/round/debug metrics

## Phase 3 - Button 2 Betting Intelligence Layer

Engine families staged:
- odds ingestion
- implied probability/fair price/market edge
- volatility/path/watch engines
- pass/no-bet and risk disclaimer engines

Button 2 betting outcomes required:
- betting analyst brief generation support
- fair price + edge + volatility outputs available
- pass/no-bet condition required for betting outputs

Gate to proceed:
- betting outputs blocked from customer_ready if disclaimer or pass/no-bet is missing

## Phase 4 - Button 2 Generation and Visual Pack Layer

Engine families staged:
- report generators (single matchup, event pack, audience-specific variants)
- visual engines (radar, heat map, control-shift, method chart)
- customer-ready QA engine
- draft watermark engine
- download/export proof engine

Button 2 generation outcomes required:
- audience-specific output variants generated deterministically
- draft_only vs customer_ready promotion states enforced
- export proof metadata captured

Gate to proceed:
- automatic customer PDF remains operator-approval gated
- draft watermark required for internal-only outputs

## Phase 5 - Button 3 Ledger/Accuracy/Calibration Integration

Engine families staged:
- result ledger and report ledger update adapters
- accuracy and segment accuracy engines
- calibration recommendation engines
- calibration ledger adapters (approval-gated)

Button 3 outcomes required:
- report-vs-result comparison retained
- ledger updates are deterministic and auditable
- calibration writes remain approval-gated

Gate to proceed:
- no automatic learning/calibration writes
- existing Button 3 contracts remain intact

## Phase 6 - Advanced Dashboard Diagnostics and v100 Controls

Deliverables:
- engine-level diagnostics panel contracts
- block-reason drilldowns
- provenance trace viewers
- internal override request workflow (approval-gated)

Gate to proceed:
- no customer-surface behavior drift
- diagnostics exposure stays internal-only

## 5. Canonical Engine Contracts (Planned)

Each engine will publish:
- engine_id
- engine_group
- engine_version
- required_inputs
- optional_inputs
- output_schema_version
- blocking_fields
- contributed_fields
- provenance_refs
- debug_metrics
- quality_status: complete | partial | blocked | failed

Cross-engine aggregation contract will provide:
- required_engine_status_map
- missing_required_engine_outputs
- customer_ready_block_reasons
- draft_only_reasons
- engine_contribution_preview_rows

## 6. Customer-Ready Promotion Contract (Planned)

Promotion to customer_ready requires all:
- operator approval present
- required engines complete for target output type
- no unavailable placeholders in required sections
- missing_required_engine_outputs empty
- betting disclaimer + pass/no-bet present when betting content exists
- sparse-case completion requirements satisfied when sparse path is used

Fallback behavior:
- blocked_missing_required_engine_output for failed required paths
- blocked_missing_analysis where analysis linkage is absent
- draft_only allowed only when explicitly enabled

## 7. Write Governance and Audit Model

Mandatory controls:
- no uncontrolled writes
- all global database writes approval-gated
- all ledger writes auditable with operation metadata
- no auto-learning or auto-calibration writes
- deterministic upsert and conflict policy required

Audit fields planned:
- operation_id
- operator_id or approval marker
- action_type
- target_store
- before_hash/after_hash (where applicable)
- source_provenance_refs
- timestamp

## 8. Backward Compatibility Strategy

Compatibility commitments:
- no break to existing Button 1/2/3 entry points
- additive contracts first; avoid destructive schema replacement
- phased opt-in flags for new engine groups
- preserve current sealed Button 2 content-engine behavior during rollout

## 9. Implementation Touchpoint Plan (Future Code Slices)

Planned code domains for later implementation slices only:
- engine registry module
- engine orchestration service
- per-button aggregation adapters
- queue/database/ledger adapters
- generation/export adapters
- diagnostics adapters
- backend route payload extension points
- frontend preview render extensions
- focused contract and regression tests

No touchpoint changes are made in this slice.

## 10. Validation and Test Gate Plan

Required acceptance gates for later slices:

1. Button 1 ranks discovered fights before save.
2. Button 1 saves only approved rows to queue/database with audit trail.
3. Button 2 maps fighters analytics + combat intelligence into all 14 sections.
4. Button 2 customer_ready output has no unavailable placeholder sections.
5. Button 2 betting brief includes fair price, edge, volatility, and pass/no-bet.
6. Button 2 can generate audience-specific outputs.
7. Sparse-case completion provides winner/confidence/method/round/debug metrics.
8. Preview identifies contributing engines and block reasons.
9. Missing required engine output blocks customer_ready promotion.
10. Button 3 compares results vs reports and updates accuracy ledgers.
11. Learning/calibration updates remain approval-gated.
12. Existing Button 1/2/3 tests stay green throughout phased rollout.

## 11. Non-Goals (This Slice)

- No implementation code
- No test edits
- No route changes
- No template/dashboard UI changes
- No queue/database/ledger mutation logic changes
- No betting model activation
- No generation pipeline activation

## 12. Implementation Design Verdict

APPROVED AS PLANNING ARTIFACT.

The engine-pack scope is large and requires phased execution. This implementation-design slice provides the required architecture, dependency sequencing, governance gates, and validation checkpoints to proceed safely into later implementation slices without violating the 3-button workflow model.