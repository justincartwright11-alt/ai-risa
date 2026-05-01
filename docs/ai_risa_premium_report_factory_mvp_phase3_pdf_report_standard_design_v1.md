# AI-RISA Premium Report Factory MVP — Phase 3 PDF Report Standard Design v1

## Purpose

Define the customer-facing quality standard for AI-RISA premium PDF reports before any builder implementation begins. This document governs what a premium report must contain, how it must be structured, and what rules apply to export and distribution.

No code is written in this slice. This is a docs-only design artifact.

---

## Baseline

| Field | Value |
|-------|-------|
| Parent checkpoint commit | `e279077` |
| Parent checkpoint tag | `ai-risa-premium-report-factory-mvp-phase2-dashboard-runtime-mismatch-diagnostic-closure-v1` |
| Phase 2 archived baseline commit | `dfbacd4` |
| Phase 2 archived baseline tag | `ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-archive-lock-v1` |
| Slice type | Docs-only design |

---

## Report Types in Scope (Phase 3)

| Report Type | Description | Phase 3 |
|-------------|-------------|---------|
| Single matchup premium report | One fight from the saved queue — full analytical deep-dive | Yes |
| Full event-card report | All fights from a saved event in a single packaged PDF | Yes |
| Fighter profile report | Standalone fighter career/style profile | No — later slice if needed |

---

## Required Report Sections

Every premium report (single matchup or full event-card) must include all of the following sections in the order listed. Sections may be empty-state rendered with a clear placeholder if source data is insufficient, but must not be silently omitted.

### 1. Cover Page
- AI-RISA branding
- Report type label (`Single Matchup Premium Report` or `Full Event-Card Report`)
- Event name
- Event date
- Promotion
- Location
- Fighter A vs Fighter B (single matchup) or full card list (event-card)
- Report generation timestamp
- Operator notes (if any)
- Version and source reference

### 2. Headline Prediction
- Predicted winner
- Predicted method (Decision / KO / TKO / Submission)
- Confidence level (expressed as a clear plain-English band, e.g. "Moderate — 61–70%")
- One-sentence rationale

### 3. Executive Summary
- 3–5 sentences covering the strategic shape of the matchup
- No raw data or numeric clutter
- Framed for a non-technical reader

### 4. Matchup Snapshot
- Weight class
- Ruleset
- Fighter A: key physical and record attributes
- Fighter B: key physical and record attributes
- Head-to-head comparison table (reach, stance, win method distribution)

### 5. Decision Structure
- How this fight is likely to be decided (striking exchange, grappling control, pace/gas tank, judging criteria)
- Key decision pathway for each fighter

### 6. Energy Use and Gas Tank Projection
- Projected pace and energy expenditure per fighter
- Estimated performance drop-off round (if applicable)
- Factors driving the projection

### 7. Fatigue Failure Points
- Specific conditions under which each fighter's output degrades
- Round windows where fatigue is expected to become decisive

### 8. Mental Condition
- Confidence, pressure-handling, and adversity-response profile per fighter
- Championship or high-stakes performance track record (if available)

### 9. Collapse Triggers
- Identified scenario conditions that historically cause a fighter's game plan to break down
- E.g. early knockdown, forced grappling against preference, extended late rounds

### 10. Deception and Unpredictability
- Feint and timing tendencies
- Style deception — fighters who perform differently than their record implies
- Surprise-factor rating

### 11. Round-by-Round Control Shifts
- Projected control map across rounds (who leads in striking / grappling / pace)
- Key swing rounds identified
- Presented as a structured table or timeline, not prose only

### 12. Scenario Tree / Method Pathways
- Branching outcome map: if X happens → Y is likely
- At minimum two scenario branches per fighter
- Each branch links to a predicted method and confidence modifier

### 13. Risk Warnings
- Explicit list of factors that could invalidate the prediction
- E.g. late injury, weight-cut miss, opponent's uncharacteristic gameplan execution
- Framed as decision-support caveats, not disclaimers

### 14. Operator Notes
- Free-text section sourced from the `notes` field of the saved queue record
- If empty, rendered as "No operator notes recorded."

---

## Customer-Facing Quality Rules

| Rule | Standard |
|------|----------|
| Language | Professional, clear, no debug output, no raw JSON, no internal field names |
| Confidence explanation | Always expressed in plain English alongside any numeric value |
| Limitations | Every report must include a limitations statement in the Risk Warnings section |
| Branding | AI-RISA name, version, and generation timestamp on every page |
| Source traceability | `source_reference`, `event_name`, `event_date`, `promotion` recorded in report metadata |
| Consistency | Section order must be fixed — operators and customers must be able to navigate by section number |
| Empty-state handling | Sections with no available data render a clear placeholder, not a blank or missing section |
| No raw clutter | Internal IDs (e.g. `matchup_id`, `temporary_matchup_id`) must not appear in the customer-facing report body |

---

## Export Rules

| Rule | Standard |
|------|----------|
| PDF filename | `ai_risa_premium_report_{event_id}_{matchup_id}_{YYYYMMDD}.pdf` |
| Output folder | `ops/prf_reports/` (runtime-only, not committed) |
| Report status update | On successful export, the queue record's `report_status` field must be updated to `generated` |
| No automatic selling or billing | PDF generation does not trigger any payment, customer notification, or distribution action |
| No result lookup | PDF generation does not perform any web lookup or accuracy comparison |
| No self-learning | PDF generation does not update any accuracy ledger, scoring weight, or prediction model |
| Operator-initiated only | Export is always triggered by explicit operator action — never automatic or scheduled |

---

## Out of Scope (Phase 3)

The following are explicitly excluded from Phase 3 and must not be introduced during builder implementation:

- Result lookup or accuracy comparison triggered by PDF generation
- Accuracy ledger updates triggered by PDF generation
- Self-learning or model weight updates
- Web discovery or external data fetch during report generation
- Billing, payment processing, or customer automation of any kind
- Automatic distribution or emailing of generated PDFs
- Fighter profile reports (separate slice if needed)
- Global database expansion beyond the approved saved queue
- Any mutation to existing fight records, predictions, or accuracy scores

---

## Next Slice

After this design is reviewed and committed, the next authorized slice is:

```
ai-risa-premium-report-factory-mvp-phase3-pdf-report-builder-design-v1
```

That slice will define the technical implementation design for the PDF builder — endpoints, template engine, rendering pipeline, and dashboard controls — using this standard as the governing content contract.

No implementation begins until both design slices are committed and reviewed.
