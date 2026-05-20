# button2-v29-template-readability-overlap-polish-v1

## Scope
Polish v29 readability and overlap safety for customer-facing pages while preserving Button 2 contracts and governance boundaries.

Baseline lock carried forward:
- Commit: `aaa588a`
- Tag: `button2-v29-template-visual-defect-polish-v1`

Open repair slice:
- `button2-v29-template-readability-overlap-polish-v1`

## Defect Reproduction
Primary reference used:
- Uploaded evidence for Ryan Curtis vs Adam Borics readability defects
- Prior visual scan sheet copied into this slice proof folder for before-reference:
  - `ops/release_checks/button2_v29_template_readability_overlap_polish_v1/proof/ryan_curtis_vs_adam_borics_before_readability_overlap_contact_sheet.png`

Defect pages targeted:
- Page 6: Tactical Edge Map overlap/legibility pressure
- Page 14: Round-by-Round Outlook alignment/balance
- Page 16: Scorecard Scenario commentary compression
- Page 17: Stoppage Windows mechanism/risk text compression

All-page scan target:
- 1-24 scanned through fresh post-fix output review; high-risk pages additionally captured in proof sheets.

## Root Causes and Corrections
### Page 6 Tactical Edge Map
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_tactical_edge_table`

Corrections:
- Raised table caption/body readability floor.
- Increased row minimum height and reduced row density near footer boundary.
- Moved Command Instruction and Failure Consequence into a dedicated panel above bottom strip.
- Preserved bottom risk/corner strip safe separation from footer.
- Added page-level layout safety markers:
  - `readable_min_font_passed`
  - `tactical_edge_overlap_passed`
  - `footer_safe_zone_passed`

### Page 14 Round-by-Round Outlook
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_round_control_graph`

Corrections:
- Replaced stacked cards with three balanced equal-width cards.
- Centered card set in content area.
- Increased text clarity and consistent spacing.
- Added marker: `round_outlook_centered_passed`

### Page 16 Scorecard Scenario
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_scorecard_scenario`

Corrections:
- Raised table and commentary font sizes to readable minimums.
- Wrapped long driver values instead of compressing to tiny text.
- Moved commentary panel upward and resized for bottom-strip clearance.
- Added marker: `scorecard_readability_passed`

### Page 17 Stoppage Windows
Likely renderer function:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py::_draw_method_probability_chart`

Corrections:
- Raised caption/body sizes for mechanism and risk-control language.
- Split mechanism and risk-control into two separate bottom panels.
- Kept panels above footer-safe strip with clean breathing room.
- Added marker: `stoppage_readability_passed`

## Readability/Layout Constants Added
In renderer:
- `MIN_BODY_FONT_SIZE`
- `MIN_CAPTION_FONT_SIZE`
- `MIN_TABLE_FONT_SIZE`
- `FOOTER_SAFE_ZONE_Y`
- `BOTTOM_STRIP_SAFE_Y`
- `PANEL_INNER_PADDING`
- `CARD_GAP`
- `MAX_TEXT_LINES_PER_PANEL`

## Visual Gate Extension
Gate target:
- `operator_dashboard/app.py::_selected_matchup_passes_strict_pdf_quality_gate`
- `operator_dashboard/app.py::_pdf_quality_gate_status`

Added fail-closed readability violations:
- `readability_min_font_not_met`
- `readability_footer_safe_zone_not_met`
- `readability_tactical_edge_overlap_not_met`
- `readability_round_outlook_not_centered`
- `readability_scorecard_scenario_not_readable`
- `readability_stoppage_windows_not_readable`

Status mapping:
- `v29_readability_overlap_failed`

Behavior:
- customer-facing output is blocked when readability markers fail.

## Files Changed
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_v29_template_readability_overlap_polish_v1.py`
- `operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py` (test fixture metadata/text alignment for stricter gate)

## Validation
### Compile
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py operator_dashboard/test_button2_v29_template_readability_overlap_polish_v1.py operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py`
- Result: pass

### Tests
- `python -m pytest operator_dashboard/test_button2_v29_template_readability_overlap_polish_v1.py -q` -> `13 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py -q` -> `12 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_sample_data_bleed_repair_v1.py -q` -> `11 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py -q` -> `12 passed`
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q` -> `16 passed`

## Live 5050 Proof
Route exercised:
- `/api/button2/generate-selected-batch`

Selected:
- `bellator_298_ryan_curtis_adam_borics`
- `ufc_300_bo_nickal_vs_cody_brundage`

Result:
- `ok=true`
- `generated_count=2`
- `failed_count=0`
- `skipped_count=0`
- `customer_ready=true` for both
- `visual_gate_status=premium_template_confirmed` for both

Generated proof PDFs:
- `reports/ryan_curtis_vs_adam_borics_bellator_298_premium_20260520T024658Z_b69d462b6a69.pdf`
- `reports/bo_nickal_vs_cody_brundage_ufc_300_premium_20260520T024700Z_63a53acd1112.pdf`

Proof sheets (pages 1, 6, 14, 16, 17, 23):
- `ops/release_checks/button2_v29_template_readability_overlap_polish_v1/proof/ryan_curtis_vs_adam_borics_readability_polish_contact_sheet.png`
- `ops/release_checks/button2_v29_template_readability_overlap_polish_v1/proof/bo_nickal_vs_cody_brundage_readability_polish_contact_sheet.png`
- Before reference:
  - `ops/release_checks/button2_v29_template_readability_overlap_polish_v1/proof/ryan_curtis_vs_adam_borics_before_readability_overlap_contact_sheet.png`

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
PASS - readability/overlap polish accepted for controlled hold-delivery continuation.
