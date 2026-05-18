# Button 2 Customer PDF - Phase 3 Typography-Style Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-typography-style-proof-design-v1
- Type: docs-only
- Purpose: define fail-closed typography/style proof contract before implementation

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

Define a safe typography-style proof module that validates required typography/style tokens from supplied proof input for rendered output, without modifying rendering behavior.

---

## Scope

Typography-style proof covers metadata/token evidence only:

- required font family token presence
- required weight/size token presence
- required heading/body style token presence
- forbidden style token detection
- style consistency checks for fixed fixture sections

Out of scope:

- pixel-level visual comparison
- geometry overlap checks
- page/section ordering checks
- renderer behavior changes
- delivery/certification behavior changes

---

## Evidence Inputs

Required runtime inputs for preview implementation:

- style_hits: list of discovered style evidence records
- required_style_tokens: list of required style tokens
- forbidden_style_tokens: list of forbidden style tokens
- section_style_rules: mapping of section name to required token subset

Each style hit should provide:

- section_name
- token
- optional source marker id

---

## Required Checks

1. Required Token Presence Check
   - every required style token must be present in evidence

2. Forbidden Token Detection Check
   - any forbidden style token must fail closed

3. Section Rule Coverage Check
   - each section with style rules must include required tokens

4. Style Hit Shape Check
   - each style hit must include minimum required fields

5. Ambiguous Token Mapping Check
   - conflicting token mappings within the same section fail closed unless explicitly allowed

---

## Fail-Closed Status Model

Typography-style proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- style_channel_unavailable
- invalid_style_hit_shape
- missing_required_style_tokens
- forbidden_style_tokens_detected
- missing_section_style_tokens
- ambiguous_style_mapping
- missing_section_style_rules

No partial pass in v1.

---

## Output Signal Model

Preview output should include a style_signal field:

- clear: all checks pass
- detected: rule violations found
- unavailable: channel unavailable or malformed input

Proof status remains failed_closed for detected and unavailable.

---

## No-Write and No-Behavior-Change Constraints

The typography-style proof helper must explicitly report:

- pdf_generation_performed = false
- file_write_performed = false
- renderer_behavior_changed = false
- dashboard_behavior_changed = false
- delivery_workflow_changed = false
- certification_automation_changed = false

---

## Preview Contract Target

run_typography_style_proof(style_hits, required_style_tokens, forbidden_style_tokens, section_style_rules, style_channel_available=True) -> dict

Minimum output fields:

- schema_version
- proof_channel = typography_style
- proof_status
- style_signal
- failure_reasons
- discovered_style_hit_count
- missing_required_style_tokens
- forbidden_style_tokens_detected
- section_style_violations
- ambiguous_style_sections
- pdf_generation_performed
- file_write_performed
- renderer_behavior_changed
- dashboard_behavior_changed
- delivery_workflow_changed
- certification_automation_changed

---

## Implementation Sequence Link

After design lock:

1. typography-style proof preview helper
2. typography-style proof smoke tests
3. integrate typography-style channel with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design locks a governance-safe typography-style proof channel with fail-closed contracts and no operational expansion.
