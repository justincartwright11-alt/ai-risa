# Button 2: Source Traceability Visual Layer Design (v1)

**Status**: DESIGN PHASE (no implementation yet)  
**Date**: 2026-05-17

---

## Executive Summary

This design document defines the source traceability visual layer for Button 2 customer PDF reports. The source traceability layer adds rich metadata about information sources, credibility signals, and research lineage without introducing renderer changes, approval logic changes, or file-write behavior changes.

Following established Button 2 patterns:
- **Metadata-first** — Define contracts before rendering
- **Fail-closed** — Invalid/missing metadata → certification downgrade
- **Renderer-agnostic** — Annotations only, no rendering logic
- **Non-intrusive** — Composition-only, no approval/delivery changes

---

## Design Governance

### Scope (In)
- ✅ Source block metadata structure
- ✅ Source classification contracts (official/research/operator)
- ✅ Confidence/credibility label enums
- ✅ Source footer placement rules
- ✅ Traceability QA metadata
- ✅ Validation contracts and fail-closed behavior
- ✅ HTML metadata embedding schema
- ✅ Default metadata generation
- ✅ Test strategy

### Scope (Out)
- ❌ Renderer implementation (future layer)
- ❌ PDF output behavior changes
- ❌ Approval gate changes
- ❌ Dashboard changes
- ❌ File-write behavior changes
- ❌ Customer workflow changes
- ❌ Operator approval workflow changes

---

## Source Traceability Context

### Current State
- Sources collected in `source_traceability` list in report_context_preview
- Each source has: id, type, date, url (optional)
- Currently rendered as simple `<li>` items in HTML
- No classification, credibility labeling, or research lineage

### Goal
- Classify sources by provenance (official/research/operator)
- Add credibility signals (confidence levels, corroboration counts)
- Track research lineage (which analyses relied on which sources)
- Provide QA metadata for operator verification
- Make source traceability machine-readable for downstream processing

### Non-Goal
- Change PDF rendering (rendering layer will follow)
- Add operator approval requirements
- Change delivery workflow
- Modify dashboard display

---

## Source Classification Model

### Source Types (Existing)
```
- "official" — Official organization records (boxing.org, tapology, sherdog, etc.)
- "research" — Research/analysis sources (academic papers, statistical analysis)
- "operator" — Operator-curated sources (manual research, expert notes)
```

### Source Class Mapping
```python
{
    "official": {
        "tier": "tier_a",
        "requires_citation": True,
        "credibility_baseline": "high",
        "examples": ["boxing.org", "tapology", "sherdog"]
    },
    "research": {
        "tier": "tier_b",
        "requires_citation": True,
        "credibility_baseline": "medium",
        "examples": ["academic_paper", "statistical_analysis"]
    },
    "operator": {
        "tier": "tier_c",
        "requires_citation": False,
        "credibility_baseline": "operator_determined",
        "examples": ["manual_research", "expert_notes"]
    }
}
```

---

## Confidence/Credibility Labels

### Confidence Levels
```
"high" — Source is authoritative, well-sourced, corroborated
"medium" — Source is credible but single-sourced or dated
"low" — Source is preliminary, requires corroboration
"uncertain" — Source credibility cannot be determined
```

### Credibility Signal Attributes
```python
{
    "confidence_level": "high|medium|low|uncertain",
    "corroboration_count": int,  # How many other sources corroborate this
    "corroborating_source_ids": [str],  # IDs of corroborating sources
    "last_updated": str,  # ISO 8601 timestamp
    "citation_quality": "complete|partial|minimal",  # How complete the citation is
    "verification_status": "verified|unverified|contradicted"  # vs. real-world facts
}
```

---

## Source Block Metadata Structure

### Per-Source Metadata
```python
{
    "source_id": str,  # Unique identifier (e.g., "src_boxing_org_001")
    "source_type": str,  # "official" | "research" | "operator"
    "source_class": str,  # "tier_a" | "tier_b" | "tier_c"
    "source_title": str,  # Human-readable title
    "source_url": str,  # URL if available
    "source_date": str,  # ISO 8601 date of source
    "ingest_date": str,  # When ingested into system
    
    # Credibility signals
    "confidence_level": str,  # "high" | "medium" | "low" | "uncertain"
    "confidence_justification": str,  # Why assigned this level
    "corroboration_count": int,  # Count of corroborating sources
    "corroborating_source_ids": [str],  # IDs that corroborate
    
    # Citation and verification
    "citation_completeness": str,  # "complete" | "partial" | "minimal"
    "verification_status": str,  # "verified" | "unverified" | "contradicted"
    "verification_timestamp": str,  # When verified
    "verification_note": str,  # Optional note about verification
    
    # Operator context
    "operator_id": str,  # Operator who added/curated source
    "operator_note": str,  # Optional operator comment
    "operator_confidence_override": bool,  # Operator override flag
}
```

### Source Block Collection
```python
{
    "schema_version": "button2.source_traceability.v1",
    "validation_status": "valid|invalid|missing",
    "validation_issues": [str],  # List of validation failures
    
    "total_sources": int,
    "official_sources_count": int,
    "research_sources_count": int,
    "operator_sources_count": int,
    
    "average_confidence_level": str,  # "high" | "medium" | "low" | "uncertain"
    "corroboration_coverage": float,  # 0.0-1.0: what % are corroborated
    
    "sources": [
        {per-source metadata as above}
    ],
    
    "lineage_graph": {
        # Which analyses relied on which sources
        "analysis_id_1": ["src_id_1", "src_id_2"],
        "analysis_id_2": ["src_id_1", "src_id_3"]
    }
}
```

---

## Source Footer Placement Contracts

### Footer Model
```python
{
    "placement": "section_footer|document_footer|inline",
    "visibility": "always|on_demand|metadata_only",
    "format": "list|table|summary",
    
    # Summary metrics
    "show_source_count": bool,
    "show_confidence_stats": bool,
    "show_corroboration_stats": bool,
    "show_verification_status": bool,
    
    # Interactivity (for PDF renderer to implement later)
    "source_links_enabled": bool,
    "confidence_badges_enabled": bool,
    "verification_checkmarks_enabled": bool,
}
```

### Section Footer (After Source Traceability Section)
- List of all sources used in that section
- Confidence levels for each source
- Corroboration indicators
- Verification status
- Operator notes (if any)

### Document Footer (At End)
- Summary of all sources in document
- Source classification breakdown (official/research/operator counts)
- Average confidence level
- Corroboration coverage (% of sources with multiple corroborations)
- Data freshness note (oldest/newest source dates)

### Inline (Future)
- Superscript source references in text
- Hover/click to show source details
- (Not implemented in composition layer; reserved for renderer)

---

## Validation Contracts

### Required Fields
```
Per source:
- source_id: non-empty string
- source_type: must be in {official, research, operator}
- source_class: must match source_type mapping (e.g., official → tier_a)
- source_title: non-empty string
- confidence_level: must be in {high, medium, low, uncertain}

Collection:
- schema_version: must be "button2.source_traceability.v1"
- sources: non-empty list
```

### Optional But Validated
```
Per source:
- source_url: if provided, must be valid URL format
- source_date: if provided, must be ISO 8601 date
- corroboration_count: if provided, must be non-negative integer
- corroborating_source_ids: if provided, all IDs must exist in sources list
- verification_status: if provided, must be in {verified, unverified, contradicted}

Collection:
- lineage_graph: if provided, all analysis IDs and source IDs must be valid
```

### Enum Validation
```python
source_type in {"official", "research", "operator"}
source_class in {"tier_a", "tier_b", "tier_c"}
confidence_level in {"high", "medium", "low", "uncertain"}
citation_completeness in {"complete", "partial", "minimal"}
verification_status in {"verified", "unverified", "contradicted"}
```

### Cross-Field Validation
```
Rule 1: source_type="official" → source_class must be "tier_a"
Rule 2: source_type="research" → source_class must be "tier_b"
Rule 3: source_type="operator" → source_class must be "tier_c"

Rule 4: confidence_level="high" AND source_class="tier_c" → warning (contradiction)
Rule 5: confidence_level="low" AND source_class="tier_a" → warning (rare but possible)

Rule 6: corroborating_source_ids is non-empty → corroboration_count >= len(corroborating_source_ids)
Rule 7: corroboration_count=0 → corroborating_source_ids must be empty

Rule 8: verification_status="verified" → verification_timestamp must exist
Rule 9: verification_status="unverified" → verification_timestamp may be absent
```

### Fail-Closed Behavior
```
Invalid source metadata → validation_status = "invalid"
Missing required fields → validation_status = "missing"
Cross-field validation failures → validation_status = "invalid"

In either case:
  → visual_certification_status downgraded to "not_certified"
  → QA row shows validation issue
  → No HTML rendering of source footer (data remains in metadata)
```

---

## HTML Embedding Schema

### Hidden Metadata Section
```html
<section
    id="button2-source-traceability-metadata"
    class="source-traceability-metadata"
    data-source-traceability-schema-version="button2.source_traceability.v1"
    data-source-traceability-validation-status="valid|invalid|missing"
    data-total-sources="N"
    data-official-sources-count="N"
    data-research-sources-count="N"
    data-operator-sources-count="N"
    data-average-confidence-level="high|medium|low|uncertain"
    data-corroboration-coverage="0.0-1.0"
>
    <pre data-hierarchy-level="Meta">{json_payload}</pre>
</section>
```

### CSS Rule (Display: None)
```css
.source-traceability-metadata { display: none; }
```

### QA Footer Row
```html
<div class="qa-row">Source traceability metadata validation: {validation_status}</div>
<div class="qa-row">Total sources: {total_sources} (Official: {official_count}, Research: {research_count}, Operator: {operator_count})</div>
<div class="qa-row">Average confidence level: {avg_confidence}</div>
<div class="qa-row">Corroboration coverage: {coverage_percent}%</div>
```

---

## Default Metadata Generation

When `source_traceability_metadata` is not provided in report_context_preview:

```python
def _default_source_traceability_metadata():
    return {
        "schema_version": "button2.source_traceability.v1",
        "validation_status": "missing",
        "validation_issues": ["missing_source_traceability_metadata"],
        "total_sources": 0,
        "official_sources_count": 0,
        "research_sources_count": 0,
        "operator_sources_count": 0,
        "average_confidence_level": "uncertain",
        "corroboration_coverage": 0.0,
        "sources": [],
        "lineage_graph": {}
    }
```

Operator should provide explicit metadata. Defaults trigger fail-closed behavior (certification downgrade).

---

## Test Strategy

### Implementation Tests (~40-50 tests)
```
Coverage:
- Metadata presence and schema (button2.source_traceability.v1)
- Source type enum validation (official, research, operator)
- Source class mapping validation (tier_a, tier_b, tier_c)
- Confidence level enum validation (high, medium, low, uncertain)
- Citation completeness enum validation (complete, partial, minimal)
- Verification status enum validation (verified, unverified, contradicted)
- Required fields validation (source_id, source_type, source_class, title, confidence)
- URL format validation (if source_url provided)
- ISO 8601 date validation (if source_date provided)
- Cross-field validation (source_type → source_class mapping)
- Corroboration count validation (must match corroborating_source_ids)
- Lineage graph validation (all IDs must be valid)
- Fail-closed: invalid metadata → not_certified
- Fail-closed: missing metadata → not_certified
- Safety flags preserved (preview_only, pdf_generation_performed, etc.)
```

### Smoke Tests (~10-15 tests)
```
Coverage:
- All 6 metadata layers coexist (typography + hierarchy + page-breaks + charts + hfw + source_traceability)
- All schema versions present
- Fail-closed behavior preserved across all layers
- No duplicate metadata sections
- All validation QA rows present
- CSS display:none applied
- Safety flags unchanged
- Prior layer integrity preserved
```

### Regression Tests (Prior Layers)
- All 189 existing tests continue to pass
- Expected: ~230-250 tests total after source_traceability implementation

---

## Implementation Order

### Step 1: Add to Composition Entry Point
- Add source traceability constants and enums
- Add `_default_source_traceability_metadata()`
- Add `_validate_source_traceability_metadata()`
- Add `_source_traceability_payload()`
- Add hidden HTML section
- Add QA footer rows
- Integrate fail-closed logic

### Step 2: Create Implementation Tests
- 40-50 tests covering all contracts

### Step 3: Run Regression
- Verify all 189 prior tests still pass
- Verify new 40-50 tests pass

### Step 4: Create Smoke Tests
- 10-15 tests verifying coexistence with all prior layers

### Step 5: Lock Implementation
- Git commit + tag: button2-customer-pdf-source-traceability-implementation-v1

### Step 6: Create Final Handoff
- Docs-only handoff document
- Git commit + tag: button2-customer-pdf-source-traceability-final-handoff-v1

---

## Next Layer Design (After Handoff)

After source traceability is implemented and locked, consider next visual-polish layer:

### Option 1: Fight Profile Visual Layer
- Fighter name/image/record prominence
- Matchup visual indicators
- Fighting style classifications
- Historical performance charts (visual metadata)

### Option 2: Analysis Depth Indicators
- Section depth classifications
- Evidence strength indicators
- Risk/uncertainty signals
- Recommendation confidence levels

### Option 3: Temporal/Recency Layer
- Source age indicators
- Data freshness badges
- Historical data lineage
- Update timestamps

---

## Design Lock Criteria

Before proceeding to implementation, this design document should satisfy:

- ✅ All contracts clearly defined (source block structure, validation rules, HTML embedding)
- ✅ Enum values exhaustive and non-overlapping
- ✅ Default metadata generation deterministic
- ✅ Fail-closed behavior specified
- ✅ No renderer changes required
- ✅ No approval logic changes required
- ✅ No file-write behavior changes required
- ✅ Safety invariants preserved
- ✅ Test strategy clearly specified
- ✅ Implementation order unambiguous

---

## Compliance Checklist

- ✅ Metadata-first design
- ✅ Non-intrusive (composition-only)
- ✅ Fail-closed semantics
- ✅ Renderer-agnostic
- ✅ No renderer changes
- ✅ No approval changes
- ✅ No file-write changes
- ✅ No dashboard changes
- ✅ Safety flags preserved
- ✅ Prior layers unaffected
- ✅ Test strategy defined
- ✅ Implementation order clear
- ✅ Enum contracts exhaustive
- ✅ Validation contracts strict
- ✅ Default generation deterministic

---

## Sign-Off

**Design Phase**: button2-customer-pdf-source-traceability-visual-layer-design-v1  
**Date**: 2026-05-17  
**Status**: READY FOR DESIGN REVIEW  

Design review required before implementation begins.
