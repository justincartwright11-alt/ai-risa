# Button 2 Customer PDF - Phase 3 Source-Traceability Proof Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-source-traceability-proof-design-v1
- Type: docs-only
- Purpose: define fail-closed source-traceability proof contract before implementation

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

Define a safe proof channel for validating required source-traceability claims from supplied rendered-output proof input, without changing rendering behavior.

---

## Scope

Source-traceability proof covers evidence checks only:

- source type token presence
- source class token presence
- citation completeness validation
- source verification status token presence
- required source markers per section
- forbidden source class detection
- source footer placement markers

Out of scope:

- visual styling polish
- geometry overlap logic
- page-section ordering logic
- renderer behavior changes
- delivery/certification automation changes

---

## Evidence Inputs

Required runtime inputs for preview implementation:

- source_traceability_hits: list of discovered source-traceability evidence records
- required_source_types: list of required source types
- required_source_classes: list of required source classes
- required_citations_per_section: mapping of section name to minimum citation count
- forbidden_source_classes: list of forbidden source classes
- required_verification_statuses: list of required verification status tokens

Each hit should provide:

- section_name
- source_index
- source_type
- source_class
- citation_count
- verification_status
- optional marker_id

---

## Required Checks

1. Source Type Presence Check
   - all required source types must be present

2. Source Class Presence Check
   - all required source classes must be present

3. Citation Completeness Check
   - each section's required source citation count must be met

4. Verification Status Check
   - all required verification statuses must be present

5. Forbidden Source Class Detection
   - forbidden source classes must fail closed

6. Hit Shape Check
   - every evidence record includes minimum required fields

---

## Fail-Closed Status Model

Source-traceability proof statuses:

- passed
- failed_closed

Deterministic failure reasons (minimum set):

- source_channel_unavailable
- invalid_source_hit_shape
- missing_required_source_types
- missing_required_source_classes
- missing_required_citations
- forbidden_source_classes_detected
- missing_required_verification_statuses

No partial pass in v1.

---

## Output Signal Model

Preview output should include source_signal:

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

run_source_traceability_proof(source_traceability_hits, required_source_types, required_source_classes, required_citations_per_section, forbidden_source_classes, required_verification_statuses, source_channel_available=True) -> dict

Minimum output fields:

- schema_version
- proof_channel = source_traceability
- proof_status
- source_signal
- failure_reasons
- discovered_source_hit_count
- missing_required_source_types
- missing_required_source_classes
- missing_required_citations
- forbidden_source_classes_detected
- missing_required_verification_statuses
- pdf_generation_performed
- file_write_performed
- renderer_behavior_changed
- dashboard_behavior_changed
- delivery_workflow_changed
- certification_automation_changed

---

## Implementation Sequence Link

After design lock:

1. source-traceability proof preview helper
2. source-traceability proof smoke tests
3. integrate source-traceability channel with Phase 3 rendered-output proof orchestration

---

## Final Statement

This design locks a governance-safe source-traceability proof channel with fail-closed contracts and no operational expansion.
