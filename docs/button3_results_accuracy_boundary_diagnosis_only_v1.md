# Button 3 Results/Accuracy Boundary Diagnosis Only v1

Slice: button3-results-accuracy-boundary-diagnosis-only-v1
Date: 2026-06-18
Status: Docs-only boundary diagnosis

## Purpose

Define the current Button 3 boundary as diagnosis-only for results and accuracy preview surfaces, without opening learning execution.

This slice records what is currently allowed, what is blocked, and what must remain gated before any learning/calibration writes can be considered.

## Hard Scope

- docs-only
- no Button 3 runtime code changes
- no Button 1 runtime changes
- no Button 2 runtime changes
- no dashboard/runtime template changes
- no learning execution
- no calibration writes
- no queue/database writes
- no provider/source execution expansion

## Current Button 3 Known Surfaces (Indexed)

### Controlled Preview Route

- Route: `POST /api/button3/result-comparison/preview-v1`
- Contract: preview-only comparison payload
- Mutation flags remain false

Referenced docs:

- `docs/button3_result_comparison_controlled_preview_path_v1.md`
- `docs/button3_result_comparison_controlled_preview_dashboard_runtime_confirmation_v1.md`

### Runtime Confirmation

Previously confirmed runtime evidence indicates:

- route responds HTTP 200
- preview_only style behavior is active
- comparison/accuracy preview fields are returned
- mutation/learning/calibration/queue flags remain false

## Boundary Diagnosis

Button 3 is in a controlled preview state, not an apply state.

### Allowed in This State

- result comparison preview
- accuracy preview computation/display
- operator review surfaces
- diagnosis, docs-only indexing, and governance definition

### Blocked in This State

- learning writes
- calibration writes
- queue/database mutation from Button 3
- automatic apply without explicit governance package
- operator apply endpoint expansion in this slice

## Required Governance Before Any Learning Execution

The following must be locked before learning/calibration writes are allowed:

1. Official result governance package (source trust + conflict handling)
2. Apply-path contract design with fail-closed semantics
3. Operator approval gate contract for apply execution
4. Regression tests for write suppression and authorization failure paths
5. Runtime smoke proof for apply path under gate (if and only if approved)
6. Final handoff and chain index confirming mutation boundaries

## Cross-Track Alignment

This diagnosis aligns with the frozen Button 2 stop-state index:

- Button 2 remains not activated for customer generation
- Button 3 may continue diagnosis-only work
- cross-cutting governance docs are allowed
- no write execution paths are opened by this document

Reference:

- `docs/ai_risa_three_button_factory_button2_stop_state_and_next_track_governance_index_v1.md`

## Explicit Non-Goals

This slice does not:

- implement learning/calibration writes
- add apply endpoints
- change provider execution strategy
- change dashboard controls
- change queue/database behavior
- alter Button 2 or Button 1 behavior

## Next Allowed Step

- Button 3 official result governance design (docs-only)
- then Button 3 apply-path boundary design (docs-only)
- still no learning execution until governance chain is locked

## Conclusion

Button 3 is confirmed as results/accuracy boundary diagnosis only.

Learning execution remains blocked until a dedicated official-result governance and apply-authorization chain is designed, validated, and locked.
