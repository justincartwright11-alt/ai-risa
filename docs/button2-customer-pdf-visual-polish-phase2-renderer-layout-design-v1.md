# Button 2 Customer PDF — Visual-Polish Phase 2 — Renderer & Layout Design

**Phase 2 Objective**: Design how Phase 1 locked metadata layers will be applied to renderer/layout logic before implementing PDF output changes.

**Phase Status**: 🔒 **DESIGN ONLY — NO IMPLEMENTATION YET**

**Phase 1 Foundation**: Commit `70d3ff5`, Tag `button2-customer-pdf-visual-polish-phase1-final-handoff-v1`

---

## 1. Purpose

Phase 2 defines the renderer and layout implementation strategy that consumes Phase 1 metadata layers to produce visually consistent, quality-assured PDF output.

**Design Principle**: Phase 1 metadata is frozen and immutable. Phase 2 design describes how to use that metadata to drive rendering decisions.

**Core Contract**:
- Input: Phase 1 frozen metadata layers (7 layers, all observational)
- Process: Apply metadata to renderer CSS/layout logic
- Output: PDF with consistent typography, hierarchy, page-breaks, charts, headers/footers, citations, and embedded quality indicators
- Safety: No changes to Phase 1 metadata, no new decision logic, no approval-gate changes

---

## 2. Locked Phase 1 Foundation

### Phase 1 Layers (Immutable for Phase 2)

| Layer | Locked Status | Key Outputs for Phase 2 |
|-------|---------------|--------------------------|
| **Layer 1: Typography Tokens** | ✅ Locked | CSS font stacks, sizes, weights, colors, line-heights |
| **Layer 2: Page Hierarchy** | ✅ Locked | Heading levels, semantic roles, DOM outline structure |
| **Layer 3: Page-Breaks & Section Blocks** | ✅ Locked | Break rules, section boundaries, orphan/widow constraints |
| **Layer 4: Chart & Scenario-Tree** | ✅ Locked | Chart inventory, data binding, SVG metadata, visual rules |
| **Layer 5: Header/Footer/Watermark** | ✅ Locked | Document structure, approval indicator, watermark rules |
| **Layer 6: Source Traceability** | ✅ Locked | Citation completeness, source URL tier, evidence embedding |
| **Layer 7: Visual QA Rollup** | ✅ Locked | Completeness score, confidence, readiness, review focus |

### Phase 1 Safety Invariants (Immutable for Phase 2)

✅ **preview_only = True** (remains True)  
✅ **pdf_generation_performed = False** (remains False until Phase 3)  
✅ **file_write_performed = False** (remains False until Phase 3)  
✅ **export_performed = False** (remains False until Phase 3)  
✅ **delivery_performed = False** (remains False until Phase 3)

**Implication for Phase 2**: No Phase 2 code should change these invariants. Phase 2 is still "preview" mode — PDF composition without actual file output.

---

## 3. Phase 2 Renderer & Layout Scope

### What Phase 2 Includes

✅ **Typography Rendering**: Apply Layer 1 CSS tokens to HTML/PDF renderer  
✅ **Hierarchy Rendering**: Enforce Layer 2 heading structure, semantic roles  
✅ **Page-Break Rendering**: Apply Layer 3 break rules, section boundaries  
✅ **Chart Visual Rendering**: Render Layer 4 charts as SVG/PNG in PDF  
✅ **Header/Footer/Watermark Rendering**: Apply Layer 5 document structure  
✅ **Source Link Embedding**: Render Layer 6 citations as hyperlinks in PDF  
✅ **Quality Watermark**: Visual indicator of Layer 7 QA status (optional preview marker)  

### What Phase 2 Does NOT Include

❌ **No Dashboard Changes**: Dashboard UI remains unchanged  
❌ **No Delivery Workflow**: No PDF export, no file write, no email/storage  
❌ **No Approval Gates**: No operator sign-off logic, no automatic decisions  
❌ **No Certification Automation**: No status changes based on QA metrics  
❌ **No Safety Invariant Changes**: All 5 invariants remain as-is  
❌ **No Phase 1 Metadata Changes**: All 7 layers frozen and untouched  

---

## 4. Typography Rendering Application

### Phase 1 Typography Input

**Layer 1 outputs** (from Phase 1 metadata):
- CSS font-family stack (system fonts first, fallbacks)
- Font size scale (8pt, 9pt, 10pt, 11pt, 12pt, 14pt, 16pt, 18pt, 20pt, 24pt)
- Font weight classes (400=regular, 600=semibold, 700=bold)
- Color palette (text color #111111, secondary #666666, caption #999999)
- Line-height scale (1.2, 1.3, 1.4, 1.5)

### Phase 2 Renderer Application

**Typography rendering strategy**:

1. **Font Stack Application**:
   - Pass Phase 1 font-family CSS to PDF renderer
   - Render all text with system fonts in order (system fonts → Segoe UI → sans-serif)
   - Validate font availability at render time
   - Fall back to default sans-serif if fonts unavailable

2. **Size & Weight Application**:
   - Typography class → CSS size/weight mapping
   - `typography-body-primary` → 12pt, 400 weight
   - `typography-caption-primary` → 10pt, 600 weight
   - Apply mapping consistently across all text elements

3. **Color Application**:
   - Text color → #111111 (dark text on white background)
   - Secondary text → #666666 (subtext, metadata)
   - Caption text → #999999 (timestamp, attribution)
   - Render with color ICC profile for consistent output

4. **Line-Height Application**:
   - Body text → 1.5 line-height
   - Headings → 1.3-1.4 line-height (tighter for titles)
   - Apply at render time to ensure proper spacing

### Phase 2 QA Proof for Typography

**Proof required**: All text in PDF renders with correct font, size, weight, color, line-height.

**Validation**:
- Spot-check: Sample body text, caption, heading for correct font stack
- Validate: No missing fonts, no fallback surprises
- Measure: Line-height matches CSS specification within ±5%

---

## 5. Page-Break Rendering Application

### Phase 1 Page-Break Input

**Layer 3 outputs** (from Phase 1 metadata):
- Break rules (forced break, avoid break, inherit break)
- Section block definitions with break constraints
- Orphan/widow prevention rules
- Cross-page boundary handling strategy

### Phase 2 Renderer Application

**Page-break rendering strategy**:

1. **Break Rule Enforcement**:
   - Identify all section blocks marked with break rules
   - Apply forced break (page-break-before: always) where specified
   - Apply avoid break (page-break-inside: avoid) where specified
   - Apply inherit rules to child elements

2. **Section Boundary Handling**:
   - Section starts on new page if marked with forced break
   - Section stays together if marked with avoid break
   - Measure section height; if > page height, allow section to split with avoid-break guidance
   - Apply break at logical content points (between subsections, not mid-sentence)

3. **Orphan/Widow Prevention**:
   - Orphan rule: First line of section not left at bottom of page
   - Widow rule: Last line of section not left at top of page
   - Apply at render time; if violation detected, reflow content to previous or next page

4. **Cross-Page Boundary**:
   - Headers/footers continue across all pages
   - Section number/title reappears on continuation page (e.g., "Fighter Details (cont'd)")
   - Watermark appears on all pages
   - Metadata embedded on all pages

### Phase 2 QA Proof for Page-Breaks

**Proof required**: All page breaks render correctly; no orphans, no widows, no mid-sentence breaks.

**Validation**:
- Visual inspection: Check page boundaries, section continuity
- Orphan/widow test: Inspect first/last lines of sections
- Break rule test: Verify forced/avoided breaks applied

---

## 6. Header/Footer/Watermark Rendering Application

### Phase 1 HFW Input

**Layer 5 outputs** (from Phase 1 metadata):
- Header structure (branding, title, metadata fields)
- Footer structure (page numbers, timestamp, approval indicator)
- Watermark visibility and opacity
- Approval timestamp format

### Phase 2 Renderer Application

**Header/Footer/Watermark rendering strategy**:

1. **Header Rendering** (All Pages):
   - Branding logo (top-left, fixed size)
   - Report title (top-center, typography-heading-primary)
   - Metadata line (top-right, small font, "Generated: YYYY-MM-DD")
   - Horizontal line separator (0.5pt, #CCCCCC)
   - Fixed position in page margins (not part of flow)

2. **Footer Rendering** (All Pages):
   - Page number (bottom-center, "Page X of Y")
   - Timestamp (bottom-left, approval_timestamp format "YYYY-MM-DD HH:MM:SS UTC")
   - Approval indicator (bottom-right, small badge, "Generated (Preview)" or "Approved")
   - Fixed position in page margins (not part of flow)

3. **Watermark Rendering** (All Pages):
   - Watermark text: "CONFIDENTIAL — AI-RISA Premium Report"
   - Watermark opacity: 0.05 (5% opacity, very faint)
   - Watermark angle: 45° diagonal
   - Watermark layer: Behind all content (z-index: 0)
   - Watermark color: #999999 (light gray)
   - Fixed size across all pages

4. **Page Continuity**:
   - If section spans multiple pages, repeat header on continuation
   - If section spans multiple pages, increment footer page number
   - Watermark consistent on all pages

### Phase 2 QA Proof for HFW

**Proof required**: Headers/footers/watermarks render consistently on all pages.

**Validation**:
- Multi-page test: Verify header/footer on page 1, 2, 3+
- Watermark opacity: Check watermark visibility (5% opacity)
- Continuity: Verify page numbers increment correctly
- Timestamp: Verify approval indicator displays correctly

---

## 7. Chart & Scenario Visual Rendering Strategy

### Phase 1 Chart Input

**Layer 4 outputs** (from Phase 1 metadata):
- Chart inventory (types: bar, line, scenario tree, heatmap)
- Chart data binding (series definitions, axis labels, legend)
- Visual consistency rules (color palettes, spacing, alignment)
- SVG metadata

### Phase 2 Renderer Application

**Chart rendering strategy**:

1. **Chart Type Rendering**:
   - **Bar Charts**: Render as horizontal/vertical bars with category labels on axes
   - **Line Charts**: Render as line series with markers at data points
   - **Scenario Trees**: Render as tree diagram with nodes and edges
   - **Heatmaps**: Render as color grid with intensity legend

2. **Data Binding Application**:
   - Apply axis labels from Layer 4 metadata
   - Apply legend from Layer 4 metadata
   - Render all series with correct colors from color palette
   - Apply grid lines if specified in metadata

3. **Visual Consistency**:
   - Use consistent color palette across all charts (Layer 4)
   - Apply consistent spacing between bars/series
   - Use consistent font sizes for labels (Layer 1 typography)
   - Align chart edges at column boundaries

4. **SVG Rendering**:
   - Charts rendered as inline SVG in HTML
   - SVG metadata embedded (from Layer 4)
   - SVG accessibility labels included
   - SVG rasterized to PNG for PDF output (if PDF renderer doesn't support SVG)

5. **Placeholder Fallback**:
   - If chart data missing, render placeholder gray box with "Chart: [Name] (No Data)"
   - Placeholder maintains same dimensions as chart would
   - Placeholder doesn't break page layout

### Phase 2 QA Proof for Charts

**Proof required**: All charts render correctly with correct data binding and visual consistency.

**Validation**:
- Chart type test: Verify each chart type renders correctly
- Data binding test: Check axis labels, legend, series colors match metadata
- Visual consistency test: Verify spacing, alignment, font sizes consistent
- Placeholder test: Verify placeholder renders if data missing

---

## 8. Source Traceability Rendering Strategy

### Phase 1 Source Input

**Layer 6 outputs** (from Phase 1 metadata):
- Citation inventory (all sources used in report)
- Source URL tier classification (official, secondary)
- Evidence embedding rules
- Citation completeness score

### Phase 2 Renderer Application

**Source rendering strategy**:

1. **Citation Embedding**:
   - All inline citations rendered as hyperlinks in PDF
   - Hyperlink text: [Source: Fighter DB] or [Source: Sherdog]
   - Hyperlink target: URL from Layer 6 metadata
   - Hyperlink color: #0066CC (standard blue)
   - Hyperlink formatting: Underlined (PDF standard)

2. **Citation List**:
   - Final report section: "Sources Cited"
   - List all citations with URLs, access dates, tier classification
   - Format: "• [Source Name] ([Tier]) - [URL] - accessed [Date]"
   - Render after all report content

3. **Evidence Embedding**:
   - Optional: Embed Layer 6 evidence metadata as PDF document properties
   - PDF property: /Subject = "Citation evidence embedded"
   - PDF property: /Keywords = comma-separated source URLs
   - Not visible to user, available for programmatic inspection

4. **Citation Completeness**:
   - Visual indicator if citation completeness < 100%
   - Indicator: Small note in footer, "Citation coverage: X%"
   - Color: Green if 100%, Yellow if 90-99%, Red if <90%
   - Render on all pages

### Phase 2 QA Proof for Sources

**Proof required**: All citations render as hyperlinks; citation list complete; completeness indicator visible.

**Validation**:
- Hyperlink test: Click all citation links in generated PDF
- Citation list test: Verify all sources appear in final section
- Completeness test: Verify indicator color matches coverage level
- Evidence test: Inspect PDF metadata for embedded evidence

---

## 9. Visual QA Proof Requirements

### Phase 1 Visual QA Input

**Layer 7 outputs** (from Phase 1 metadata):
- Rollup status (all_valid, mixed, all_invalid)
- Completeness score (0-1)
- Visual confidence (high, medium, low, unknown)
- Certification readiness (ready, needs_review, not_ready)
- Recommended review focus (prioritized list)

### Phase 2 Renderer Application

**Visual QA proof strategy**:

1. **Quality Watermark** (Optional Preview Indicator):
   - If certification_readiness == "ready": Render "[✓ Quality Assured]" in corner
   - If certification_readiness == "needs_review": Render "[⚠ Needs Review]" in corner
   - If certification_readiness == "not_ready": Render "[✗ Incomplete]" in corner
   - Corner position: Top-right, small font (8pt), light color (#AAAAAA)
   - This is visual indicator only, not certification

2. **Embedded QA Metadata**:
   - All QA metadata (from Layer 7) embedded in PDF hidden section
   - Format: JSON in PDF document properties or XMP metadata
   - Content: rollup_status, completeness, confidence, readiness, focus
   - Accessible to operator for inspection, not visible to customer

3. **QA Footer Row** (Optional):
   - Optional: Render Layer 7 QA indicator in footer
   - Format: "Visual QA: [Confidence] / [Readiness]"
   - Example: "Visual QA: High / Ready" or "Visual QA: Low / Needs Review"
   - Color: Green for "High"/"Ready", Yellow for "Medium"/"Needs Review", Red for "Low"/"Not Ready"
   - Only render if explicitly requested in operator dashboard

4. **Review Focus** (Operator Internal Only):
   - Do not render review focus in PDF (internal use only)
   - Render in operator dashboard/preview (separate from PDF)
   - Layer 7 recommended focus available for operator inspection before approval

### Phase 2 QA Proof for Visual QA

**Proof required**: Quality watermark renders correctly; QA metadata embedded; QA footer optional but functional.

**Validation**:
- Watermark test: Verify watermark text matches certification_readiness
- Metadata test: Inspect PDF for embedded QA metadata
- Footer test: If enabled, verify QA indicator colors correct
- Operator test: Verify operator can inspect recommended focus in dashboard

---

## 10. Safety & Approval Boundaries

### Phase 2 Safety Constraints

**Immutable invariants** (from Phase 1):
- ✅ preview_only = True (remains True throughout Phase 2)
- ✅ pdf_generation_performed = False (remains False)
- ✅ file_write_performed = False (remains False)
- ✅ export_performed = False (remains False)
- ✅ delivery_performed = False (remains False)

**Implication**: Phase 2 code changes HTML/CSS/rendering logic but does not:
- Write files to disk
- Generate actual PDF bytes (or if it does, doesn't save to file)
- Perform exports
- Perform delivery operations
- Change approval/certification logic

### No New Decision Logic

**Phase 2 constraint**: No new decision-making logic.

- ✅ Phase 2 applies Phase 1 metadata to rendering (procedural)
- ❌ Phase 2 does not make new decisions (no conditional business logic)
- ❌ Phase 2 does not automate certification (that's Phase 3+)
- ❌ Phase 2 does not trigger approval gates (that's Phase 3+)

### No Phase 1 Modifications

**Phase 2 constraint**: Phase 1 metadata layers frozen.

- ✅ Phase 2 reads Phase 1 metadata (consume-only)
- ❌ Phase 2 does not modify Phase 1 metadata
- ❌ Phase 2 does not add new Phase 1 requirements
- ❌ Phase 2 does not change Phase 1 validation contracts

---

## 11. Implementation Slice Sequence

### Proposed Slices (Design Only, No Implementation Yet)

**Slice 1: Typography Rendering Foundation**
- Purpose: Apply Phase 1 typography tokens to PDF renderer
- Input: Phase 1 Layer 1 CSS, Phase 1 typography metadata
- Output: HTML/PDF with correct fonts, sizes, weights, colors
- Tests: Spot-check fonts, colors, sizes in generated PDF
- Status: Design → Implementation (when approved)

**Slice 2: Page Structure & Hierarchy Rendering**
- Purpose: Apply Phase 1 page hierarchy to PDF renderer
- Input: Phase 1 Layer 2 hierarchy metadata, heading structure
- Output: HTML/PDF with correct heading levels, semantic roles
- Tests: Validate heading order, nesting levels, semantic structure
- Status: Design → Implementation (after Slice 1)

**Slice 3: Page-Break & Section Rendering**
- Purpose: Apply Phase 1 page-break rules to PDF renderer
- Input: Phase 1 Layer 3 page-break metadata, section boundaries
- Output: HTML/PDF with correct page breaks, section continuity, orphan prevention
- Tests: Multi-page PDF validation, orphan/widow prevention
- Status: Design → Implementation (after Slice 2)

**Slice 4: Chart & Scenario Visual Rendering**
- Purpose: Render Phase 1 Layer 4 charts as visual elements
- Input: Phase 1 Layer 4 chart metadata, SVG definitions
- Output: HTML/PDF with rendered charts, legends, accessibility
- Tests: Chart rendering validation, data binding verification
- Status: Design → Implementation (after Slice 3)

**Slice 5: Header/Footer/Watermark Rendering**
- Purpose: Render Phase 1 Layer 5 document structure
- Input: Phase 1 Layer 5 HFW metadata, document fields
- Output: HTML/PDF with headers, footers, watermarks on all pages
- Tests: Multi-page HFW validation, page numbering, watermark opacity
- Status: Design → Implementation (after Slice 4)

**Slice 6: Source Link Embedding & Citation Rendering**
- Purpose: Render Phase 1 Layer 6 citations as hyperlinks
- Input: Phase 1 Layer 6 source metadata, citation list
- Output: HTML/PDF with hyperlinked citations, sources section
- Tests: Hyperlink validation, citation completeness verification
- Status: Design → Implementation (after Slice 5)

**Slice 7: Quality Watermark & QA Indicator Rendering**
- Purpose: Render Phase 1 Layer 7 QA status as visual indicator
- Input: Phase 1 Layer 7 rollup metadata, QA indicators
- Output: HTML/PDF with quality watermark, QA metadata embedded
- Tests: Watermark rendering, QA metadata verification
- Status: Design → Implementation (after Slice 6)

**Slice 8: Full Phase 2 Integration & Smoke Testing**
- Purpose: Verify all 7 slices coexist without conflicts
- Input: All Phase 2 rendering code
- Output: Complete HTML/PDF composition with all layers rendered
- Tests: Multi-layer coexistence, full regression, PDF structure validation
- Status: Design → Implementation (after Slices 1-7)

### Slice Dependencies

```
Slice 1 (Typography)
    ↓
Slice 2 (Hierarchy)
    ↓
Slice 3 (Page-Breaks)
    ↓
Slice 4 (Charts)
    ↓
Slice 5 (HFW)
    ↓
Slice 6 (Sources)
    ↓
Slice 7 (QA Watermark)
    ↓
Slice 8 (Integration & Smoke)
```

Sequential order ensures:
- Each slice builds on prior rendering work
- Fonts available before hierarchy sizing
- Page structure defined before page-breaks applied
- Content layout complete before HFW addition
- All visual elements present before QA watermark

---

## 12. Non-Goals (Phase 2 Explicitly Does NOT Do)

❌ **Dashboard UI Changes**: No changes to 3-button dashboard  
❌ **PDF Export**: No actual PDF file generation or saving  
❌ **File Write Operations**: No disk writes, no export folders  
❌ **Delivery Workflow**: No email, no cloud upload, no customer handoff  
❌ **Approval Automation**: No automatic status changes based on QA metrics  
❌ **Certification Decisions**: No certification logic, no approval gates  
❌ **New Metadata Layers**: No additions to Phase 1 layers  
❌ **Phase 1 Modifications**: No changes to frozen Phase 1 metadata  
❌ **Visual Certification Feature**: No operator sign-off logic  
❌ **Learning/Calibration**: No self-improvement automation  

---

## 13. Final Verdict

### Phase 2 Design Lock

**Status**: 🔒 **DESIGN LOCKED (This Document)**

**Approved Scope**:
- ✅ Typography rendering strategy (Layer 1 application)
- ✅ Hierarchy rendering strategy (Layer 2 application)
- ✅ Page-break rendering strategy (Layer 3 application)
- ✅ Chart visual rendering strategy (Layer 4 application)
- ✅ Header/Footer/Watermark rendering strategy (Layer 5 application)
- ✅ Source link embedding strategy (Layer 6 application)
- ✅ QA watermark rendering strategy (Layer 7 application)
- ✅ Implementation slice sequence (8 slices, sequential)
- ✅ Safety constraints (5 invariants preserved)

**Approved to Implement**: Yes, after this design lock.

**Design Review Required Before Implementation**: 
- Optional: Stakeholder design review of Phase 2 rendering strategy
- Optional: Architecture review of slice dependencies
- Recommended: Verify slice sequence with renderer team

### Ready for Phase 2 Implementation

Once design approved (or confirmed current lock is acceptable):

1. Create implementation branch: `feature/button2-phase2-renderer-layout`
2. Implement Slices 1-8 sequentially
3. Create unit tests for each slice (mirroring Phase 1 test pattern)
4. Create smoke tests for slice coexistence
5. Run full regression with Phase 1 tests + Phase 2 tests
6. Tag Phase 2 implementation when complete
7. Create Phase 2 final handoff document

### Next Steps

**Immediate** (Before Any Implementation):
- [ ] Design review gate (optional but recommended)
- [ ] Confirm slice sequence acceptable
- [ ] Confirm rendering strategy aligns with PDF output format

**After Design Approval**:
- [ ] Begin Phase 2 implementation (Slice 1: Typography)
- [ ] Follow slice dependencies strictly
- [ ] Maintain Phase 1 tests alongside new Phase 2 tests
- [ ] Create integration smoke tests (all slices together)

**Post-Phase 2 Implementation**:
- [ ] Phase 2 final handoff (mirroring Phase 1 pattern)
- [ ] Tag Phase 2 complete
- [ ] Design Phase 3 (PDF Export & Delivery)

---

## Appendix: Phase 2 Design Lock

**Document**: docs/button2-customer-pdf-visual-polish-phase2-renderer-layout-design-v1.md

**Status**: 🔒 **LOCKED (Design Only)**

**Next**: [Implement if approved, or design review if needed]

**Phase 1 Dependency**: Commit `70d3ff5`, Tag `button2-customer-pdf-visual-polish-phase1-final-handoff-v1`

---

**Generated**: 2026-05-17T11:21:53Z  
**Phase**: Phase 2 Design (Renderer & Layout)  
**Status**: DESIGN LOCKED  
**Implementation Status**: NOT YET STARTED  

---

**Design locked. Awaiting design review or implementation approval.**
