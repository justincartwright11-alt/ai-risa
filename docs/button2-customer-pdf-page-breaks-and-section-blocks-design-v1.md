# Button 2: Customer PDF Page Breaks and Section Blocks Design v1

**Status:** Design-Only (No Implementation)
**Date:** May 17, 2026
**Design Lock Candidate:** Ready for implementation review
**Governance:** Design page breaks before changing composition behavior.

---

## 1. Purpose

Define the next visual-polish layer for Button 2 customer PDFs:

- page-break rules,
- atomic section-block behavior,
- widow/orphan prevention,
- section-block metadata contracts.

This slice is design-only and does not change renderer behavior, route behavior, approval logic, output-path resolution, file-write behavior, dashboard behavior, or delivery workflow.

---

## 2. Core Rule (Locked)

```
Design page breaks before changing composition behavior.
No renderer changes yet.
No file-write behavior changes.
No output-path changes.
No dashboard changes.
```

Interpretation:
- This slice defines constraints and metadata contracts only.
- Composition changes are deferred to `button2-customer-pdf-page-breaks-and-section-blocks-implementation-v1`.
- Any implementation must remain inside the already-locked render-gate envelope.

---

## 3. Locked Foundation This Design Depends On

This design is constrained by already-locked slices:

- Route render-gate integration (`7b408f4`)
- Visual polish roadmap design review (`834ea7e`)
- Typography token scaffold (`3d257b5`)
- Typography implementation (`ec71cc7`)
- Page hierarchy design (`a4660e8`)
- Page hierarchy implementation (`a3d11c3`)
- Page hierarchy smoke (`0cdfa61`)

Non-negotiable inherited constraints:
- Gate 2 approval remains first in execution path.
- Output path remains server-derived by existing resolver.
- No partial writes; write occurs only after all prior stages pass.
- No renderer replacement or custom rendering path.
- No dashboard/delivery expansion.

---

## 4. Section-Block Model

### 4.1 Atomic Section Blocks

Each report section is modeled as an atomic block candidate with break policy metadata.

Required block categories:

- `report_identity_block`
- `fighter_context_block`
- `matchup_signal_block`
- `analysis_block`
- `sources_calibration_block`
- `footer_metadata_block`

Each block declares:

- `break_policy`: `keep_together` | `allow_internal_break` | `split_by_chunk`
- `min_lines_after_header`: integer (default 2)
- `min_space_for_chart_in`: numeric inches (default 1.0)
- `continuation_header_required`: bool

### 4.2 Block Priority Rules

- Report identity block must remain intact at the report top.
- Matchup signal block has elevated keep-together priority when chart height is within threshold.
- Sources/calibration block may split by chunk when source count exceeds threshold.
- Footer metadata block is always page-local and never moved ahead of primary content.

---

## 5. Page-Break Rule Set

### 5.1 Baseline Break Policies

- `report_identity_block`: `keep_together`
- `fighter_context_block`: `keep_together` if compact; otherwise move whole block to next page
- `matchup_signal_block`: `keep_together` if text + chart fit threshold; otherwise move chart to next page with continuation marker
- `analysis_block`: `allow_internal_break` at approved subsection boundaries only
- `sources_calibration_block`: `split_by_chunk` by source chunk size

### 5.2 Approved Break Boundaries

Allowed break boundaries:

- between H1 sections,
- between approved H2 subgroup boundaries in analysis,
- between source chunks in sources/calibration.

Forbidden break boundaries:

- directly after an H1/H2 header when required trailing lines are unavailable,
- inside a chart/table render unit,
- between a claim and its immediate citation line.

### 5.3 Source Chunking Rule

For `sources_calibration_block`:

- keep on one page when source count <= 20,
- split by chunks of 10 entries when source count > 20,
- repeat section header on continuation pages.

---

## 6. Widow and Orphan Prevention Rules

Required safeguards:

- No section header at page bottom unless at least 2 body lines follow.
- No single list item orphaned at top of next page.
- No chart/table alone at page bottom with less than 1.0 inch of available vertical space.
- No isolated caption detached from associated chart/table.

Resolution order when a violation is detected:

1. move violating block to next page,
2. if allowed, split at next approved boundary,
3. if still unresolved, mark metadata issue and fail certification status to `not_certified`.

---

## 7. Page-Break and Section-Block Metadata Contract

### 7.1 Metadata Shape (Design Contract)

Implementation must emit deterministic, renderer-agnostic metadata:

```json
{
  "schema_version": "button2.page_breaks_and_blocks.v1",
  "page_breaks": [
    {
      "break_id": "pb_001",
      "trigger_block_id": "matchup_signal",
      "trigger_section": "Matchup Signal",
      "overflow_reason": "chart_height",
      "previous_page_content_height_in": 8.2,
      "atomic_unit_preserved": true,
      "widow_orphan_rule_applied": false
    }
  ],
  "section_blocks": [
    {
      "block_id": "fighter_a_context",
      "role": "fighter_context_block",
      "break_policy": "keep_together",
      "can_split": false,
      "continuation_header_required": false
    }
  ]
}
```

### 7.2 Required Page-Break Fields

Per break event:

- `break_id`
- `trigger_block_id`
- `trigger_section`
- `overflow_reason` (`section_size` | `chart_height` | `widow_rule` | `source_chunking`)
- `previous_page_content_height_in`
- `atomic_unit_preserved` (bool)
- `widow_orphan_rule_applied` (bool)

### 7.3 Required Section-Block Fields

Per section block:

- `block_id`
- `role`
- `break_policy`
- `can_split` (bool)
- `continuation_header_required` (bool)

Optional but recommended:

- `chunk_size`
- `approved_break_boundaries`
- `estimated_block_height_in`

---

## 8. Validation Rules

The next implementation slice must validate:

- All block roles belong to locked role set.
- All break policies belong to allowed policy set.
- All break events reference known block IDs.
- `atomic_unit_preserved` is true for `keep_together` blocks.
- `widow_orphan_rule_applied` is true when widow/orphan prevention triggers.
- Source chunking rules match configured threshold and chunk size.

Failure semantics:

- Missing/invalid page-break metadata must fail closed to `not_certified`.
- Failure must not bypass approval gates or alter file-write behavior.

---

## 9. Non-Goals (Explicit)

This design slice does not authorize:

- renderer updates, custom engine behavior, or alternate render path,
- route flow changes or approval logic changes,
- output-path derivation changes,
- file-write behavior changes,
- dashboard UI changes,
- delivery workflow changes,
- visual redesign beyond documented block/break contracts.

---

## 10. Implementation Guardrails For Next Slice

When implementing `button2-customer-pdf-page-breaks-and-section-blocks-implementation-v1`:

- Keep changes composition-layer only.
- Prefer non-visual metadata markers first; introduce minimal CSS/page-break hints only where needed.
- Preserve typography and hierarchy contracts already locked.
- Keep renderer-agnostic behavior and no new external assets.
- Preserve legacy fixture compatibility where safe.

Recommended test scope:

- page-break policy mapping tests,
- atomic block preservation tests,
- widow/orphan prevention tests,
- metadata completeness and validation tests,
- fail-closed certification downgrade tests,
- regression tests proving no route/path/write/approval behavior changes.

---

## 11. Design Lock Checklist

Design is lock-ready when all statements below are true:

- [x] Atomic section-block model is defined.
- [x] Break policy set is defined.
- [x] Allowed/forbidden break boundaries are defined.
- [x] Widow/orphan prevention rules are defined.
- [x] Page-break metadata schema is defined.
- [x] Validation/failure semantics are defined.
- [x] Non-goals are explicit.
- [x] Inherited governance constraints are preserved.

---

## 12. Handoff Statement

This document locks page-break and section-block design contracts for Button 2 customer PDFs and authorizes the next slice to implement composition-layer metadata and validation only, within the existing render-gate, output-path, and file-write safety envelope.

No implementation is included in this slice.
