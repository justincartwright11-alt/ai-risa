# Button 2 Customer PDF - Phase 3 Geometry Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-geometry-proof-design-v1
- Type: docs-only
- Purpose: define geometry proof contract for rendered PDFs before any renderer behavior or delivery changes

---

## Core Rule

Proof before polish.

- No renderer rewrite
- No PDF generation behavior changes
- No delivery expansion
- No certification automation
- No dashboard/approval/output-path/file-write behavior changes

---

## Objective

Define a fail-closed geometry proof module that verifies rendered PDF spatial/layout safety contracts against required regions and boundaries.

---

## Scope

Geometry proof covers spatial evidence only:

- page-level text/object bounding envelopes
- overlap checks for protected regions
- off-page checks for required content regions
- section placement boundary checks

Out of scope for this design slice:

- visual style polish
- rendering engine changes
- delivery behavior
- certification automation behavior

---

## Geometry Evidence Inputs

Required runtime inputs for preview implementation:

- pdf_bytes (bytes)
- required_regions (list of named geometry regions)
- protected_non_overlap_pairs (list of region pairs that must not overlap)
- required_on_page_regions (list of required region names)

Optional future inputs (not required in v1):

- tolerance profile
- page templates
- expected section map per fixture

---

## Safe Geometry Extraction Approach

Preferred extraction approach for preview:

- use a safe PDF parsing layer capable of exposing text/object boxes (library choice finalized in implementation preview)
- run in-memory against pdf_bytes where possible
- no file writes in proof helper

If extraction channel is unavailable or parsing fails, geometry proof must fail closed.

---

## Required Geometry Checks

1. Region Presence Check
   - each required region appears in extracted geometry map

2. Region On-Page Check
   - region coordinates must lie within page boundaries

3. Protected Overlap Check
   - configured protected region pairs must not overlap above tolerance

4. Section Boundary Check
   - required section regions must appear in allowed page ranges/areas for fixed fixtures

5. Geometry Completeness Check
   - geometry map must include minimum required fields per region

---

## Fail-Closed Status Model

Geometry proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- missing_pdf_bytes
- geometry_library_unavailable
- geometry_extraction_error
- missing_required_regions
- off_page_required_regions
- protected_overlap_detected
- invalid_region_geometry_shape

No partial pass in v1.

---

## No-Write and No-Behavior-Change Constraints

The geometry proof helper must:

- not write files
- not generate PDFs
- not modify renderer behavior
- not modify dashboard behavior
- not modify delivery workflow
- not modify certification automation

These constraints must be explicit output flags for every run.

---

## Contract Shape (Preview Target)

run_geometry_proof(pdf_bytes, required_regions, protected_non_overlap_pairs, required_on_page_regions) -> dict

Minimum output fields:

- schema_version
- proof_channel = geometry
- proof_status
- failure_reasons
- extracted_region_count
- missing_required_regions
- off_page_required_regions
- protected_overlap_pairs_detected
- pdf_generation_performed = false
- file_write_performed = false
- renderer_behavior_changed = false
- dashboard_behavior_changed = false
- delivery_workflow_changed = false
- certification_automation_changed = false

---

## Implementation Sequence Link

After design lock:

1. geometry proof preview helper (fail-closed scaffold)
2. geometry smoke tests (success + fail-closed error paths)
3. integration with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design freezes Phase 3 geometry proof boundaries: strict fail-closed spatial verification, in-memory first, and governance-safe with no operational expansion.