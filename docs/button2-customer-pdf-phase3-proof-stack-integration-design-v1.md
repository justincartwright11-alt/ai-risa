# Button 2 Customer PDF - Phase 3 Proof Stack Integration Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-proof-stack-integration-design-v1
- Type: docs-only
- Purpose: define fail-closed proof-stack integration contract before implementation

---

## Core Rule

Proof orchestration before operational expansion.

- No renderer rewrite
- No PDF generation behavior changes
- No dashboard behavior changes
- No delivery workflow changes
- No certification automation
- No file writes

---

## Objective

Define a safe proof orchestration channel that combines all Phase 3 proof signals into a single fail-closed rendered-output proof result, without changing rendering behavior.

---

## Proof Stack Channels

Phase 3 orchestration integrates seven proof channels:

1. **Text Extraction Proof** (button2-customer-pdf-phase3-text-extraction-proof-*)
   - Validates text markers in rendered output
   - Required placeholder guard tokens present/absent
   - Signal: clear | detected | unavailable

2. **Geometry Proof** (button2-customer-pdf-phase3-geometry-proof-*)
   - Validates region placement and bounds
   - Detects off-page and overlapping content
   - Signal: clear | detected | unavailable

3. **Page-Section Proof** (button2-customer-pdf-phase3-page-section-proof-*)
   - Validates section presence and order
   - Validates page-count expectations
   - Signal: clear | detected | unavailable

4. **Typography-Style Proof** (button2-customer-pdf-phase3-typography-style-proof-*)
   - Validates font-sizes, font-weights, line-heights within ranges
   - Validates required style tokens present
   - Signal: clear | detected | unavailable

5. **Header-Footer-Watermark Proof** (button2-customer-pdf-phase3-header-footer-watermark-proof-*)
   - Validates header/footer/watermark token presence
   - Validates required page coverage
   - Signal: clear | detected | unavailable

6. **Source-Traceability Proof** (button2-customer-pdf-phase3-source-traceability-proof-*)
   - Validates source class and citation presence
   - Validates source footer marker placement
   - Signal: clear | detected | unavailable

7. **Visual QA Rollup Proof** (button2-customer-pdf-phase3-visual-qa-rollup-proof-*)
   - Validates margin/padding ranges
   - Validates consistency markers and hierarchy
   - Signal: clear | detected | unavailable

---

## Integration Model

All seven proof channels must produce deterministic input-only evidence summaries.

Each channel independently validates supplied rendered-output proof input:
- No side effects (no PDF generation, no file writes, no renderer behavior changes)
- No feedback loops (no re-triggering renderer or dashboard)
- No learning/calibration (no database writes)

Stack orchestrator receives all seven signal results and produces final proof result:
- Orchestrator does NOT run individual channels (channels run independently, then results passed to orchestrator)
- Orchestrator combines signals deterministically (all clear → final clear; any detected → final detected; any unavailable → final unavailable)
- Orchestrator reports no side effects (inherits from all channels: all false → orchestrator all false)

---

## Proof Stack Contract

**Input:**
- seven_proof_channels_results: dict mapping channel_name -> proof_result dict
  - Expected keys: text_extraction, geometry, page_section, typography_style, header_footer_watermark, source_traceability, visual_qa_rollup
  - Each proof_result must include: proof_status, signal field (xxx_signal), failure_reasons

**Output:**

```python
{
    "schema_version": "button2.phase3.proof_stack_integration.v1",
    "proof_channel": "proof_stack_integration",
    "proof_status": "passed" | "failed_closed",
    "stack_signal": "clear" | "detected" | "unavailable",
    "failure_reasons": [reasons from all channels],
    "channel_signals": {
        "text_extraction": "clear" | "detected" | "unavailable",
        "geometry": "clear" | "detected" | "unavailable",
        "page_section": "clear" | "detected" | "unavailable",
        "typography_style": "clear" | "detected" | "unavailable",
        "header_footer_watermark": "clear" | "detected" | "unavailable",
        "source_traceability": "clear" | "detected" | "unavailable",
        "visual_qa_rollup": "clear" | "detected" | "unavailable",
    },
    "channel_failure_reasons": {
        "text_extraction": [...],
        "geometry": [...],
        ...
    },
    "pdf_generation_performed": False,
    "file_write_performed": False,
    "renderer_behavior_changed": False,
    "dashboard_behavior_changed": False,
    "delivery_workflow_changed": False,
    "certification_automation_changed": False,
}
```

---

## Signal Determination Logic

1. If any channel signal is unavailable → stack_signal = unavailable
2. Else if any channel signal is detected → stack_signal = detected
3. Else all channels clear → stack_signal = clear

Stack proof_status:
- signal=clear → proof_status=passed
- signal=detected or unavailable → proof_status=failed_closed

---

## Failure Reasons Aggregation

Failure reasons collected from all seven channels and flattened into single list:
- Stack failure_reasons = [channel_1_reasons..., channel_2_reasons..., ...]
- Channel-specific reasons remain descriptive and traceable

---

## No-Write and No-Behavior-Change Constraints

Stack orchestrator must explicitly report:

- pdf_generation_performed = false (all channels false → orchestrator false)
- file_write_performed = false (all channels false → orchestrator false)
- renderer_behavior_changed = false (all channels false → orchestrator false)
- dashboard_behavior_changed = false (all channels false → orchestrator false)
- delivery_workflow_changed = false (all channels false → orchestrator false)
- certification_automation_changed = false (all channels false → orchestrator false)

---

## Implementation Sequence Link

After design lock:

1. proof-stack-integration preview orchestrator (combines all channel results)
2. proof-stack-integration smoke tests (clear/detected/unavailable paths)
3. integrate proof-stack with Phase 3 rendered-output proof entry point

---

## Data Contract Guarantee

Each channel proof_result is expected to include:

- schema_version: str (e.g., "button2.phase3.xxx_proof.v1")
- proof_channel: str (e.g., "text_extraction", "geometry", ...)
- proof_status: str ("passed" | "failed_closed")
- {channel}_signal: str ("clear" | "detected" | "unavailable")
- failure_reasons: list of str
- pdf_generation_performed: bool (false)
- file_write_performed: bool (false)
- renderer_behavior_changed: bool (false)
- dashboard_behavior_changed: bool (false)
- delivery_workflow_changed: bool (false)
- certification_automation_changed: bool (false)

Orchestrator validates contract shape before combining signals.

---

## Final Statement

This design locks a governance-safe proof-stack integration orchestrator with fail-closed contracts, deterministic signal combination, and no operational expansion.
