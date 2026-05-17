# Button 2 Visual Intelligence Renderer — Metadata Bridge Final Handoff (v1)

**Slice:** `button2-visual-intelligence-renderer-metadata-bridge-final-handoff-v1`
**Date:** 2026-05-17
**Status:** LOCKED — docs-only handoff, no implementation changes

---

## Purpose

This document freezes the Button 2 visual QA metadata bridge before opening any real renderer instrumentation or layout-proof implementation. It records what has been built, locked, and validated, and establishes the exact boundary between what is provably safe now and what requires the next instrumentation design pass.

---

## What Was Built

### Slice Chain (in order)

| Slice | Commit | Tag | Purpose |
|-------|--------|-----|---------|
| Acceptance rules scaffold | — | `button2-visual-intelligence-renderer-scaffold-v1` | Locked acceptance rules and initial test scaffold |
| Sample contract + adapter | — | locked | Sample QA contract fixture + adapter to validate renderer output |
| Compatibility layer | — | locked | Maps current report-context output → QA contract shape |
| Compatibility smoke proof | — | locked | Fail-closed gap evidence: adapter rejects unavailable overlap/off-page proof |
| Metadata marker design | — | locked | Design doc: required marker fields and certification logic |
| Metadata markers preview | `1d5a0e1` | `button2-visual-intelligence-renderer-contract-metadata-markers-preview-v1` | Preview-level metadata markers added to report-context output |
| Metadata adapter integration | `b8f90c9` | `button2-visual-intelligence-renderer-contract-metadata-adapter-integration-v1` | Compatibility adapter reads real marker fields, source_traceability bug fixed |

---

## Current QA Bridge State

### Metadata Markers in Report-Context Output

All markers are present in `operator_dashboard/button2_dossier_handoff_report_context_preview.py` → `build_button2_dossier_handoff_report_context_preview()`:

| Marker | Field | Status |
|--------|-------|--------|
| Page block boundaries | `page_block_boundaries` | Present — preview-level, layout-inferred |
| Hierarchy markers | `hierarchy_markers` | Present — preview-level, structure-inferred |
| Source traceability | `source_traceability` | Present — reads real `source_context_kind` |
| Overlap proof | `overlap_proof` | Present — `"unavailable"` |
| Off-page text proof | `off_page_text_proof` | Present — `"unavailable"` |
| Visual certification status | `visual_certification_status` | Present — `"not_certified"` |

### Compatibility Adapter Behavior

`operator_dashboard/button2_visual_intelligence_renderer_contract_compatibility_layer_v1.py` — `map_report_context_to_visual_intelligence_contract()`:

- Reads `page_block_boundaries` → maps to `visual_blocks`
- Reads `hierarchy_markers` → maps to `hierarchy`
- Reads `source_traceability` → maps to `source_trace_block.sources`
- Reads `overlap_proof` — `"unavailable"` → `no_overlap = False`
- Reads `off_page_text_proof` — `"unavailable"` → `no_off_page_text = False`
- Reads `visual_certification_status` → passes through as `"not_certified"`
- **Fails closed:** `adapt_renderer_output_to_contract()` raises `ValueError` because `no_overlap` and `no_off_page_text` are both `False`

### Test Coverage

17 tests passing across three test files:

- `test_button2_visual_intelligence_renderer_contract_metadata_markers_preview_v1.py` — 2 tests
- `test_button2_visual_intelligence_renderer_contract_compatibility_smoke_v1.py` — 6 tests
- `test_button2_visual_intelligence_renderer_contract_metadata_adapter_integration_v1.py` — 9 tests

---

## What Is NOT Certified

The following remain explicitly unavailable and uncertified:

| Item | Status | Reason |
|------|--------|--------|
| Overlap proof | `unavailable` | Requires renderer instrumentation — not yet designed |
| Off-page text proof | `unavailable` | Requires renderer instrumentation — not yet designed |
| Visual certification | `not_certified` | Cannot certify while overlap/off-page proof is unavailable |
| PDF layout safety | Unknown | No layout analysis has been performed |

---

## Safety Lock

The entire bridge was built under these constraints, which remain in effect:

- No PDFs generated
- No files written
- No renderer layout changes
- No dashboard changes
- No report-generation behavior changes
- No fake visual certification

---

## Boundary

**Everything up to and including this handoff is provably safe** — all metadata markers are preview-level and correctly marked unavailable/not_certified. The QA chain is a test-only artifact; it does not affect production output.

**What comes next requires a new design slice** before any implementation:

> `button2-visual-intelligence-overlap-offpage-proof-instrumentation-design-v1`

That slice must design how real overlap and off-page text proof can be produced (from the renderer or a post-render analysis step) without changing the visual layout of any PDF output.

Only after that design is locked may real instrumentation be implemented.
