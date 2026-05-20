# button2-v29-template-readability-overlap-hardening-v2

## Scope
Hardening pass for the remaining dense-page geometry on the v29 Button 2 template pack. This slice keeps the existing v1 lock intact and only repairs the still-open layout defects on pages 6, 14, 16, and 17.

Baseline lock carried forward:
- Commit: `e1614d5`
- Tag: `button2-v29-template-readability-overlap-polish-v1`

Open repair slice:
- `button2-v29-template-readability-overlap-hardening-v2`

## Defect Reproduction
Primary reference used:
- Latest rendered PDF for Ben Whittaker vs Willy Hutchinson

Defect pages targeted:
- Page 6: Tactical Edge Map still needed a compact bottom-safe treatment
- Page 14: Round-by-Round Outlook needed tighter vertical balance
- Page 16: Scorecard Scenario commentary was still too close to the footer stack
- Page 17: Stoppage Windows mechanism/risk text still needed separate readable panels

Regression pages kept in view:
- 1, 2, 5, 9, 15, 23, 24

## Root Causes and Corrections
### Page 6 Tactical Edge Map
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_tactical_edge_table`

Corrections:
- Shortened the table copy and raised the minimum table font floor.
- Replaced footer-stack pressure with a compact operator note strip.
- Moved Command Instruction and Failure Consequence into one compact panel above the note strip.
- Added page-bounds metadata for overlap-safe verification.

### Page 14 Round-by-Round Outlook
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_round_control_graph`

Corrections:
- Tightened the card group vertically.
- Centered the three cards with equal width and balanced spacing.
- Recorded page-bounds metadata for the centered card block.

### Page 16 Scorecard Scenario
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_scorecard_scenario`

Corrections:
- Moved commentary into a compact readable panel above the bottom-safe zone.
- Replaced the footer-stack treatment with a compact operator note strip.
- Kept font sizes above the readability floor.

### Page 17 Stoppage Windows
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_method_probability_chart`

Corrections:
- Split mechanism and risk control into two readable bottom panels.
- Replaced footer-stack pressure with a compact operator note strip.
- Added page-bounds metadata for fail-closed gate checks.

## Readability/Layout Constants Added
In renderer:
- `MIN_BODY_FONT_SIZE`
- `MIN_CAPTION_FONT_SIZE`
- `MIN_TABLE_FONT_SIZE`
- `MIN_COMMENTARY_FONT_SIZE`
- `MIN_LABEL_FONT_SIZE`
- `FOOTER_SAFE_ZONE_Y`
- `BOTTOM_STRIP_SAFE_Y`
- `PANEL_INNER_PADDING`
- `MIN_PANEL_GAP`
- `MIN_CARD_GAP`
- `MAX_TEXT_LINES_PER_PANEL`
- `PAGE_SAFE_TOP`
- `PAGE_SAFE_BOTTOM`
- `FOOTER_RESERVED_HEIGHT`
- `BOTTOM_STRIP_RESERVED_HEIGHT`
- `SECTION_STRIP_RESERVED_HEIGHT`
- `DENSE_PAGE_CONTENT_BOTTOM`

## Visual Gate Extension
Gate targets:
- `operator_dashboard/app.py::_selected_matchup_passes_strict_pdf_quality_gate`
- `operator_dashboard/app.py::_pdf_quality_gate_status`

Added fail-closed checks:
- `visual_defect_page_6_overlap_detected`
- `visual_defect_page_14_overlap_detected`
- `visual_defect_page_16_overlap_detected`
- `visual_defect_page_17_overlap_detected`
- `visual_defect_page_6_font_too_small`
- `visual_defect_page_14_font_too_small`
- `visual_defect_page_16_font_too_small`
- `visual_defect_page_17_font_too_small`

Status mapping remains:
- `v29_readability_overlap_failed`

Behavior:
- customer-ready output is blocked if a dense page reports overlap metadata or falls below the readability floor.

## Files Changed
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_v29_template_readability_overlap_hardening_v2.py`

## Validation
### Compile
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py operator_dashboard/test_button2_v29_template_readability_overlap_hardening_v2.py`
- Result: pass

### Tests
- `python -m pytest operator_dashboard/test_button2_v29_template_readability_overlap_hardening_v2.py -q` -> `3 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_readability_overlap_polish_v1.py operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py operator_dashboard/test_button2_v29_template_readability_overlap_hardening_v2.py -q` -> `32 passed`

## Proof Artifacts
Rendered PDFs:
- `reports/ryan_curtis_adam_borics_bellator_298_premium_hardening_v2.pdf`
- `reports/bo_nickal_cody_brundage_ufc_300_premium_hardening_v2.pdf`
- `reports/ben_whittaker_willy_hutchinson_ben_whittaker_vs_willy_hutchinson_premium_hardening_v2.pdf`

Proof sheets:
- `ops/release_checks/button2_v29_template_readability_overlap_hardening_v2/proof/ryan_curtis_adam_borics_bellator_298_hardening_v2_contact_sheet.png`
- `ops/release_checks/button2_v29_template_readability_overlap_hardening_v2/proof/bo_nickal_cody_brundage_ufc_300_hardening_v2_contact_sheet.png`
- `ops/release_checks/button2_v29_template_readability_overlap_hardening_v2/proof/ben_whittaker_willy_hutchinson_ben_whittaker_vs_willy_hutchinson_hardening_v2_contact_sheet.png`

## Governance/Boundary Confirmation
Preserved unchanged:
- Button 1 queue promotion
- Button 2 queue selection/bulk generation contract
- Button 3
- event/source binding gate
- premium telemetry/fail-closed gate
- sample-data bleed gate
- selected-matchup payload binding
- v29 visual identity

## Final Visual Verdict
PASS - the dense-page readability hardening slice is accepted for delivery continuation.