# Button 2 Customer PDF - Phase 4 Chart/Scenario Rendering Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase4-chart-scenario-rendering-design-v1
- Type: docs-only
- Purpose: define strict, narrow chart/scenario visual-polish boundaries before any implementation

---

## Core Rule

Design first. No implementation in this slice.

- No renderer rewrite
- No delivery workflow changes
- No certification automation
- No approval-gate changes
- No output-path changes
- No file-write behavior changes

---

## Entry Preconditions

Must remain true before any implementation:

1. Phase 1 metadata contracts remain immutable
2. Phase 2 rendering foundations remain intact
3. Phase 3 proof stack remains required and locked
4. Phase 4 typography/layout polish v1 and smoke remain locked
5. Phase 4 page-break/layout polish v1 and smoke remain locked

---

## Scope for Future Implementation

Allowed:
- chart container spacing and caption hierarchy visual tuning via CSS/composition-only adjustments
- scenario table readability tuning (density, row rhythm, header/body spacing)
- chart-to-scenario block flow alignment where contracts are unchanged
- chart/scenario visual consistency pass using existing metadata and layout surfaces only

Not allowed:
- chart data computation changes
- chart generation engine changes
- metadata schema changes
- source/delivery workflow changes
- certification automation
- approval bypass or gate mutation
- output-path rewiring
- file-write behavior changes

---

## Proposed Narrow Sequence

Future implementation should execute one sub-step at a time:

1. Chart block spacing and caption hierarchy pass
2. Scenario table vertical rhythm pass
3. Chart-to-scenario transition spacing pass
4. Long scenario continuity readability pass
5. Cross-page chart/scenario consistency pass

Each sub-step must remain CSS/layout-only and contract-preserving.

---

## Required Proof Gates Before and After Each Sub-Step

Must remain green after every implementation sub-step:

- Phase 1 typography token baseline
- Phase 2 rendering-foundation smoke
- Phase 3 proof-stack integration preview
- Phase 4 typography/layout polish v1 and smoke
- Phase 4 page-break/layout polish v1 and smoke

Additionally required:
- no HTML data contract changes
- no proof-stack contract changes
- no chart rendering controls or interactive dashboard controls introduced
- no delivery/certification controls
- no mutation endpoint references
- all safety flags remain false

---

## Non-Goals

This design does not:
- implement chart/scenario visual changes
- modify metadata schema
- modify proof contracts
- introduce dashboard controls
- alter delivery/certification/approval workflows
- alter output or file-write pathways

---

## Review Verdict

Approved for next narrow implementation slice only if executed as CSS/layout procedural polish over existing chart/scenario rendering surfaces with mandatory proof-gate validation and zero operational behavior change.

---

## Final Statement

Phase 4 chart/scenario rendering work may proceed only as controlled, proof-gated, slice-by-slice visual refinement over locked Phase 1/2/3 and prior Phase 4 slices, with no renderer rewrite and no delivery, certification, approval, output-path, or file-write expansion.
