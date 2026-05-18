# Button 2 Customer PDF - Phase 3 Text Extraction Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-text-extraction-proof-design-v1
- Type: docs-only
- Purpose: define text extraction proof contract before implementation changes to delivery/certification behavior

---

## Core Rule

Design first.

- No PDF generation behavior changes
- No renderer rewrite
- No delivery expansion
- No certification automation

---

## Objective

Define a fail-closed text extraction proof module that validates rendered Button 2 PDF text against required marker contracts, without changing renderer behavior or operational workflows.

---

## Design Focus (Locked)

### 1. Source of PDF Bytes

The proof module accepts PDF bytes from caller-owned runtime context.

- Input contract: pdf_bytes (bytes)
- The module does not render PDFs itself
- The module does not read from disk by default
- Optional external file-loading wrappers are out of scope for v1

### 2. Safe Extraction Library Choice

Primary library choice for preview implementation:

- pypdf (in-memory extraction via BytesIO)

Rationale:

- mature, pure Python, common in controlled environments
- supports extraction from bytes without mandatory file writes
- straightforward exception handling for fail-closed behavior

If unavailable, module must fail closed and report deterministic reason.

### 3. Required Text Markers

Proof requires extraction to include key text markers:

- AI-RISA Premium Fight Report
- Visual certification:
- Source Traceability
- Chart/scenario metadata validation:

These are baseline markers for preview proof and can be expanded in later slices.

### 4. Required Section Markers

Proof requires section-level marker presence:

- report identity marker(s)
- analysis marker(s)
- source traceability marker(s)
- visual QA marker(s)

Section marker set is defined as contract input for deterministic checks.

### 5. Fail-Closed Statuses

Text extraction proof statuses:

- passed
- failed_closed

Mandatory fail-closed reasons include:

- missing_pdf_bytes
- extraction_library_unavailable
- extraction_error
- missing_required_text_markers
- missing_required_section_markers

No open/partial pass status in v1.

### 6. No File-Write Requirement

The module must not write files.

- in-memory only for extraction checks
- return structured evidence dictionary to caller
- no persistence side effects in preview module

### 7. Operational Boundaries

The module must not introduce:

- dashboard behavior changes
- delivery workflow changes
- certification automation changes
- approval gate changes
- output-path changes

---

## Contract Shape (Preview Target)

run_text_extraction_proof(pdf_bytes, required_text_markers, required_section_markers) -> dict

Minimum output fields:

- schema_version
- proof_channel = text_extraction
- proof_status
- failure_reasons
- extracted_text_length
- matched_text_markers
- missing_text_markers
- matched_section_markers
- missing_section_markers
- pdf_generation_performed = false
- file_write_performed = false
- renderer_behavior_changed = false
- dashboard_behavior_changed = false
- delivery_workflow_changed = false
- certification_automation_changed = false

---

## Implementation Sequence Link

After this design lock:

- proceed to button2-customer-pdf-phase3-text-extraction-proof-preview-v1
- implement in-memory extraction proof helper + tests
- enforce fail-closed defaults and no-write constraints

---

## Final Statement

This design locks the first real Phase 3 proof module boundary: text extraction proof only, fail-closed, in-memory, non-operational, and governance-safe.