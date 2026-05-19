# Open Slice: button2-pdf-rendered-visual-overlap-depth-qa-repair-v1

## Task
Fix the remaining Button 2 premium PDF defects using rendered-page visual QA, not just text extraction.

---

## Current Problem
The reports are 24 pages and pass text-marker tests, but visually they still fail:
1. Text and visuals overlap.
2. Bottom cards collide with page footer / each other.
3. Tables still collide.
4. Fighter Overview / Tale of the Tape is cramped.
5. Body Risk Heat Map still competes with labels.
6. Some pages have shallow repeated structure.
7. Text is too small and too compressed.
8. Visual modules exist, but many do not carry enough fight-specific intelligence.
9. Tests currently pass because they check markers, not rendered layout quality.

---

## Root Cause
The renderer uses fixed-position/fixed-height boxes for dynamic text. It must be converted to a safer layout system:
- Measure text before drawing.
- Wrap text properly.
- Allocate dynamic row heights.
- Split overflowing content into continuation panels/pages if needed.
- Enforce vertical spacing budgets.
- Prevent bottom cards from entering the footer zone.
- Prevent table columns from crossing.
- Prevent visual bars from entering text regions.

---

## Required Implementation Repairs

### A. Add Layout Safety Helpers
Add or improve renderer helpers:
1. `measure_wrapped_text_height()`
2. `draw_wrapped_text_box()`
3. `draw_auto_height_card()`
4. `draw_two_column_safe_layout()`
5. `draw_table_with_wrapped_cells()`
6. `check_box_fits_page()`
7. `prevent_footer_collision()`
8. `split_content_if_overflow()`

**Hard Rule:**
If text cannot fit in a box, do not shrink it until unreadable. Either increase box height, move the next module down, or split to a continuation block.

### B. Fix Cover Page
1. No logo/title overlap.
2. Title must fit inside safe bounds.
3. No clipped title.
4. No “Cover Page.”
5. Header/logo/title/event/footer all separated by reserved zones.
6. Bigger, cleaner Fighter A / VS / Fighter B layout.

### C. Fix Dashboard Page
1. Projected Edge must wrap and fit.
2. Confidence / volatility / method cards must not overflow.
3. Command Read must be a separate bounded block.
4. Round Control Snapshot must be readable.
5. Method Probability Mini Chart must not collide with text.
6. No dense paragraph dump.

### D. Fix Fighter Overview / Tale of the Tape
1. Fighter A and Fighter B profile blocks must not overlap.
2. VS block must not collide with names/profile rows.
3. Comparison bars must sit below text with clear spacing.
4. Long names must fit.
5. Add more detail:
   - Physical profile.
   - Style profile.
   - Pressure pattern.
   - Scoring route.
   - Danger route.
   - Coach meaning.
6. Keep all values marked model-derived unless source-confirmed.

### E. Fix Tactical Edge Table
1. Use real table layout with calculated row heights.
2. Columns:
   - Tactical Layer.
   - Edge.
   - Confidence.
   - Why It Matters.
   - Watch Cue.
3. Wrap “Why It Matters” and “Watch Cue.”
4. No text over borders.
5. No header collision.
6. No footer collision.
7. If table is too long, split into two tables or a continuation card.

### F. Fix Body Risk Heat Map / Anatomical Risk Map
1. Anatomy graphic gets its own isolated column.
2. Risk table gets its own isolated column.
3. Watch Cue / Interpretation panels do not overlap graphic.
4. Row labels and percentage bars must not collide.
5. Add deeper interpretation:
   - Target zone.
   - Why it matters.
   - Fight-specific trigger.
   - Mitigation/corner instruction.

### G. Fix All Lower-Section Depth Panels
Current bottom cards still collide and read like repeated filler.

Replace repeated tiny lower card rows with a safer full-width or two-column layout:
1. Tactical Thesis.
2. Mechanism.
3. Fighter A Pathway.
4. Fighter B Counter-Pathway.
5. Watch Cue.
6. Command Instruction.
7. Failure Consequence.
8. Round Band.
9. Visual/Data Read.
10. Buyer Meaning.
11. Coach Meaning.

Each item must have sentence-level depth, not fragment-level copy.

### H. Increase Fight-Specific Depth
For each matchup, generate richer section-specific content.

For every major section, write:
1. 2–3 sentence tactical thesis.
2. Mechanism explanation.
3. Fighter A route.
4. Fighter B disruption route.
5. Round band.
6. Watch cue.
7. Corner instruction.
8. Failure consequence.
9. Buyer/coach meaning.

---

## Validation

### Tests
Create:
`operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`

Test requirements:
1. Generated PDFs are 24 pages.
2. All 24 sections present.
3. Forbidden strings absent:
   - Cover Page.
   - Premium Cover.
   - where the fight is owned.
   - where the fight can flip.
   - what the corner must solve.
   - SOURCE TRACEABILITY Source Traceability.
   - customer_ready_not_ready.
   - draft_only.
   - controlled_export_not_eligible.
   - visual QA rollup.
   - template renderer profile.
   - raw ingest mode.
   - valid layers.
   - missing layers.

4. Extracted text does not show concatenation defects:
   - Fighter A PathwayAnthony.
   - Fighter B Counter-Pathway Daniel.
   - Buyer Meaning / Coach MeaningBuyer.
   - Command Instruction Preserve scoring geography before pace expansion; avoid low-value with no completion.

5. Required visual module markers present:
   - Fighter Overview.
   - Tale of the Tape.
   - Body Risk Heat Map.
   - Anatomical Risk Map.
   - Tactical Edge Table.
   - Failure Heat Map.
   - Round Control Graph.
   - Method Probability Chart.
   - Scenario Tree / Method Pathways.

6. Required depth markers present with richer content:
   - Tactical Thesis.
   - Mechanism.
   - Fighter A Pathway.
   - Fighter B Counter-Pathway.
   - Watch Cue.
   - Command Instruction.
   - Failure Consequence.
   - Round Band.
   - Visual/Data Read.
   - Buyer Meaning.
   - Coach Meaning.

7. The rendered visual QA JSON reports all pass flags true.
8. Dashboard open route returns HTTP 200.
9. PDF library route returns HTTP 200.
10. Governance flags remain false.

---

## Runtime Proof
1. Kill stale server.
2. Delete only the three matching stale reports under `reports/`.
3. Start:
   `./scripts/start_ai_risa_dashboard_windows.ps1`
4. Generate all three reports.
5. Run rendered visual scan script.
6. Open and manually inspect contact sheets.
7. Do not commit if any contact sheet still shows major overlap/collision.

---

## Commit
`button2-pdf-rendered-visual-overlap-depth-qa-repair-v1: repair rendered PDF overlap and deepen section content`

## Tag
`button2-pdf-rendered-visual-overlap-depth-qa-repair-v1`

---

**Final Report Must Include:**
1. Root cause.
2. Files changed.
3. Layout engine repairs.
4. Visual modules repaired.
5. Section-depth improvements.
6. Generated PDF paths.
7. Page counts.
8. Rendered visual proof paths.
9. Manual visual inspection verdict.
10. Forbidden/default scan result.
11. Concatenation/clipping scan result.
12. Dashboard link/library result.
13. Governance flags.
14. Tests run and result.
15. Commit hash.
16. Tag name.
17. Final git status.

---

**Hard Stop:**
Do not commit if:
1. Any contact sheet still shows obvious text/visual overlap.
2. Any lower card text is clipped.
3. Any table text collides.
4. Any PDF is not 24 pages.
5. Any forbidden/default string appears.
6. Any old stale PDF is reused.