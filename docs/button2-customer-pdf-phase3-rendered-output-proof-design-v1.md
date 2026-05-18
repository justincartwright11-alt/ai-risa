# Button 2 Customer PDF - Phase 3 Rendered Output Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-rendered-output-proof-design-v1
- Type: docs-only
- Purpose: define proof methods before any visual polish, delivery expansion, or certification automation changes

---

## Core Rule

Proof before polish.

No customer delivery expansion.
No certification automation.
No dashboard changes.
No approval-gate changes.

---

## Context Baseline (Frozen Inputs)

Phase 3 must prove rendered output against the already-frozen baseline:

- Phase 1 metadata stack (all layer contracts)
- Phase 2 render-facing foundation slices 1-8
- Current frozen proof baseline: 605 total tests (381 Phase 2 + 224 Phase 1)

Phase 3 does not alter this baseline. It proves that actual rendered PDFs faithfully realize it.

---

## Phase 3 Objective

Establish deterministic, repeatable, evidence-grade rendered PDF proof that actual output matches:

1. metadata intent
2. structural layout requirements
3. typography constraints
4. header/footer/watermark constraints
5. source traceability visibility
6. visual QA rollup visibility

This phase is proof instrumentation and proof criteria design first, then implementation in controlled slices.

---

## Non-Goals (Explicit)

The following are out of scope for this design and all initial Phase 3 proof slices:

- redesigning customer-facing visual style
- adding delivery behavior
- changing approval gate behavior
- changing output path behavior
- changing file write policy
- dashboard UX expansion
- certification automation

---

## Proof Architecture

Rendered output proof should be produced through four complementary evidence channels:

1. PDF text extraction evidence
2. PDF geometry/layout evidence
3. PDF structural/page evidence
4. pixel/visual snapshot evidence (bounded, deterministic)

Each channel must have pass/fail criteria and emit machine-readable artifacts for audit.

---

## Required Proof Domains

### 1. Rendered PDF Proof Method

Define a deterministic render harness that:

- renders from fixed input contexts
- pins renderer/runtime versions
- records artifact hash fingerprints
- stores evidence per run in predictable paths

Evidence outputs:

- rendered PDF file
- metadata manifest (hashes, runtime, commit, tag)
- proof summary JSON

### 2. Text Extraction Proof

Extract text from PDF and prove critical text presence/ordering:

- report title and identity blocks
- section headings in canonical order
- source citation labels and IDs
- QA footer rows

Rules:

- fail if required text tokens missing
- fail if canonical section order breaks beyond tolerated extraction noise

### 3. Geometry Proof

Verify positional/layout contracts using extracted bounding boxes where possible:

- no off-page text for required regions
- no overlap for protected regions
- page-block role placement boundaries respected
- section block break policies reflected in page boundaries

Rules:

- fail on protected overlap/off-page violations
- fail on forbidden geometry violations in required sections

### 4. Page Count and Section Presence Proof

Verify document-level composition:

- expected minimum/maximum page count envelope
- all required sections present
- required metadata sections included in render pipeline evidence

Rules:

- fail if required section absent
- fail if page count out of agreed envelope for fixed fixtures

### 5. Typography/Style Proof

Verify key typography constraints in rendered output:

- heading/body visual hierarchy observable
- font-size and line-height class intent preserved within tolerated render deltas
- contrast/readability checks for required text classes

Rules:

- fail if hierarchy cannot be visually distinguished in required checkpoints
- fail if required typography constraints fall outside tolerance bands

### 6. Header/Footer/Watermark Proof

Verify rendered visibility and placement of:

- header identity/status/confidentiality fields
- footer page-number format and operator/timestamp fields
- watermark visibility/type/opacity constraints

Rules:

- fail if required fields missing in rendered output
- fail if watermark rules violate lock constraints

### 7. Source Traceability Proof

Verify rendered source evidence:

- source list presence and readability
- source labels/types represented
- citation/source linkage cues present

Rules:

- fail if source traceability section not render-visible
- fail if required citation/source identifiers are missing

### 8. Visual QA Rollup Proof

Verify rendered QA summary cues align with rollup metadata:

- rollup status label
- completeness indicator
- confidence label
- readiness indicator

Rules:

- fail if rendered QA summary contradicts metadata evidence for same run

### 9. Fail-Closed Rules

Phase 3 proof layer must be fail-closed:

- if any mandatory proof channel errors, proof status = failed
- if proof artifact generation is partial/corrupt, proof status = failed
- if contradiction between channels is detected, proof status = failed

No auto-override to pass.

### 10. Future Implementation Sequence

Recommended implementation order after this design lock:

1. Phase 3 Slice A: deterministic render harness + artifact manifest
2. Phase 3 Slice B: text extraction proof
3. Phase 3 Slice C: geometry proof (overlap/off-page/placement)
4. Phase 3 Slice D: page count + section presence proof
5. Phase 3 Slice E: typography/style proof
6. Phase 3 Slice F: header/footer/watermark proof
7. Phase 3 Slice G: source traceability proof
8. Phase 3 Slice H: visual QA rollup proof
9. Phase 3 Slice I: integration smoke of all proof channels
10. Phase 3 Slice J: final handoff freeze for rendered-output proof stack

---

## Artifact Contract (Per Proof Run)

Each proof run must produce:

- run_manifest.json
- rendered_output.pdf
- extracted_text.json
- geometry_map.json
- section_presence.json
- typography_proof.json
- hfw_proof.json
- source_traceability_proof.json
- visual_qa_rollup_proof.json
- final_proof_summary.json

All artifacts must include:

- commit/tag reference
- fixture identifier
- UTC timestamp
- pass/fail status
- explicit failure reasons when failed

---

## Gating Policy for Post-Phase-3 Changes

No renderer behavior or visual-polish change may proceed until:

1. all mandatory proof channels are implemented
2. integration smoke passes for locked fixtures
3. final Phase 3 proof handoff is frozen

---

## Final Statement

This design freezes the Phase 3 strategy: prove rendered output correctness first, then consider visual polish or operational expansion in later governed slices.