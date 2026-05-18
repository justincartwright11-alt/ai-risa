# Button 2 Customer PDF - Phase 4 Renderer Polish Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase4-renderer-polish-design-v1
- Type: docs-only
- Purpose: lock the first renderer/PDF visual-polish phase design after Phase 1/2/3 freeze

---

## Core Rule

Design first. No renderer change yet.

- No renderer code changes in this slice
- No delivery expansion
- No certification automation
- No approval-gate changes

---

## Preconditions (Locked Foundations)

Phase 4 design starts only because prior phases are frozen:

1. Phase 1 metadata foundation is locked
2. Phase 2 rendering-foundation contracts are locked
3. Phase 3 rendered-output proof system is locked

Phase 4 design must preserve all prior governance constraints and proof contracts.

---

## 1) Locked Phase 1 Metadata Foundation

Phase 4 depends on stable metadata contracts already locked in earlier handoffs.

Design assumption:
- Renderer polish consumes metadata structures as-is
- No schema expansion in this design slice
- No metadata write-path changes

Impact on Phase 4:
- Typography and section polish can only use existing metadata fields
- New visual details must be mapped from already-locked metadata surfaces

---

## 2) Locked Phase 2 Rendering-Foundation Proof

Phase 2 provides stable rendering primitives and foundation behavior.

Design assumption:
- Existing render-facing foundations remain intact
- Phase 4 only layers polish behavior over validated foundations
- Foundation contracts remain backward compatible

Impact on Phase 4:
- No rewrite of composition engine
- No rewrite of base layout sequencing
- No route/gate changes for report generation pathways

---

## 3) Locked Phase 3 Rendered-Output Proof System

Phase 3 proof stack is complete and frozen across:
- text extraction
- geometry
- page/section
- typography/style
- header/footer/watermark
- source traceability
- visual QA rollup
- proof-stack orchestrator
- dashboard proof display

Impact on Phase 4:
- All visual-polish implementation slices must pass existing proof channels
- Any polish change that causes detected/unavailable proof outcomes is blocked
- Proof display remains read-only and unchanged

---

## 4) Renderer Polish Boundaries

Allowed in future Phase 4 implementation slices:
- visual tuning of typography
- spacing and layout refinement
- page-break refinement
- section-block visual consistency
- chart/scenario visual clarity tuning
- header/footer/watermark visual polish
- source traceability visual clarity polish

Disallowed in Phase 4:
- business logic rewrites
- queue/gate behavior changes
- delivery behavior changes
- certification automation
- approval model changes
- proof-gate bypasses

---

## 5) Typography/Layout Application Sequence

Future implementation sequence should apply typography/layout polish in this order:

1. Global type scale normalization
2. Heading/body hierarchy spacing
3. Intra-section paragraph rhythm and list spacing
4. Summary card typography consistency
5. Cross-page typography consistency checks

Gate after each sub-step:
- typography/style proof remains clear or acceptable per gate definition
- geometry/page-section proofs remain stable

---

## 6) Page-Break and Section-Block Rendering Sequence

Future implementation sequence:

1. Section boundary padding normalization
2. Controlled page-break thresholds per section type
3. Keep-with-next behavior for critical headings
4. Orphan/widow mitigation for key content blocks
5. Section opening visual rhythm consistency

Gate after each sub-step:
- page-section proof remains clear
- geometry proof remains clear
- text extraction proof remains stable (no placeholder regressions)

---

## 7) Chart/Scenario Rendering Sequence

Future implementation sequence:

1. Chart spacing and caption hierarchy alignment
2. Scenario table density tuning (legibility first)
3. Legend/annotation clarity pass
4. Cross-page chart continuity handling
5. Chart-to-narrative transition polish

Gate after each sub-step:
- visual QA rollup remains clear
- geometry proof remains clear (no overlap/off-page)
- typography/style proof remains clear

---

## 8) Header/Footer/Watermark Rendering Sequence

Future implementation sequence:

1. Header spacing and hierarchy alignment
2. Footer metadata legibility and consistency
3. Watermark opacity/placement refinement
4. Cross-page consistency pass
5. First/last page special-case polish (if already supported)

Gate after each sub-step:
- header/footer/watermark proof remains clear
- geometry proof remains clear
- page-section proof unchanged

---

## 9) Source Traceability Rendering Sequence

Future implementation sequence:

1. Citation marker visual readability pass
2. Source class label legibility/contrast tuning
3. Source footer placement clarity
4. Source confidence/label typography harmonization
5. Cross-section source style consistency pass

Gate after each sub-step:
- source traceability proof remains clear
- typography/style proof remains clear
- visual QA rollup remains clear

---

## 10) Required Proof Gates Before Visual Certification

Before any future visual certification proposal, all required gates must pass:

1. text extraction proof clear
2. geometry proof clear
3. page/section proof clear
4. typography/style proof clear
5. header/footer/watermark proof clear
6. source traceability proof clear
7. visual QA rollup proof clear
8. proof-stack signal clear

Additionally required:
- no unavailable channels
- no detected unresolved reasons
- all hard safety flags remain false

Certification remains operator-gated and non-automated.

---

## 11) Non-Goals

This design does not:
- implement renderer changes
- implement new UI controls
- implement delivery pipeline changes
- modify approval gates
- modify certification policy
- alter proof orchestration contracts
- introduce mutation routes

---

## 12) Final Verdict

Phase 4 renderer-polish work is approved to start only through design-led, gated implementation slices that preserve all locked Phase 1/2/3 contracts.

This v1 design is locked as the entry contract for true renderer/PDF visual polish, with strict boundaries:
- no renderer change in this slice
- no delivery expansion
- no certification automation
- no approval-gate changes

All future Phase 4 implementation slices must pass frozen Phase 3 proof gates before any visual certification recommendation.
