# Button 2: Customer PDF Page Hierarchy Design v1

**Status:** Design-Only (No Implementation)
**Date:** May 17, 2026
**Design Lock Candidate:** Ready for implementation review
**Governance:** Hierarchy before layout. No renderer changes. No PDF behavior changes.

---

## 1. Purpose

Define the page hierarchy upgrade for Button 2 customer-facing PDFs, including section levels, visual grouping, page-block roles, and hierarchy metadata.

This slice is design-only and intentionally does not change HTML composition behavior, renderer behavior, route behavior, file-write behavior, or dashboard behavior.

---

## 2. Core Rule (Locked)

```
Hierarchy before layout.
No page redesign yet.
No renderer changes yet.
No PDF behavior changes yet.
```

Interpretation:
- This slice defines hierarchy contracts only.
- Styling mechanics beyond already-locked typography are deferred to implementation slices.
- Page-break mechanics are deferred to the dedicated page-break slice.

---

## 3. Locked Foundation This Design Depends On

This design is constrained by already-locked slices:

- Route render-gate integration (`7b408f4`)
- Visual polish roadmap design review (`834ea7e`)
- Typography token scaffold (`3d257b5`)
- Typography CSS application (`ec71cc7`)

Non-negotiable inherited constraints:
- Gate 2 approval remains first in route execution.
- Output path remains server-derived via existing resolver.
- No partial writes; write occurs only after prior stages succeed.
- No dashboard surface or delivery workflow expansion.

---

## 4. Hierarchy Model

### 4.1 Section Levels

The report hierarchy is represented as semantic levels and roles:

- **H0:** Report identity
  - Report title
  - Event/date/location line
  - Approval/timestamp metadata
- **H1:** Primary report sections
  - Fighter A Context
  - Fighter B Context
  - Matchup Signal
  - Detailed Analysis
  - Sources and Calibration
- **H2:** Subsections under each H1
  - Record Summary
  - Style Notes
  - Injury Notes
  - Key Implications
  - Confidence Bound
  - Source lists
- **Body:** Paragraph/list/chart-adjacent explanatory content
- **Meta:** Footer-level provenance and versioning elements

### 4.2 Order Contract

Canonical order for top-level sections:

1. Fighter A Context
2. Fighter B Context
3. Matchup Signal
4. Detailed Analysis
5. Sources and Calibration

Design intent:
- Reader sees fighter grounding before conclusions.
- Decision signal appears before long-tail detail.
- Sources and calibration close the report for auditability.

---

## 5. Page-Block Roles

Each hierarchy unit maps to a page-block role for later implementation.

- `report_identity_block` (H0)
- `fighter_context_block` (H1/H2/body)
- `matchup_signal_block` (H1/H2/body/chart)
- `analysis_block` (H1/H2/body)
- `sources_calibration_block` (H1/H2/body/meta)
- `footer_metadata_block` (meta)

Role semantics:
- Roles describe meaning and grouping, not final layout geometry.
- Roles are used to drive future page-break and QA metadata logic.

---

## 6. Visual Grouping Contracts (Design Intent Only)

This section specifies semantic grouping targets to be implemented later without redesign.

- **Operator Signal Group:** Matchup signal and confidence content grouped as one coherent block.
- **Fighter Context Group:** Per-fighter content grouped with local subsection continuity.
- **Analysis Group:** Deep-dive sections grouped for scanability and progressive detail.
- **Sources Group:** Citations and calibration grouped as a distinct audit band.

Important:
- No new visual ornamentation is introduced in this design slice.
- Group definitions exist to prevent ad-hoc styling in future slices.

---

## 7. Hierarchy Metadata Contract

### 7.1 Metadata Shape (Design Contract)

Implementation slice must emit a hierarchy metadata object that is deterministic and renderer-agnostic.

```json
{
  "schema_version": "button2.page_hierarchy.v1",
  "report_id": "<fight_id>",
  "blocks": [
    {
      "block_id": "fighter_a_context",
      "role": "fighter_context_block",
      "level": "H1",
      "title": "Fighter A Context",
      "sequence": 1,
      "children": [
        {"level": "H2", "title": "Record Summary", "sequence": 1},
        {"level": "H2", "title": "Style Notes", "sequence": 2},
        {"level": "H2", "title": "Injury Notes", "sequence": 3}
      ]
    }
  ]
}
```

### 7.2 Required Metadata Fields

Per block:
- `block_id` (stable identifier)
- `role` (from allowed role set)
- `level` (H0/H1/H2/Body/Meta)
- `title` (human-readable)
- `sequence` (strict ordering index)

Optional but recommended in implementation:
- `parent_block_id`
- `content_kind` (text/list/chart/table)
- `estimated_density` (low/medium/high)

### 7.3 Validation Rules

- Levels must be one of: H0, H1, H2, Body, Meta.
- Roles must be from the locked role set.
- Sequence must be contiguous and unique per sibling group.
- H2 blocks must have an H1 parent context.
- Sources and Calibration must appear after Detailed Analysis.

---

## 8. Non-Goals (Explicit)

This design slice does not authorize any of the following:

- Renderer updates or custom renderer behavior
- New page-break algorithms
- Template restructuring outside hierarchy annotations
- Route logic changes
- Approval or authorization changes
- Output path logic changes
- File write behavior changes
- Dashboard UI changes
- Delivery workflow changes

---

## 9. Implementation Guardrails For Next Slice

When implementing `button2-customer-pdf-page-hierarchy-implementation-v1`:

- Keep existing HTML structure intact where possible; add hierarchy classes/attributes minimally.
- Use already-locked typography tokens only; do not introduce a new typography system.
- Emit hierarchy metadata deterministically from existing report context.
- Preserve all prior test behavior; add focused hierarchy tests.
- Keep implementation renderer-agnostic and CSS-only.

Target test scope for next slice:
- Hierarchy level assignment tests
- Section order contract tests
- Block role mapping tests
- Metadata validation tests
- Regression tests proving no route/path/approval/file-write behavior changes

---

## 10. Design Lock Checklist

Design is lock-ready when all statements below are true:

- [x] Hierarchy levels are defined and unambiguous.
- [x] Page-block roles are defined and scoped.
- [x] Canonical top-level section order is defined.
- [x] Metadata schema contract is defined.
- [x] Validation rules are defined.
- [x] Non-goals are explicit.
- [x] Inherited governance constraints are preserved.

---

## 11. Handoff Statement

This document locks the page hierarchy design for Button 2 customer PDFs and authorizes the next slice to implement hierarchy semantics only, within the already-locked render-gate and typography envelope.

No implementation is included in this slice.
