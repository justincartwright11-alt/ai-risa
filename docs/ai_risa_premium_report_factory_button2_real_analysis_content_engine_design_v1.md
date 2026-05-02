# AI-RISA Premium Report Factory - Button 2 Real Analysis Content Engine: Design v1

Date: 2026-05-02
Slice type: docs-only design
Scope: Button 2 only

## Problem

Button 2 export and download actions are now working, but generated PDF content is still mostly placeholder/unavailable text.

Observed PDF content gaps:
- Prediction unavailable
- Decision structure analysis unavailable
- Energy projection unavailable
- Fatigue analysis unavailable
- Mental condition profile unavailable
- Collapse trigger analysis unavailable
- Deception profile unavailable
- Round-by-round projection unavailable
- Scenario pathways unavailable

Current draft labeling is correct (`DRAFT ONLY - NOT CUSTOMER READY`), but content is not customer-usable.

## Goal

Design a real premium content engine for Button 2 so reports contain real AI-RISA analysis before customer-ready export is allowed.

## Hard Requirements

1. Button 2 must build report content before PDF export.

2. Content model must support all 14 premium sections:
- Cover Page
- Headline Prediction
- Executive Summary
- Matchup Snapshot
- Decision Structure
- Energy Use and Gas Tank Projection
- Fatigue Failure Points
- Mental Condition
- Collapse Triggers
- Deception and Unpredictability
- Round-by-Round Control Shifts
- Scenario Tree / Method Pathways
- Risk Warnings
- Operator Notes

3. Content source hierarchy:
- Source 1: existing prediction/report model record for the matchup
- Source 2: existing AI-RISA analysis/report JSON if available
- Source 3: operator-approved generated analyst draft
- Source 4: block customer PDF if no usable analysis exists

4. Saved queue fight must attempt analysis linkage by:
- fighter_a
- fighter_b
- normalized matchup_id
- event_name
- event_date
- source_reference

5. If an existing prediction/report record is found, map it into premium sections.

6. If no existing prediction/report record is found, customer PDF must be blocked unless operator explicitly chooses:
- Generate internal AI-RISA draft for review.

7. Internal AI-RISA draft must generate real section text using AI-RISA lenses:
- decision structure
- energy use
- fatigue failure points
- mental condition
- collapse triggers
- deception and unpredictability
- round-by-round control shifts
- scenario tree and method pathways

8. Internal draft remains:
- DRAFT ONLY - NOT CUSTOMER READY
- until operator reviews and approves it.

9. No customer_ready report may contain placeholder phrases including:
- unavailable
- insufficient data
- content will be enriched later
- prediction unavailable
- analysis unavailable

10. customer_ready requires:
- all 14 sections populated with real content
- no major unavailable placeholders
- operator approval before export
- report_quality_status = customer_ready

11. Button 2 UI must show:
- analysis source found / not found
- linked analysis record ID if found
- missing analysis sections
- customer_ready / draft_only / blocked_missing_analysis
- operator approval state

12. Add content preview before PDF export:
- headline prediction preview
- executive summary preview
- missing sections list
- approve customer export checkbox

13. Do not change Button 1.
14. Do not change Button 3.
15. Do not change result lookup.
16. Do not change learning/calibration.
17. Do not add billing.
18. Do not add uncontrolled writes.
19. Do not bypass operator approval.

## Proposed Design

### A) Content Engine Pipeline

Define a Button 2 content build stage before PDF export:

1. Normalize selected matchup identity and candidate lookup keys.
2. Resolve best available source via hierarchy (Source 1 -> Source 2 -> Source 3 -> Source 4).
3. Map resolved content into canonical 14-section premium schema.
4. Run section completeness and placeholder rejection checks.
5. Compute quality status (`customer_ready`, `draft_only`, `blocked_missing_analysis`).
6. Expose preview payload to UI before export confirmation.
7. Export PDF only after approval gate is satisfied for selected mode.

### B) Source Resolver Contract

For each selected matchup, return resolver metadata:
- analysis_source_status: `found` | `not_found`
- analysis_source_type: `model_record` | `analysis_json` | `generated_internal_draft` | `none`
- linked_analysis_record_id: string or empty
- linkage_keys_used: list
- linkage_confidence: `high` | `medium` | `low`

Resolver behavior:
- Prefer deterministic record linkage by normalized identifiers.
- If multiple candidates are found, use deterministic priority rules and emit warning.
- If no usable source is found and internal draft is not selected, return blocked state.

### C) Premium Section Mapper

Create a canonical mapping layer that guarantees the same section schema regardless of source.

Mapper responsibilities:
- Map source fields into all 14 required sections.
- Preserve section provenance metadata per section (which source populated it).
- Mark missing sections explicitly for UI preview and quality gating.
- Reject placeholder-only section text for customer-ready mode.

### D) Internal Draft Generator

When operator explicitly selects internal draft mode and no usable record is found:
- Generate real narrative content across all required analytical lenses.
- Populate premium sections with non-placeholder, structured analysis text.
- Mark output as `draft_only` and `customer_ready=false`.
- Stamp artifact text with `DRAFT ONLY - NOT CUSTOMER READY`.

Draft generation constraints:
- Must still honor operator approval gates.
- Must not auto-upgrade to customer_ready without review and approval.

### E) Quality Gate Rules

Customer export gate:
- Block if any required section missing.
- Block if placeholder phrase detector triggers on critical sections.
- Block if operator approval is not checked.

Draft export gate:
- Allow only when internal draft mode is explicitly selected.
- Require operator approval.
- Force `report_quality_status=draft_only`.

### F) Button 2 UI/UX Design Additions

Add pre-export content readiness panel per selected matchup:
- analysis source found/not found
- linked analysis record ID
- quality status
- missing sections
- headline prediction preview
- executive summary preview
- operator approval state

Action behavior:
- Customer Export enabled only when `customer_ready=true` and approval is checked.
- Internal Draft Export enabled only when explicit internal draft mode is checked and approval is checked.

Result rendering:
- Keep quality states visible (`customer_ready`, `draft_only`, `blocked_missing_analysis`).
- Keep actions separate (Download PDF / Open Reports Folder / Copy PDF Path).

## Validation Plan

1. Queue fight with no linked analysis record blocks customer PDF export.
2. Queue fight with existing linked analysis record generates populated report.
3. Internal draft mode generates real draft content (not unavailable placeholders).
4. Customer-ready PDF contains no unavailable placeholder sections.
5. UI shows linked analysis source and linked record ID when found.
6. UI shows missing sections before export.
7. Existing Button 1/2/3 tests remain green.

## Out of Scope

- Any Button 1 behavior or contracts
- Any Button 3 behavior or contracts
- Result lookup expansion
- Learning/calibration changes
- Billing or entitlement changes
- Uncontrolled write paths

## Design Verdict

Approved as docs-only design slice for design-review gating.