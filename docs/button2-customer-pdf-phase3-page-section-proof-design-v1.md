# Button 2 Customer PDF - Phase 3 Page-Section Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-page-section-proof-design-v1
- Type: docs-only
- Purpose: define fail-closed page-section proof contract before implementation

---

## Core Rule

Proof before polish.

- No renderer rewrite
- No PDF generation behavior changes
- No dashboard behavior changes
- No delivery workflow changes
- No certification automation
- No file writes

---

## Objective

Define a safe page-section proof module that verifies required sections are present on allowed pages and in the required order for fixed fixtures.

---

## Scope

Page-section proof covers structure evidence only:

- required section presence
- required section order
- allowed page index/range placement
- duplicate or ambiguous section mapping detection

Out of scope:

- visual styling or typography checks
- geometry overlap checks
- renderer behavior changes
- delivery/certification behavior changes

---

## Evidence Inputs

Required runtime inputs for preview implementation:

- section_hits: list of discovered section anchors
- required_sections: ordered list of required section names
- allowed_section_pages: mapping of section name to allowed page indexes/ranges

Each section hit should provide:

- section_name
- page_index
- optional evidence text marker id

---

## Required Checks

1. Required Section Presence Check
   - all required sections must be present

2. Required Section Order Check
   - section order must match required sequence

3. Allowed Page Placement Check
   - each required section must appear on an allowed page

4. Ambiguity Check
   - duplicate/conflicting hits for a required section must fail closed unless explicitly allowed

5. Completeness Check
   - section hit records must include minimum required fields

---

## Fail-Closed Status Model

Page-section proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- section_channel_unavailable
- invalid_section_hit_shape
- missing_required_sections
- section_order_mismatch
- section_page_out_of_bounds
- ambiguous_section_mapping
- missing_allowed_page_rules

No partial pass in v1.

---

## Output Signal Model

Preview output should include a section_signal field:

- clear: all checks pass
- detected: rule violations found
- unavailable: section channel unavailable or malformed input

Proof status remains failed_closed for detected and unavailable.

---

## No-Write and No-Behavior-Change Constraints

The page-section proof helper must explicitly report:

- pdf_generation_performed = false
- file_write_performed = false
- renderer_behavior_changed = false
- dashboard_behavior_changed = false
- delivery_workflow_changed = false
- certification_automation_changed = false

---

## Preview Contract Target

run_page_section_proof(section_hits, required_sections, allowed_section_pages, section_channel_available=True) -> dict

Minimum output fields:

- schema_version
- proof_channel = page_section
- proof_status
- section_signal
- failure_reasons
- discovered_section_count
- missing_required_sections
- section_order_violations
- out_of_bounds_sections
- ambiguous_sections
- pdf_generation_performed
- file_write_performed
- renderer_behavior_changed
- dashboard_behavior_changed
- delivery_workflow_changed
- certification_automation_changed

---

## Implementation Sequence Link

After design lock:

1. page-section proof preview helper
2. page-section proof smoke tests
3. integrate page-section channel with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design locks a governance-safe page-section proof channel with fail-closed contracts and no operational expansion.
