# Button 2 Visual QA Metadata Rollup Design (v1)

**Slice**: button2-customer-pdf-visual-qa-metadata-rollup-design-v1

**Design Status**: DOCS-ONLY DESIGN LOCKED (no implementation)

**Prior Layer**: button2-customer-pdf-source-traceability-visual-layer-final-handoff-v1 (e2a1e5a)

---

## Executive Summary

The Visual QA Metadata Rollup layer (Layer 7) consolidates all 6 visual-polish metadata layer validations into a single comprehensive QA status block. This layer does NOT automate certification decisions—it provides rich metadata about all validation statuses so operators can make informed approval decisions.

**Key principle**: All decisions remain with operators. This layer is observational, not prescriptive.

---

## Scope

### What This Layer Does

Combines validation results from:
1. Typography CSS tokens (Layer 1)
2. Page hierarchy markers (Layer 2)
3. Page-break/section-block policies (Layer 3)
4. Chart/scenario tree metadata (Layer 4)
5. Header/footer/watermark metadata (Layer 5)
6. Source traceability metadata (Layer 6)
7. Overlap proof status (existing)
8. Off-page text proof status (existing)

### What This Layer Does NOT Do

- ❌ Automate `visual_certification_status` — operators decide
- ❌ Block approval — all validation is informational
- ❌ Change renderer behavior
- ❌ Add new file-write operations
- ❌ Change approval gates
- ❌ Change PDF output

---

## Visual QA Rollup Metadata Structure

### Top-Level Rollup Schema

```python
{
    "schema_version": "button2.visual_qa_rollup.v1",
    "rollup_generated_timestamp": "2026-05-17T12:00:00Z",
    "rollup_status": "mixed|all_valid|all_invalid",  # Enum
    "layer_validation_summary": {
        # All 6 layers + proofs
    },
    "visual_qa_indicators": {
        # QA status summary
    },
    "recommended_review_focus": [
        # Prioritized list of areas needing attention
    ],
}
```

### Layer Validation Summary Structure

```python
"layer_validation_summary": {
    "layer_1_typography": {
        "schema_version": "button2.page_typography_tokens.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "layer_2_hierarchy": {
        "schema_version": "button2.page_hierarchy.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "layer_3_page_breaks": {
        "schema_version": "button2.page_breaks_and_blocks.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "layer_4_charts": {
        "schema_version": "button2.chart_and_scenario.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "layer_5_header_footer_watermark": {
        "schema_version": "button2.header_footer_watermark.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "layer_6_source_traceability": {
        "schema_version": "button2.source_traceability.v1",
        "validation_status": "valid|invalid|missing",
        "validation_issues_count": 0,
        "required_for_certification": True,
    },
    "proof_overlap": {
        "proof_kind": "overlap_proof",
        "proof_status": "present|missing|invalid",
        "required_for_certification": True,
    },
    "proof_off_page_text": {
        "proof_kind": "off_page_text_proof",
        "proof_status": "present|missing|invalid",
        "required_for_certification": True,
    },
}
```

### Visual QA Indicators

```python
"visual_qa_indicators": {
    "overall_visual_completeness": 0.0..1.0,  # Float [0.0, 1.0]
    "overall_visual_confidence": "high|medium|low|unknown",
    "certification_readiness": "ready|needs_review|not_ready",
    "valid_layers_count": 6,
    "invalid_layers_count": 0,
    "missing_layers_count": 0,
    "layers_requiring_attention": [
        # List of layer names needing attention
    ],
}
```

### Recommended Review Focus

```python
"recommended_review_focus": [
    {
        "priority": 1,
        "category": "layer_5_header_footer_watermark",
        "issue": "missing_metadata",
        "recommendation": "Provide header/footer/watermark metadata before certification",
    },
    {
        "priority": 2,
        "category": "layer_6_source_traceability",
        "issue": "incomplete_citation",
        "recommendation": "Add missing source URLs to improve traceability",
    },
]
```

---

## Input Contracts

### Layer Validation Inputs (From Prior Layers)

Each layer provides:
```
{
    "schema_version": str,
    "validation_status": "valid" | "invalid" | "missing",
    "validation_issues": list[str],
}
```

**Source**: Embedded in HTML metadata sections (already present)

### Proof Inputs (Existing)

```
overlap_proof: dict {
    "status": "present" | "missing" | "invalid",
    ...
}

off_page_text_proof: dict {
    "status": "present" | "missing" | "invalid",
    ...
}
```

**Source**: Already in `report_context_preview`

---

## Validation Contracts

### Rollup Status Enum

```
"rollup_status":
  - "all_valid" — All 8 inputs are valid
  - "mixed" — Some valid, some invalid/missing
  - "all_invalid" — All 8 inputs are invalid or missing
```

### Validation Status Enum (Per Layer)

```
"validation_status": 
  - "valid" — Layer metadata valid
  - "invalid" — Layer metadata present but invalid
  - "missing" — Layer metadata not provided
```

### Proof Status Enum

```
"proof_status":
  - "present" — Proof available and valid
  - "missing" — Proof not provided
  - "invalid" — Proof present but invalid
```

### Certification Readiness Enum

```
"certification_readiness":
  - "ready" — All 8 inputs valid OR operator override enabled
  - "needs_review" — Some inputs invalid; operator review recommended
  - "not_ready" — Critical inputs missing/invalid
```

### Confidence Levels Enum

```
"overall_visual_confidence":
  - "high" — All 8 inputs valid
  - "medium" — 6-7 inputs valid, 1-2 invalid/missing
  - "low" — 3-5 inputs valid, 3-5 invalid/missing
  - "unknown" — Cannot determine (no inputs)
```

---

## Calculation Rules

### Overall Visual Completeness

```
overall_visual_completeness = (valid_input_count / total_inputs) * 1.0

Where:
  total_inputs = 8 (6 layers + 2 proofs)
  valid_input_count = count where validation_status == "valid" OR proof_status == "present"

Result: Float in [0.0, 1.0]
  1.0 = all 8 valid/present
  0.0 = none valid/present
```

### Overall Visual Confidence

```
if overall_visual_completeness == 1.0:
    confidence = "high"
elif overall_visual_completeness >= 0.75:
    confidence = "medium"
elif overall_visual_completeness >= 0.50:
    confidence = "low"
else:
    confidence = "unknown"
```

### Certification Readiness

```
if ALL (8 inputs valid/present):
    readiness = "ready"
elif invalid_count > 0 AND invalid_count < 3:
    readiness = "needs_review"
else:
    readiness = "not_ready"
```

### Layers Requiring Attention

```
List layer names where:
  validation_status != "valid" OR (proof_status != "present")

Ordered by:
  1. Missing layers (highest priority)
  2. Invalid layers (medium priority)
  3. Layer dependency order
```

### Recommended Review Focus

Generate prioritized list:
```
Priority 1: Missing critical proofs (overlap_proof, off_page_text_proof)
Priority 2: Missing layer metadata
Priority 3: Invalid layer metadata (specific issues)
Priority 4: Low-confidence inputs
```

---

## Cross-Field Validation Rules

### Rule 1: Consistency Check
```
If any_layer_invalid AND proof_both_valid:
    → Mark for operator review (design issue, not certification blocker)

If all_layers_valid AND any_proof_invalid:
    → Mark for operator review (metadata good, proof gap)
```

### Rule 2: Required Fields
```
All 8 inputs are required for "ready" status:
  - 6 layer validation_status fields
  - 2 proof status fields

Missing any → certification_readiness = "not_ready"
```

### Rule 3: Fail-Closed Cascade
```
If layer_{n} = invalid:
    → validation_status = "invalid"
    → Add to recommended_review_focus

If proof_{k} = missing:
    → proof_status = "missing"
    → Add to recommended_review_focus

If ANY input is missing AND visual_qa_rollup not provided:
    → rollup_status = "mixed" (not "all_valid")
```

### Rule 4: Proof Dependency
```
If overlap_proof = invalid:
    → certification_readiness should not be "ready"
    
If off_page_text_proof = missing:
    → certification_readiness downgrade to "needs_review"
```

---

## HTML Embedding Schema

### Metadata Section Structure

```html
<section
    id="button2-visual-qa-rollup-metadata"
    class="visual-qa-rollup-metadata"
    data-visual-qa-rollup-schema-version="button2.visual_qa_rollup.v1"
    data-visual-qa-rollup-status="{rollup_status}"
    data-certification-readiness="{certification_readiness}"
    data-visual-completeness="{overall_visual_completeness}"
    data-visual-confidence="{overall_visual_confidence}"
>
    <pre data-hierarchy-level="Meta">{json_payload}</pre>
</section>
```

### CSS Hiding

```css
.visual-qa-rollup-metadata { display: none; }
```

### QA Footer Row

```html
<div class="qa-row">
  Visual QA rollup status: {rollup_status} 
  | Certification readiness: {certification_readiness} 
  | Completeness: {overall_visual_completeness:.0%}
</div>
```

### Extended QA Rows (Optional)

```html
<div class="qa-row">Valid layers: {valid_layers_count} / 6</div>
<div class="qa-row">Layers requiring attention: {layers_requiring_attention_count}</div>
<div class="qa-row">Overall confidence: {overall_visual_confidence}</div>
```

---

## Default Rollup Metadata Generation

When visual QA rollup not provided in report context:

```python
def _default_visual_qa_rollup_metadata():
    return {
        "schema_version": "button2.visual_qa_rollup.v1",
        "rollup_generated_timestamp": "2026-05-17T12:00:00Z",
        "rollup_status": "missing",
        "layer_validation_summary": {
            "layer_1_typography": {"validation_status": "missing", ...},
            "layer_2_hierarchy": {"validation_status": "missing", ...},
            "layer_3_page_breaks": {"validation_status": "missing", ...},
            "layer_4_charts": {"validation_status": "missing", ...},
            "layer_5_header_footer_watermark": {"validation_status": "missing", ...},
            "layer_6_source_traceability": {"validation_status": "missing", ...},
            "proof_overlap": {"proof_status": "missing", ...},
            "proof_off_page_text": {"proof_status": "missing", ...},
        },
        "visual_qa_indicators": {
            "overall_visual_completeness": 0.0,
            "overall_visual_confidence": "unknown",
            "certification_readiness": "not_ready",
            "valid_layers_count": 0,
            "invalid_layers_count": 0,
            "missing_layers_count": 8,
            "layers_requiring_attention": [
                "layer_1_typography",
                "layer_2_hierarchy",
                "layer_3_page_breaks",
                "layer_4_charts",
                "layer_5_header_footer_watermark",
                "layer_6_source_traceability",
                "proof_overlap",
                "proof_off_page_text",
            ],
        },
        "recommended_review_focus": [
            {
                "priority": 1,
                "category": "all_layers",
                "issue": "missing_visual_qa_rollup_metadata",
                "recommendation": "Provide visual QA rollup metadata",
            }
        ],
    }
```

---

## Payload Structure

### Rollup Payload Builder

```python
def _visual_qa_rollup_payload(report_context_preview):
    """
    Build and validate visual QA rollup payload.
    
    Inputs:
    - All 6 layer payloads (from HTML metadata or defaults)
    - overlap_proof (from report_context_preview)
    - off_page_text_proof (from report_context_preview)
    - existing visual_qa_rollup_metadata (optional)
    
    Returns:
    {
        "schema_version": "button2.visual_qa_rollup.v1",
        "validation_status": "valid|invalid",
        "validation_issues": [],
        "allowed_rollup_statuses": ["all_valid", "mixed", "all_invalid"],
        "allowed_confidence_levels": ["high", "medium", "low", "unknown"],
        "allowed_readiness_levels": ["ready", "needs_review", "not_ready"],
        "visual_qa_rollup": {
            # Full rollup metadata structure
        },
    }
    """
```

---

## Fail-Closed Behavior

### Non-Blocking Design

- ❌ Visual QA rollup does NOT block approval
- ❌ Visual QA rollup does NOT change certification decisions
- ✅ Visual QA rollup IS informational for operator review

### Validation Failure Handling

If rollup metadata is invalid:
- Outer payload `validation_status` = "invalid"
- Inner rollup falls back to defaults
- Certification status unchanged (no downgrade)
- QA rows show "unknown" or "not_ready"

---

## Implementation Strategy (Future)

### Phase 1: Payload Generation
1. Extract all 6 layer validation statuses from HTML metadata
2. Extract proof statuses from report context
3. Calculate QA indicators (completeness, confidence, readiness)
4. Generate recommended review focus
5. Build complete rollup metadata structure

### Phase 2: Integration
1. Add `_visual_qa_rollup_payload()` to composition entry point
2. Add rollup metadata section to HTML template
3. Add rollup QA footer rows
4. Integrate with all 6 layer validations

### Phase 3: Testing
1. **Implementation tests** (~40-50):
   - Rollup status calculation (all_valid, mixed, all_invalid)
   - Completeness calculation
   - Confidence level mapping
   - Readiness determination
   - Recommended focus generation
   - Cross-field validation rules

2. **Smoke tests** (~10-15):
   - All 7 layers coexist (6 layers + rollup)
   - All schema versions present
   - CSS display:none rules active
   - Safety flags preserved
   - No duplicate sections
   - Fail-closed logic intact

### Phase 4: Final Handoff
- Comprehensive handoff documentation
- All tests passing (expected: 180+ total)
- Complete implementation locked and tagged

---

## Safety Invariants (Always Preserved)

- ✅ No renderer changes
- ✅ No approval logic changes
- ✅ No certification automation (decisions remain with operators)
- ✅ No output path changes
- ✅ No file-write behavior changes
- ✅ No dashboard changes
- ✅ No delivery workflow changes
- ✅ All safety flags preserved (preview_only=True, etc)
- ✅ All 6 prior layers remain intact and unchanged
- ✅ No new approval gates or conditions

---

## Metadata-First Composition Pattern

The Visual QA Rollup follows the established pattern:

1. **Constants & Enums** — Rollup status, confidence, readiness enums
2. **Default Generator** — `_default_visual_qa_rollup_metadata()`
3. **Validator** — Validate enum values, calculation rules
4. **Payload Builder** — `_visual_qa_rollup_payload()`
5. **HTML Embedding** — Hidden section with JSON payload
6. **QA Rows** — Multiple rows showing rollup status
7. **Fail-Closed Logic** — Invalid rollup → no side effects
8. **Test Coverage** — Implementation + Smoke tests

---

## Integration with Prior Layers

### Layer Dependencies

```
Layer 7 (Rollup) depends on:
├── Layer 1 (Typography) — validation_status input
├── Layer 2 (Hierarchy) — validation_status input
├── Layer 3 (Page-breaks) — validation_status input
├── Layer 4 (Charts) — validation_status input
├── Layer 5 (Header/Footer/Watermark) — validation_status input
├── Layer 6 (Source Traceability) — validation_status input
├── Existing (Overlap Proof) — proof_status input
└── Existing (Off-Page Proof) — proof_status input
```

### No Changes to Prior Layers

- ✅ All 6 prior layers remain unchanged
- ✅ No new validation rules in prior layers
- ✅ No new metadata fields in prior layers
- ✅ Rollup only reads, never modifies

---

## Operator Workflow Impact

### For Operator Dashboard

- **Invisible**: All rollup metadata hidden (CSS display:none)
- **Informational**: Rollup status visible in QA footer rows only
- **Non-Blocking**: No approval changes or new gates
- **Helpful**: Operator can review rollup before approving if desired

### For Approval Flow

- No changes to Gate 1, Gate 2, or delivery flow
- Visual QA rollup is observational only
- Certification decisions remain with operator

---

## Compliance Checklist

- ✅ Design-first (no implementation changes yet)
- ✅ No renderer changes
- ✅ No certification automation
- ✅ No approval logic changes
- ✅ No PDF output behavior changes
- ✅ All prior layers preserved
- ✅ Deterministic default generation
- ✅ Strict enum validation
- ✅ Hidden HTML sections (display:none)
- ✅ Rich QA metadata for operator reference
- ✅ Cross-field validation rules documented
- ✅ Fail-closed behavior specified (non-blocking)
- ✅ Pattern follows all 6 prior layers exactly
- ✅ Test strategy defined (40-50 implementation + 10-15 smoke)
- ✅ Safety invariants documented and preserved

---

## Next Steps

**Design Status**: ✅ LOCKED (docs-only, no code changes)

**Design Review Gate**: This design ready for approval.

**Implementation Trigger**: Proceed to implementation phase when approved.

**Expected Implementation Timeline**:
1. Modify composition entry point
2. Create implementation tests (40-50)
3. Create smoke tests (10-15)
4. Full regression (180+ tests)
5. Lock implementation
6. Create final handoff

**Track Integration**:
- Button 2 track: 7 visual-polish layers complete
- Button 1 track: Auto-Discovery + Ranking (separate)
- Button 3 track: Result Comparison + Learning (separate)

---

## Design Lock Checklist

- ✅ Purpose clearly stated (rollup consolidation)
- ✅ Metadata schema fully specified
- ✅ All enums defined with values
- ✅ Validation contracts documented
- ✅ Cross-field rules specified
- ✅ HTML embedding schema defined
- ✅ Default generation specified
- ✅ Calculation rules fully specified
- ✅ Fail-closed behavior (non-blocking) defined
- ✅ Implementation strategy outlined
- ✅ Test strategy defined
- ✅ Safety invariants preserved
- ✅ Pattern consistency verified
- ✅ No breaking changes to prior layers
- ✅ Operator workflow impact assessed

**Status**: ✅ DESIGN LOCKED — READY FOR IMPLEMENTATION WHEN APPROVED
