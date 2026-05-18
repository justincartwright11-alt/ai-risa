# Button 2 Customer PDF - Phase 3 Visual QA Rollup Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-visual-qa-rollup-proof-design-v1
- Type: docs-only
- Purpose: define fail-closed visual-qa rollup proof contract before implementation

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

Define a safe proof channel for validating visual quality assertions from supplied rendered-output proof input, without changing rendering behavior.

---

## Scope

Visual QA rollup proof covers evidence checks only:

- page margin and padding validation
- typography consistency validation
- color and style consistency validation
- layout alignment validation
- visual spacing validation
- component positioning validation
- visual grouping hierarchy validation

Out of scope:

- geometry overlap logic (handled by geometry proof)
- source traceability logic (handled by source-traceability proof)
- header/footer/watermark logic (handled by header-footer-watermark proof)
- renderer behavior changes
- delivery/certification automation changes

---

## Evidence Inputs

Required runtime inputs for preview implementation:

- visual_qa_hits: list of discovered visual-qa evidence records
- required_margin_ranges: dict mapping page_section -> [min_margin, max_margin]
- required_padding_ranges: dict mapping component_type -> [min_padding, max_padding]
- required_typography_consistency_markers: list of required typography consistency tokens
- required_color_consistency_markers: list of required color consistency tokens
- required_alignment_markers: list of required alignment tokens
- required_spacing_consistency_markers: list of required spacing consistency tokens

Each hit should provide:

- section_name
- check_id
- check_type (margin|padding|typography|color|alignment|spacing|hierarchy)
- component_name
- value (numeric for ranges, string for token presence)
- status (pass|fail)
- optional marker_id

---

## Required Checks

1. Page Margin Validation Check
   - all required_margin_ranges must have measured values within range

2. Component Padding Validation Check
   - all required_padding_ranges must have measured values within range

3. Typography Consistency Check
   - all required typography consistency markers must be present

4. Color Consistency Check
   - all required color consistency markers must be present

5. Layout Alignment Check
   - all required alignment markers must be present

6. Visual Spacing Consistency Check
   - all required spacing consistency markers must be present

7. Visual Hierarchy Validation Check
   - component positioning follows required hierarchy markers

8. Hit Shape Check
   - every evidence record includes minimum required fields

---

## Fail-Closed Status Model

Visual QA rollup proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- visual_qa_channel_unavailable
- invalid_visual_qa_hit_shape
- out_of_range_margins
- out_of_range_padding
- missing_typography_consistency_markers
- missing_color_consistency_markers
- missing_alignment_markers
- missing_spacing_consistency_markers
- visual_hierarchy_validation_failed

No partial pass in v1.

---

## Output Signal Model

Preview output should include visual_qa_signal:

- clear: all checks pass
- detected: rule violations found
- unavailable: channel unavailable or malformed input

Proof status remains failed_closed for detected and unavailable.

---

## No-Write and No-Behavior-Change Constraints

The helper must explicitly report:

- pdf_generation_performed = false
- file_write_performed = false
- renderer_behavior_changed = false
- dashboard_behavior_changed = false
- delivery_workflow_changed = false
- certification_automation_changed = false

---

## Preview Contract Target

run_visual_qa_rollup_proof(visual_qa_hits, required_margin_ranges, required_padding_ranges, required_typography_consistency_markers, required_color_consistency_markers, required_alignment_markers, required_spacing_consistency_markers, visual_qa_channel_available=True) -> dict

Minimum output fields:

- schema_version
- proof_channel = visual_qa_rollup
- proof_status
- visual_qa_signal
- failure_reasons
- discovered_visual_qa_hit_count
- out_of_range_margins
- out_of_range_padding
- missing_typography_consistency_markers
- missing_color_consistency_markers
- missing_alignment_markers
- missing_spacing_consistency_markers
- visual_hierarchy_failures
- pdf_generation_performed
- file_write_performed
- renderer_behavior_changed
- dashboard_behavior_changed
- delivery_workflow_changed
- certification_automation_changed

---

## Implementation Sequence Link

After design lock:

1. visual-qa-rollup proof preview helper
2. visual-qa-rollup proof smoke tests
3. integrate visual-qa-rollup channel with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design locks a governance-safe visual-qa-rollup proof channel with fail-closed contracts and no operational expansion.
