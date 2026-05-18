# Button 2 Customer PDF - Phase 4 Header/Footer/Watermark Rendering Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase4-header-footer-watermark-rendering-design-v1
- Type: docs-only
- Purpose: define strict, narrow header/footer/watermark visual-polish boundaries before implementation

---

## Core Rule

Design first. No implementation in this slice.

- No renderer rewrite
- No delivery workflow changes
- No certification automation
- No approval-gate changes
- No output-path changes
- No file-write behavior changes
- No dashboard behavior changes

---

## Entry Preconditions

Must remain true before any implementation:

1. Phase 1 metadata contracts remain immutable
2. Phase 2 rendering foundations remain intact
3. Phase 3 proof stack remains required and locked
4. Phase 4 typography/layout polish v1 and smoke remain locked
5. Phase 4 page-break/layout polish v1 and smoke remain locked
6. Phase 4 chart/scenario rendering v1 and smoke remain locked

---

## Scope for Future Implementation

Allowed:
- header spacing and hierarchy readability tuning via CSS/composition-only rules
- footer metadata legibility and line rhythm tuning
- watermark opacity/placement visual consistency tuning using existing metadata surfaces
- cross-page header/footer/watermark visual consistency refinement

Not allowed:
- metadata schema changes
- header/footer/watermark validation logic changes
- source/delivery workflow changes
- certification automation
- approval bypass or gate mutation
- output-path rewiring
- file-write behavior changes
- dashboard behavior changes

---

## Proposed Narrow Sequence

Future implementation should execute one sub-step at a time:

1. Header spacing and hierarchy alignment pass
2. Footer metadata readability/rhythm pass
3. Watermark opacity/placement consistency pass
4. First/continuation page visual continuity pass
5. Cross-page consistency verification pass

Each sub-step must remain CSS/layout-only and contract-preserving.

---

## Required Proof Gates Before and After Each Sub-Step

Must remain green after every implementation sub-step:

- Phase 1 typography token baseline
- Phase 2 rendering-foundation smoke
- Phase 3 proof-stack integration preview
- Phase 4 typography/layout polish v1 and smoke
- Phase 4 page-break/layout polish v1 and smoke
- Phase 4 chart/scenario rendering v1 and smoke

Additionally required:
- no HTML data contract changes
- no proof-stack contract changes
- no delivery/certification controls
- no mutation endpoint references
- no approval/output/file-write/dashboard behavior changes
- all safety flags remain false

---

## Non-Goals

This design does not:
- implement header/footer/watermark visual changes
- modify metadata schema
- modify proof contracts
- alter delivery/certification/approval workflows
- alter output or file-write pathways
- alter dashboard behavior

---

## Review Verdict

Approved for next narrow implementation slice only if executed as CSS/layout procedural polish over existing header/footer/watermark rendering surfaces, with mandatory proof-gate validation and zero operational behavior change.

---

## Final Statement

Phase 4 header/footer/watermark rendering work may proceed only as controlled, proof-gated, slice-by-slice visual refinement over locked Phase 1/2/3 and prior Phase 4 slices, with no renderer rewrite and no delivery, certification, approval, output-path, file-write, or dashboard behavior expansion.
