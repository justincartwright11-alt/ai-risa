# Button 2 Customer PDF - Phase 3 Header-Footer-Watermark Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-header-footer-watermark-proof-design-v1
- Type: docs-only
- Purpose: define fail-closed header/footer/watermark proof contract before implementation

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

Define a safe proof channel for validating required header/footer/watermark claims from supplied rendered-output proof input, without changing rendering behavior.

---

## Scope

Header/footer/watermark proof covers evidence checks only:

- required header token presence
- required footer token presence
- watermark policy token presence/absence
- forbidden watermark token detection
- page-coverage checks for header/footer markers

Out of scope:

- visual styling polish
- geometry overlap logic
- page-section ordering logic
- renderer behavior changes
- delivery/certification automation changes

---

## Evidence Inputs

Required runtime inputs for preview implementation:

- header_footer_hits: list of discovered header/footer/watermark evidence records
- required_header_tokens: list of required header tokens
- required_footer_tokens: list of required footer tokens
- required_watermark_tokens: list of required watermark tokens (policy dependent)
- forbidden_watermark_tokens: list of forbidden watermark tokens
- required_page_coverage: page indexes that must include required header/footer evidence

Each hit should provide:

- page_index
- area_type (header | footer | watermark)
- token
- optional marker id

---

## Required Checks

1. Header Token Presence Check
   - all required header tokens must be present

2. Footer Token Presence Check
   - all required footer tokens must be present

3. Watermark Policy Check
   - required watermark tokens must be present when required
   - forbidden watermark tokens must fail closed

4. Page Coverage Check
   - required pages contain header/footer evidence

5. Hit Shape Check
   - every evidence record includes minimum fields and valid area type

---

## Fail-Closed Status Model

Header-footer-watermark proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- hfw_channel_unavailable
- invalid_hfw_hit_shape
- missing_required_header_tokens
- missing_required_footer_tokens
- missing_required_watermark_tokens
- forbidden_watermark_tokens_detected
- required_page_coverage_missing

No partial pass in v1.

---

## Output Signal Model

Preview output should include hfw_signal:

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

run_header_footer_watermark_proof(header_footer_hits, required_header_tokens, required_footer_tokens, required_watermark_tokens, forbidden_watermark_tokens, required_page_coverage, hfw_channel_available=True) -> dict

Minimum output fields:

- schema_version
- proof_channel = header_footer_watermark
- proof_status
- hfw_signal
- failure_reasons
- discovered_hfw_hit_count
- missing_required_header_tokens
- missing_required_footer_tokens
- missing_required_watermark_tokens
- forbidden_watermark_tokens_detected
- missing_required_page_coverage
- pdf_generation_performed
- file_write_performed
- renderer_behavior_changed
- dashboard_behavior_changed
- delivery_workflow_changed
- certification_automation_changed

---

## Implementation Sequence Link

After design lock:

1. header-footer-watermark proof preview helper
2. header-footer-watermark proof smoke tests
3. integrate channel with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design locks a governance-safe header/footer/watermark proof channel with fail-closed contracts and no operational expansion.
