# Button 2: Customer PDF Header Footer Watermark Design v1

**Status:** Design-Only (No Implementation)
**Date:** May 17, 2026
**Design Lock Candidate:** Ready for implementation review
**Governance:** Design first. No header/footer rendering yet. No renderer changes yet.

---

## 1. Purpose

Define the next visual-polish layer for Button 2 customer PDFs covering:

- report header contracts,
- footer/page-number contracts,
- confidentiality/status label contracts,
- brand watermark rules,
- source and QA footer placement rules,
- metadata and validation contracts for header/footer/watermark behavior.

This slice is design-only and does not change renderer behavior, output behavior, approval logic, output-path logic, file-write behavior, dashboard behavior, or delivery workflow.

---

## 2. Core Rule (Locked)

```
Design first.
No header/footer rendering yet.
No renderer changes yet.
No PDF output behavior changes.
No file-write behavior changes.
No dashboard changes.
No delivery changes.
```

Interpretation:
- This slice defines contracts and validation rules only.
- Rendering and visual placement implementation is deferred to:
  `button2-customer-pdf-header-footer-watermark-implementation-v1`.
- Future implementation must remain inside existing render-gate and write-path controls.

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
- Page breaks and section-blocks design (`2231fc1`)
- Page breaks and section-blocks implementation (`7919a93`)
- Page breaks and section-blocks smoke (`acd90f0`)
- Chart and scenario-tree design (`0997cfb`)
- Chart and scenario-tree implementation (`c940dc6`)
- Chart and scenario-tree smoke (`3377e92`)

Inherited non-negotiables:
- Gate 2 approval remains first in route path.
- Output path remains server-derived only.
- No partial writes and no alternate write path.
- No renderer swap or custom rendering path.
- No dashboard/delivery expansion.

---

## 4. Header Contract

### 4.1 Header Content Model

Header metadata must support:

- `report_title`
- `event_name`
- `event_date`
- `report_generated_timestamp`
- `status_label` (optional)
- `confidentiality_label` (optional)

### 4.2 Header Visibility Rules

- Header intended on every content page by default.
- First page may use title-forward variant (header optional) when `title_page_mode=true`.
- Header must never obscure body content area.

### 4.3 Header Readability Contract

- Target typography band: equivalent 11-12pt for primary line.
- Separator line allowed beneath header metadata.
- Header labels must remain text-selectable in HTML/PDF path (no image-only substitution in this slice).

---

## 5. Footer Contract

### 5.1 Footer Content Model

Footer metadata must support:

- `page_number`
- `page_count`
- `operator_label`
- `generated_timestamp`
- `version_label` (optional)
- `source_summary_anchor` (optional)
- `qa_summary_anchor` (optional)

### 5.2 Footer Rules

- Footer intended on every content page.
- Page numbering format contract: `Page N of M`.
- Footer should remain isolated from body block flow.
- Footer metadata must never replace safety/validation rows in core meta-footer content.

---

## 6. Status and Confidentiality Labels

### 6.1 Status Label Set

Allowed `status_label` values:

- `DRAFT`
- `FINAL`
- `INTERNAL_REVIEW`

### 6.2 Confidentiality Label Set

Allowed `confidentiality_label` values:

- `PUBLIC`
- `CONFIDENTIAL`
- `STRICTLY_CONFIDENTIAL`

### 6.3 Placement Rules

- Status/confidentiality labels belong to header metadata zone.
- Labels are metadata-first in this slice (annotation-only).
- Label presence must be validation-aware and auditable in emitted metadata.

---

## 7. Watermark Contract

### 7.1 Watermark Model

Watermark metadata must support:

- `watermark_enabled` (bool)
- `watermark_type` (`none` | `draft` | `confidential`)
- `watermark_text`
- `watermark_opacity`
- `watermark_angle`
- `watermark_position`

### 7.2 Watermark Rules

- `watermark_type=none` requires `watermark_enabled=false`.
- `watermark_type=draft` requires text token `DRAFT`.
- `watermark_type=confidential` requires text token `CONFIDENTIAL`.
- Opacity must remain in safe range (0.05 to 0.20 target contract).
- Watermark must never be defined as content-block replacement.

### 7.3 Non-Blocking Rule

In this design slice, watermark is metadata only. Actual rendered watermark behavior is deferred.

---

## 8. Source and QA Footer Placement Contract

### 8.1 Source Summary Placement

Footer metadata may include summary anchors:

- `official_records_count`
- `research_sources_count`
- `ai_analysis_sections_count`
- `operator_overrides_count`

### 8.2 QA Summary Placement

Footer metadata may include summary anchors:

- `visual_certification_status`
- `hierarchy_validation_status`
- `page_breaks_validation_status`
- `chart_scenario_validation_status`
- `header_footer_watermark_validation_status`

### 8.3 Separation Rule

Source/QA summaries in footer metadata must not alter canonical section order or replace full source traceability sections in body flow.

---

## 9. Header/Footer/Watermark Metadata Contract

### 9.1 Metadata Shape (Design Contract)

Implementation must emit deterministic metadata with schema:

```json
{
  "schema_version": "button2.header_footer_watermark.v1",
  "header": {
    "report_title": "AI-RISA Premium Fight Report",
    "event_name": "Sample Event",
    "event_date": "2026-05-17",
    "status_label": "DRAFT",
    "confidentiality_label": "CONFIDENTIAL"
  },
  "footer": {
    "page_number_format": "Page {n} of {m}",
    "operator_label": "Operator",
    "generated_timestamp": "2026-05-17T12:00:00Z"
  },
  "watermark": {
    "watermark_enabled": true,
    "watermark_type": "draft",
    "watermark_text": "DRAFT",
    "watermark_opacity": 0.12,
    "watermark_angle": 45
  }
}
```

### 9.2 Required Fields

- `schema_version`
- `header.report_title`
- `footer.page_number_format`
- `watermark.watermark_enabled`
- `watermark.watermark_type`

Optional but recommended:

- `header.status_label`
- `header.confidentiality_label`
- `footer.source_summary_anchor`
- `footer.qa_summary_anchor`

---

## 10. Validation Rules

The next implementation slice must validate:

- header/footer objects are present and dict-shaped,
- label enums are in allowed sets,
- watermark type/text coupling rules are valid,
- watermark opacity in accepted bounds,
- page number format token includes both `{n}` and `{m}` placeholders,
- source/QA footer anchors do not conflict with existing metadata keys.

Failure semantics:

- missing/invalid header-footer-watermark metadata must set validation status to `missing` or `invalid`,
- visual certification must downgrade to `not_certified`,
- no approval/path/write behavior may be altered.

---

## 11. Non-Goals (Explicit)

This design slice does not authorize:

- real header/footer rendering logic,
- watermark drawing/painting in renderer,
- renderer behavior changes,
- route or approval logic changes,
- output path changes,
- file-write behavior changes,
- dashboard UI changes,
- delivery workflow changes.

---

## 12. Implementation Guardrails For Next Slice

When implementing `button2-customer-pdf-header-footer-watermark-implementation-v1`:

- Metadata-first and annotation-first approach only.
- Keep renderer-agnostic output and inline-safe HTML only.
- Preserve prior typography/hierarchy/page-break/chart metadata contracts.
- Preserve all safety flags and no-side-effect invariants.
- Keep legacy fixture compatibility where safe.

Recommended test scope:

- metadata presence/schema tests,
- label enum validation tests,
- watermark coupling/opacity validation tests,
- page number format validation tests,
- fail-closed downgrade tests,
- regression stack for typography/hierarchy/page-break/chart/composition.

---

## 13. Design Lock Checklist

Design is lock-ready when all statements below are true:

- [x] Header content contract defined.
- [x] Footer/page-number contract defined.
- [x] Status/confidentiality label rules defined.
- [x] Watermark metadata contract defined.
- [x] Source/QA footer placement rules defined.
- [x] Validation rules and fail-closed semantics defined.
- [x] Non-goals explicit.
- [x] Inherited safety constraints preserved.

---

## 14. Handoff Statement

This document locks header/footer/watermark design contracts for Button 2 customer PDFs and authorizes the next slice to implement metadata and composition annotations only, without renderer or behavior-surface changes.

No implementation is included in this slice.
