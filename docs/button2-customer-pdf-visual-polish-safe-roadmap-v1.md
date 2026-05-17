# Button 2: Customer PDF Visual Polish Safe Roadmap v1

**Status:** Design-Only (No Implementation)  
**Date:** May 17, 2026  
**Design Lock Candidate:** Ready for review before implementation begins  
**Governance:** All visual polish remains behind Gate 2 operator approval

---

## 1. Purpose

Define the safe visual/layout polish sequence for customer-facing Button 2 PDFs now that the guarded generation foundation is proven and locked.

This design document establishes rules for typography, hierarchy, spacing, page breaks, and visual metadata without changing the underlying report generation path, approval logic, or delivery workflow.

**Scope:** Visual presentation only  
**Out of Scope:** Approval logic changes, new file write paths, customer data changes, renderer rewrite, dashboard UI changes, delivery workflow expansion

---

## 2. Locked Generation Foundation

All visual polish implementations will run within this unchanging envelope:

### Approval Gate (Non-Negotiable)
```
POST /api/operator/button2/generate-report
  → Gate 2 operator approval check (403 if absent)
  → Approval: proceed to composition
  → Rejection: no side effects, no file write
```

### Generation Chain (Locked)
```
Slice 1 (2e94a1b, 42 tests):
  - HTML composition entry point
  - Dynamic content → HTML template → escaped output
  - No external URLs, inline CSS only

Slice 2 (300975b, 35 tests):
  - PDF output root config (env var, server-derived path, traversal guard)
  - fight_id → safe filename → realpath verification

Slice 3 (7b408f4, 30 tests):
  - Route render-gate integration
  - Approval → composition → render → path resolution → file write
  - All-or-nothing: failure at any stage prevents file write

Slice 4 (938a8d3, 13 smoke tests):
  - Real file I/O proof with temp dirs
  - No partial writes on failure
  - Visual QA optional, best-effort, fail-closed
  - 339 total Button 2 tests passed

Slice 5 (9522ca7, docs-only):
  - Final handoff locking all safety constraints
```

### No Changes to These Invariants
- Gate 2 approval check remains first, non-negotiable
- Output path derivation remains server-only (`resolve_pdf_output_path(fight_id)`)
- No user-supplied path injection
- No partial writes on failure
- All PDF writes through single guarded route only
- Visual QA metadata optional, never blocks report generation

---

## 3. Visual Polish Principles from AI-RISA Research Engine

Button 2 reports serve a single purpose: **operator-to-customer handoff of fight intelligence with transparent sourcing and confidence bounds.**

### Core Principle: Transparency Over Aesthetics
- Every claim traceable to source or calculation
- Confidence/uncertainty always visible
- No ornament without information value
- Reader should know what AI-RISA believes with certainty vs. research/estimate

### Design Hierarchy
1. **Critical operator signal** (why this fight matters) — largest, most prominent
2. **Fighter context** (records, styles, matchup implications) — secondary prominence
3. **Scenario details** (tactical reads, injury factors) — tertiary, scannable sections
4. **Sources and calibration** (who provided this, how certain) — always visible, never hidden

### Polish Targets (In Priority Order)
1. **Typography consistency** — clear distinction between title, section header, body, small print
2. **Section scanability** — visual hierarchy that lets operator find key signal fast
3. **Page break logic** — no orphaned sections, no mid-thought page breaks
4. **Chart readability** — scenario trees, heatmaps, comp charts sized for print
5. **Source traceability** — inline citations, footer references, calibration metadata
6. **Export polish** — headers, footers, watermarks, page numbering

---

## 4. Typography Rules

### Font Stack (No Changes to Render Stack)
Current composition uses WeasyPrint defaults. Polish defines visual intent **within** those constraints.

```
Desktop Display (on-screen review):
  Body: system sans-serif
  Headers: system sans-serif, weight 600+
  Small Print: 9-10pt, monospace for URLs/sources

PDF Export (operator → customer):
  Body: embedded system sans-serif
  Headers: embedded sans-serif, weight 600+
  Small Print: 8-9pt monospace
```

### Font Sizing Rules
```
Report Title:         18-20pt, weight 700, letter-spacing +0.5px
Section Header (L1):  14-16pt, weight 600, margin-top 12pt, margin-bottom 6pt
Subsection (L2):      12-13pt, weight 600, margin-top 8pt, margin-bottom 4pt
Body Paragraph:       11-12pt, weight 400, line-height 1.5
Figure Caption:       10pt, weight 500, color #666
Source Citation:      9pt, weight 400, color #777, monospace
Page Metadata:        8-9pt, weight 400, color #999, monospace
```

### Weight Distribution
- **Bold (600+):** Section headers only, not inline
- **Regular (400):** All body text, captions
- **Monospace (9pt):** Source URLs, fighter names with diacritics (ASCII fallback), calibration references

### Line Height Rules
- Body paragraphs: 1.5 (55-65 characters per line, 11-12pt font)
- List items: 1.4
- Captions: 1.3
- Section headers: 1.2 (compact)

---

## 5. Page Hierarchy Rules

### Mandatory Top-Level Sections
Every report must maintain this visual hierarchy:

```
[Page 1, Top]
  Report Title (18-20pt)
    Fight Date, Event, Location (12pt)
    Operator Approval Timestamp (9pt, gray)

[Page 1, Body]
  Fighter A Context (L1 header)
    Record Summary (L2), Style Notes (L2), Injury Notes (L2)
  
  Fighter B Context (L1 header)
    Record Summary (L2), Style Notes (L2), Injury Notes (L2)

  Matchup Signal (L1 header)
    Key Implications (L2), Confidence Bound (L2)
    [Scenario Tree / Heatmap Chart]

[Pages 2+]
  Detailed Analysis (L1 header per section)
    [Tactical Deep Dives, Fight History, Comp Charts]

[Final Page]
  Sources & Calibration (L1 header)
    Official Records (L2), Research Sources (L2), AI-RISA Confidence Bounds (L2)
    Footer: Operator name, timestamp, report version
```

### Visual Distinction Between Section Types
- **Operator-facing signal** (matchup implications, confidence): white background, 1pt border, light blue tint
- **Fighter context** (records, style): white background, left border accent
- **Detailed analysis** (scenario trees, comps): white background, no accent
- **Sources** (citations, calibration): light gray background, 9pt monospace

---

## 6. Spacing and No-Overlap Rules

### Margin Rules (All measurements in pt)
```
Section Header (L1):          margin-top: 12,   margin-bottom: 6
Subsection (L2):              margin-top: 8,    margin-bottom: 4
Paragraph:                    margin-top: 0,    margin-bottom: 8
Figure/Chart:                 margin-top: 8,    margin-bottom: 8
Figure Caption:               margin-top: 2,    margin-bottom: 8
Table:                        margin-top: 8,    margin-bottom: 8
List Item:                    margin-top: 2,    margin-bottom: 4
```

### Padding Rules (Box/Section Containers)
```
Operator Signal Box:          padding: 12pt all sides
Fighter Context Box:          padding: 10pt all sides
Analysis Section:             padding: 0 (borders only)
Source Citation:              padding: 4pt horizontal, 2pt vertical
```

### No-Overlap Guarantees
- No text shadow overlaps: use only direct color contrast
- No figure/chart overlaps with adjacent paragraphs: fixed spacing above/below
- Section headers never appear at page bottom without ≥2 body lines: adjust page breaks
- Footnotes/citations never float into margins: inline or fixed footer only

### Minimum Whitespace
- Horizontal margins: ≥0.5in on letter-size pages
- Vertical margins: ≥0.75in on letter-size pages
- Gutter (left margin on facing pages if double-sided): ≥0.25in additional

---

## 7. Page-Break Rules

### Atomic Section Units (Never Break Mid-Section)
```
Fighter Context:
  [L1 Header] + [All L2 subsections + content]
  → Keep all on one page if content ≤ 4 lines per subsection
  → If overflows, move entire section to next page

Matchup Signal:
  [L1 Header] + [Key Implications L2] + [Scenario Tree/Heatmap]
  → Keep all on one page if chart height ≤ 3 inches
  → If chart taller, move chart to next page, keep text on previous

Detailed Analysis Sections:
  [L1 Header] + [Tactical Analysis] + [Comp Chart]
  → Allow breaks after every 2-3 subsections if necessary
  → Never split a comp chart mid-display

Sources & Calibration:
  [L1 Header] + [All source lists]
  → Keep all on one page if ≤ 20 sources
  → If more, break after every 10 sources, repeat header on continuation page
```

### Widow/Orphan Prevention
- No section header on page bottom without ≥2 body lines following
- No single bullet point isolated at top of next page: adjust content or merge with previous
- No chart/table appearing alone at bottom of page with <1 inch of vertical space: move to next page

### Page-Break Metadata (For QA Validation)
```
Each page break must carry:
  - Section name triggering break
  - Content height on previous page
  - Overflow reason (section size, chart height, widow rule)
  - Atomic unit preserved (yes/no)
```

---

## 8. Tactical Chart / Scenario Tree Rules

### Chart Types in Button 2 Reports
1. **Scenario Tree** (tactical branches for fight outcome)
2. **Heatmap** (fighter strengths vs opponent styles)
3. **Comp Chart** (historical fighter comparisons)
4. **Timeline** (injury history, record progression)

### Sizing for Print (Letter-Size, 0.75in Margins)
```
Scenario Tree:
  Max width: 6.5 inches
  Max height: 3.5 inches
  Node size: 14-16pt font
  Branch thickness: 1-2pt
  Color contrast: ≥4.5:1 WCAG AA

Heatmap (Grid):
  Max width: 6.5 inches
  Max height: 4 inches
  Cell size: ≥0.3 inches
  Label font: 9-10pt
  Color scale: blue (low) → white (neutral) → red (high)

Comp Chart (Scatter/Bar):
  Max width: 6 inches
  Max height: 3 inches
  Point/bar size: ≥4pt radius or 0.1in width
  Legend: 9pt monospace, positioned right or below
  Grid lines: light gray, 0.5pt, no-print option in CSS

Timeline:
  Max width: 6.5 inches
  Max height: 2 inches
  Node spacing: ≥0.3 inches
  Label font: 10pt
```

### Chart Data Attribution
Every chart must include:
```
[Chart Title]
[Chart Display]
[Caption: Data source, date range, operator notes]
[Inline Citation: URL or source reference in 9pt monospace]
```

### Visual Consistency Rules
- All charts in same report use consistent color palettes
- Axis labels in 9pt sans-serif, monospace for values
- All legends positioned consistently (right edge or below)
- No chart rotations >15° (readability in print)
- All charts rendered at 300 DPI for PDF export

---

## 9. Header / Footer / Watermark Rules

### Header (Repeats on Every Page)
```
[Report Title] | [Event Name] | [Date]
[12pt left-aligned, gray separator line below]
```

### Footer (Repeats on Every Page)
```
[Page N of M] | Operator: [Name] | Generated: [Timestamp]
[8pt right-aligned, gray separator line above]
```

### Watermark (Optional, Controlled by Approval Metadata)
```
If operator approval includes "DRAFT" flag:
  - "DRAFT" watermark at 45° angle, gray, low opacity, behind text
  - Watermark removed when customer approval applied (future workflow)

If operator approval includes "CONFIDENTIAL" flag:
  - "CONFIDENTIAL" watermark at top, red text, 10pt, not behind text
```

### QA Check for Headers/Footers
```
Each page ≥2 (pages with content) must have:
  - Header present and readable (11-12pt, ≥2pt bold)
  - Footer present with page number (8-9pt)
  - Watermark (if applicable) not blocking critical content
```

---

## 10. Source Traceability Rules

### Inline Citation Format
```
Claim: "[Operator signal or AI-RISA assertion]"
Citation: "[Source Type: URL or Record ID]" in 9pt monospace, blue color
Example: "Fighter A has won 8 of last 10 fights (Source: boxrec.com/fighter/12345)"
```

### Source Categories
```
Official Records:     boxrec.com, tapology.com, sherdog.com (tier A — always first)
Research Sources:     mma-stats.com, ufcstats.com (tier B — secondary)
AI-RISA Analysis:     "AI-RISA v100 research" + date + confidence bound
Operator Input:       "Operator research: [date]" (always marked)
```

### Calibration Metadata in Footer
```
End-of-report source block:
  Official Records: [count] citations
  Research Sources: [count] citations
  AI-RISA Analysis: [count] sections, confidence bound [X-Y%]
  Operator Input: [count] overrides
```

### Never Omit Source
- Every numerical claim (records, percentages, comp metrics) must have inline citation
- Every qualitative claim (style, injury severity) must cite operator input or research source
- Placeholder text ("Fighter A", "Fight Date") flagged as QA failure

---

## 11. Visual QA Metadata Requirements

All visual polish implementations will emit QA metadata as part of the report context:

```json
{
  "visual_qa_metadata": {
    "typography_applied": true,
    "page_hierarchy_verified": true,
    "spacing_no_overlap_checked": true,
    "page_breaks_atomic": true,
    "chart_sizing_compliant": true,
    "header_footer_present": true,
    "source_traceability_complete": true,
    "watermark_applied": false,
    "geometry_proof_passed": true,
    "issues": []
  },
  "page_count": 3,
  "geometry_data": {
    "page_1": { "content_height": 8.5, "chart_count": 0, "break_reason": null },
    "page_2": { "content_height": 8.2, "chart_count": 1, "break_reason": "chart_height" },
    "page_3": { "content_height": 2.1, "chart_count": 0, "break_reason": "section_end" }
  },
  "source_summary": {
    "official_records": 12,
    "research_sources": 5,
    "ai_risa_analysis": 3,
    "operator_input": 2
  }
}
```

### QA Validation Checklist
- [ ] Typography applied: font sizes, weights, line heights per spec
- [ ] Page hierarchy visible: section headers distinguished from body
- [ ] Spacing consistent: margins/padding match no-overlap rules
- [ ] Page breaks preserve atomic units (no orphaned headers)
- [ ] Charts render at correct size for print (6in width typical)
- [ ] Header/footer present on every page (except first if full-bleed title)
- [ ] Source citations inline and traceable (no orphaned claims)
- [ ] Watermark (if applied) doesn't obscure critical content
- [ ] Geometry proof passes (no overlaps, correct page count)

---

## 12. Future Implementation Slice Sequence

### Post-Design Review (Before First Implementation)
1. **Design Review Lock** — architecture team confirms all rules are safe, no approval logic changes, no new file write paths
2. **Safety Audit** — verify no rules violate Gate 2 governance
3. **Backward Compatibility Audit** — confirm existing reports remain readable, no breaking changes to template structure

### Implementation Order (After Design Review Passes)
```
Slice 1 (Foundation + CSS):
  - Add typography rules to CSS (font sizes, weights, line heights)
  - Add spacing/margin rules to CSS
  - Add color/contrast rules to CSS
  - Create Typography QA test (35-50 tests)
  - Commit: button2-visual-polish-typography-implementation-v1

Slice 2 (Page Hierarchy):
  - Update section template HTML (L1, L2 headers, visual distinction)
  - Add hierarchy metadata to composition context
  - Create Hierarchy QA test (25-35 tests)
  - Commit: button2-visual-polish-page-hierarchy-implementation-v1

Slice 3 (Page Breaks + Charts):
  - Implement atomic section page-break rules (no orphans)
  - Implement chart sizing rules per type
  - Implement page-break metadata emission
  - Create Page Break QA test (30-40 tests)
  - Create Chart Sizing QA test (20-25 tests)
  - Commit: button2-visual-polish-page-breaks-chart-sizing-implementation-v1

Slice 4 (Headers/Footers/Watermarks):
  - Add header/footer template to PDF composition
  - Implement conditional watermark logic (draft/confidential flags)
  - Create Header/Footer QA test (15-20 tests)
  - Commit: button2-visual-polish-headers-footers-watermarks-implementation-v1

Slice 5 (Source Traceability):
  - Add inline citation HTML to all claims
  - Implement source category filtering (official/research/AI-RISA/operator)
  - Implement calibration metadata footer
  - Create Source Traceability QA test (25-30 tests)
  - Commit: button2-visual-polish-source-traceability-implementation-v1

Slice 6 (Visual QA Metadata + Proof):
  - Implement visual_qa_metadata emission in composition context
  - Extend run_geometry_proof() to validate all QA checks
  - Create Visual QA Proof test (30-40 tests)
  - Commit: button2-visual-polish-visual-qa-metadata-proof-v1

Slice 7 (Integration + Smoke Tests):
  - Route integration test (full flow with visual polish enabled)
  - Real file I/O smoke test (temp PDF export with geometry proof)
  - Create Integration Smoke test (15-20 tests)
  - Commit: button2-visual-polish-integration-smoke-v1

Slice 8 (Final Handoff):
  - Comprehensive handoff doc (locked, docs-only)
  - Commit: button2-visual-polish-final-handoff-v1
```

### Test Count Target
- Typography: 40 tests
- Hierarchy: 30 tests
- Page Breaks/Charts: 50 tests
- Headers/Footers/Watermarks: 20 tests
- Source Traceability: 30 tests
- Visual QA Metadata: 35 tests
- Integration/Smoke: 20 tests
- **Total: ~225 new Button 2 tests** (564+ total after all slices)

### Integration Assumptions
- All slices assume generate_button2_report_render_gate_integration() remains unchanged (no new route)
- All slices emit telemetry through existing {ok, error, output_path, qa_summary, telemetry} response format
- All slices remain behind Gate 2 approval gate
- All slices use existing BUTTON2_PDF_OUTPUT_ROOT for file writes

---

## 13. Non-Goals

**Explicitly Out of Scope:**

- ❌ Approval logic changes (Gate 2 remains first, non-negotiable)
- ❌ New file write paths (all PDFs written to configured BUTTON2_PDF_OUTPUT_ROOT only)
- ❌ Dashboard UI polish (this is API/report layer only)
- ❌ Delivery workflow expansion (customer handoff workflow is future scope)
- ❌ New data collection or transformation (composition data contracts unchanged)
- ❌ Renderer rewrite (WeasyPrint rendering unchanged, CSS polish only)
- ❌ Report format changes (PDF format locked, no new export formats)
- ❌ Authentication/authorization changes (Gate 2 operator approval unchanged)
- ❌ Customer personalization (all customer reports follow same visual rules)
- ❌ Dynamic content (all content determined at composition time, no async polish)

---

## 14. Final Verdict

### Safety Assessment
✅ **No approval logic changes** — Gate 2 operator approval remains first, non-negotiable guard  
✅ **No new file write paths** — all PDFs through guarded route only, server-derived output root  
✅ **No customer data exposure** — visual polish is presentation only, data contracts unchanged  
✅ **No partial writes** — all-or-nothing policy preserved (fail at any stage → no file write)  
✅ **Backward compatible** — existing reports readable, no breaking changes to template structure  

### Compliance Checklist
- ✅ Design-first approach (no implementation yet)
- ✅ Design review gate before first slice implementation
- ✅ Safety audit confirmation required
- ✅ Backward compatibility audit required
- ✅ All slices remain behind Gate 2 approval
- ✅ All slices use existing file write infrastructure
- ✅ All slices emit QA metadata for validation
- ✅ Implementation order designed to lock prerequisites first (typography → hierarchy → page breaks → charts → sources → QA → integration → handoff)

### Readiness Assessment
**Design:** COMPLETE and LOCKED  
**Prerequisite Validation:** All prior Button 2 slices locked (339 tests passed)  
**Next Step:** Architecture team design review + safety audit before implementation begins

### Implementation Readiness
This design is ready for implementation only after:
1. ✅ Architecture team confirms all rules are safe (no approval logic changes, no new paths, no data exposure)
2. ✅ Safety audit confirms Gate 2 governance preserved
3. ✅ Backward compatibility audit confirms no breaking changes to existing reports
4. Design review lock commit created (button2-customer-pdf-visual-polish-safe-roadmap-design-review-v1)

---

## Appendix A: Typography Quick Reference

```
Title:        18-20pt, 700 weight
H1 Header:    14-16pt, 600 weight, margin-top: 12pt
H2 Header:    12-13pt, 600 weight, margin-top: 8pt
Body:         11-12pt, 400 weight, line-height: 1.5
Caption:      10pt, 500 weight, color: #666
Source:       9pt, 400 weight, monospace, color: #777
Metadata:     8-9pt, 400 weight, monospace, color: #999
```

## Appendix B: Spacing Quick Reference

```
H1 + body:        margin-bottom: 6pt
H2 + body:        margin-bottom: 4pt
Paragraph:        margin-bottom: 8pt
Figure:           margin-top/bottom: 8pt
Chart:            margin-top/bottom: 8pt
Caption:          margin-bottom: 8pt
List item:        margin-bottom: 4pt
Box padding:      10-12pt all sides
Horizontal margin (page): ≥0.5in
Vertical margin (page):   ≥0.75in
```

## Appendix C: Page Break Atomic Units

```
Fighter Context Block:       [Header] + [All subsections] → NO BREAK
Matchup Signal Block:        [Header] + [Text] + [Chart] → NO BREAK (if ≤3in)
Analysis Section:            [Header] + [Content] → BREAK after 2-3 subsections if needed
Sources Block:               [Header] + [All sources] → BREAK every 10 sources if needed
```

---

**Design Lock Timestamp:** 2026-05-17  
**Ready for Architecture Review:** Yes  
**Design Status:** COMPLETE AND LOCKED (docs-only, no implementation)
