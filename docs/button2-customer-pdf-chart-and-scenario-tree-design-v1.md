# Button 2: Customer PDF Chart and Scenario Tree Design v1

**Status:** Design-Only (No Implementation)
**Date:** May 17, 2026
**Design Lock Candidate:** Ready for implementation review
**Governance:** Design first. No chart rendering yet. No renderer changes yet.

---

## 1. Purpose

Define the next visual-polish layer for Button 2 customer PDFs covering:

- tactical chart contracts,
- scenario tree contracts,
- method pathway visual contracts,
- round-control visual contracts,
- risk/collapse marker contracts,
- chart metadata and validation rules.

This slice is design-only and does not change composition execution behavior, renderer behavior, approval behavior, output paths, file-write behavior, dashboard behavior, or delivery workflow.

---

## 2. Core Rule (Locked)

```
Design first.
No chart rendering yet.
No renderer changes yet.
No PDF output behavior changes.
No file-write behavior changes.
No dashboard changes.
No delivery changes.
```

Interpretation:
- This slice locks visual/chart contracts and metadata shape only.
- Rendering implementation is deferred to `button2-customer-pdf-chart-and-scenario-tree-implementation-v1`.
- Any future implementation must remain inside existing render-gate constraints.

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

Inherited non-negotiables:
- Gate 2 approval remains first in route path.
- Output path remains server-derived only.
- No partial writes and no alternate write path.
- No renderer swap or custom engine path.
- No dashboard/delivery surface expansion.

---

## 4. Chart System Model

### 4.1 Chart Types (Contract-Only)

The chart layer supports these logical types:

1. `scenario_tree`
2. `method_pathway`
3. `round_control`
4. `risk_collapse_markers`
5. `comparison_chart` (future-compatible placeholder)

### 4.2 Chart Unit Semantics

Each chart unit is a semantic report component with:

- `chart_id`
- `chart_type`
- `title`
- `intent`
- `source_citations`
- `placement_block_id`
- `size_contract`
- `print_readability_contract`

A chart unit is metadata-first and renderer-agnostic.

---

## 5. Scenario Tree Contract

### 5.1 Required Nodes

`scenario_tree` must define:

- `root_node` (fight baseline state)
- `branch_nodes` (at least 2)
- `terminal_nodes` (at least 2)
- `confidence_band` per terminal node

### 5.2 Branch Rules

- Branch labels must describe tactical trigger conditions.
- Terminal labels must describe outcome pathways, not vague conclusions.
- Each branch/terminal must carry at least one citation reference.
- Confidence must be represented as bounded interval (e.g. 58-66%), not single-point certainty.

### 5.3 Readability Contract

- Max intended display width: 6.5in
- Max intended display height: 3.5in
- Node label min size target: equivalent 9-10pt print readability
- Branch stroke target: equivalent 1-2pt

---

## 6. Method Pathway Contract

`method_pathway` captures likely finish or decision pathways.

Required fields:

- `pathway_id`
- `method_type` (`ko_tko`, `submission`, `decision`, `attritional_breakdown`)
- `trigger_factors` (list)
- `counter_factors` (list)
- `evidence_links` (list)
- `confidence_band`

Rules:
- Every method pathway must include at least one trigger and one counter factor.
- Confidence band required; missing band marks pathway metadata invalid.
- At least one evidence reference per method pathway.

---

## 7. Round-Control Visual Contract

`round_control` captures tempo/initiative expectations by round windows.

Required fields:

- `window_id`
- `round_range` (e.g. `R1-R2`, `R3-R5`)
- `control_expectation` (`fighter_a`, `fighter_b`, `swing`, `contested`)
- `dominance_signal` (`low`, `medium`, `high`)
- `evidence_links`

Rules:
- Round ranges must be non-overlapping in sequence.
- Control expectation and dominance signal both required.
- Evidence links required for each round window.

---

## 8. Risk/Collapse Marker Contract

`risk_collapse_markers` highlights high-impact failure or collapse pathways.

Required fields:

- `marker_id`
- `risk_type` (`gas_tank_drop`, `damage_accumulation`, `defensive_breakdown`, `pace_collapse`)
- `trigger_window`
- `severity` (`watch`, `elevated`, `critical`)
- `mitigation_note`
- `evidence_links`

Rules:
- Severity must use locked enum values.
- Critical markers require explicit mitigation note.
- Every marker requires evidence references.

---

## 9. Chart Placement and Section Integration

Charts are placed by metadata pointer only in this slice.

Allowed placement block roles:

- `matchup_signal_block`
- `analysis_block`

Forbidden placement:

- `report_identity_block`
- `footer_metadata_block`

Integration rules:
- Chart units attach to existing section-block metadata by `placement_block_id`.
- Chart units must not alter canonical section ordering contract.
- Chart units must not bypass page-break policies.

---

## 10. Chart and Scenario Metadata Contract

### 10.1 Metadata Shape (Design Contract)

Implementation must emit deterministic metadata with schema:

```json
{
  "schema_version": "button2.chart_and_scenario.v1",
  "charts": [
    {
      "chart_id": "chart_scenario_tree_001",
      "chart_type": "scenario_tree",
      "title": "Primary Scenario Pathways",
      "intent": "Explain major tactical branches",
      "placement_block_id": "matchup_signal",
      "size_contract": {"max_width_in": 6.5, "max_height_in": 3.5},
      "print_readability_contract": {
        "min_label_pt": 9,
        "min_stroke_pt": 1,
        "min_contrast_ratio": 4.5
      },
      "source_citations": ["SRC-001", "SRC-002"]
    }
  ],
  "scenario_tree": {
    "root_node": "baseline",
    "branches": ["pace_advantage", "distance_control"],
    "terminal_nodes": ["late_finish", "decision_path"],
    "confidence_band": "58-66%"
  }
}
```

### 10.2 Required Chart Fields

Per chart unit:

- `chart_id`
- `chart_type`
- `title`
- `placement_block_id`
- `size_contract.max_width_in`
- `size_contract.max_height_in`
- `print_readability_contract.min_label_pt`
- `source_citations`

### 10.3 Validation Rules

- `chart_type` must be in locked chart type set.
- `placement_block_id` must map to known allowed block roles.
- `source_citations` must be non-empty.
- `size_contract` must not exceed print bounds (6.5in x 4.0in max by type).
- `print_readability_contract.min_label_pt` must be >= 9.
- Scenario tree must include root, branch nodes, terminal nodes, and confidence band.

---

## 11. Fail-Closed Semantics

When chart/scenario metadata is missing or invalid:

- validation status must be `missing` or `invalid`,
- visual certification must downgrade to `not_certified`,
- composition may still return HTML preview (no renderer/file-write side effects),
- no bypass of approval or output-path controls.

---

## 12. Non-Goals (Explicit)

This design slice does not authorize:

- actual chart rendering engines or drawing primitives,
- renderer changes or upgrades,
- page geometry extraction changes,
- route or approval logic changes,
- output-path changes,
- file-write behavior changes,
- dashboard UI changes,
- delivery workflow changes.

---

## 13. Implementation Guardrails For Next Slice

When implementing `button2-customer-pdf-chart-and-scenario-tree-implementation-v1`:

- Keep implementation metadata/annotation first.
- Keep renderer-agnostic output and inline-safe HTML only.
- Reuse existing section-block and hierarchy metadata contracts.
- Preserve typography class application.
- Preserve all no-side-effect flags and route-level invariants.

Recommended test scope:

- chart metadata presence and schema tests,
- scenario tree field validation tests,
- placement mapping tests,
- size/readability contract tests,
- fail-closed downgrade tests,
- regression tests for typography/hierarchy/page-break stacks.

---

## 14. Design Lock Checklist

Design is lock-ready when all statements below are true:

- [x] Chart type set is defined.
- [x] Scenario tree contract is defined.
- [x] Method pathway contract is defined.
- [x] Round-control visual contract is defined.
- [x] Risk/collapse marker contract is defined.
- [x] Placement rules are defined.
- [x] Metadata schema and validation rules are defined.
- [x] Fail-closed semantics are defined.
- [x] Non-goals are explicit.
- [x] Inherited safety constraints are preserved.

---

## 15. Handoff Statement

This document locks chart and scenario-tree design contracts for Button 2 customer PDFs and authorizes the next slice to implement metadata and composition annotations only, without renderer or behavior-surface changes.

No implementation is included in this slice.
