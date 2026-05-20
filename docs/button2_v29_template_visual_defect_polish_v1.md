# button2-v29-template-visual-defect-polish-v1

## Scope
Polish the v29 premium renderer for customer-ready visual quality while preserving existing governance and data-binding contracts.

Baseline lock carried forward:
- Commit: `5d3f9bd`
- Tag: `button2-v29-template-sample-data-bleed-repair-v1`

## Critical Defects Reproduced
Reference PDF:
- `reports/bo_nickal_vs_cody_brundage_ufc_300_premium_20260520T005949Z_cd9397d11bc9.pdf`

Pages inspected:
- 1, 6, 14, 15, 16, 17, 23, 24

Reproduced defects:
- Cover logo tile risk when legacy logo asset fallback is used.
- Risk Trigger / Corner Command cards too close to footer rail on two-card bottom-strip pages (6, 16, 17).
- Source-map overlap on page 23 around REPORT ID / SOURCE URL region and discipline text placement.

Defect repro artifact:
- `ops/release_checks/button2_v29_template_visual_defect_polish_v1/bo_nickal_vs_cody_brundage_defect_repro_before_contact_sheet.png`

## Root Cause
- Logo candidate preference did not prioritize blended assets.
- Bottom-strip depth footer did not enforce a strict footer safe-zone contract.
- Source-map rows used fixed spacing and non-wrapped draw calls for long fields.
- Customer-ready gate lacked renderer-provided layout-safety metadata checks for these visual defects.

## Implementation
Primary patch targets:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`

Added test suite:
- `operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py`

### Renderer changes
- Prefer blended logo assets first (`ai_risa_logo_clean_blend.png`, `ai_risa_logo_watermark_blend.png`) before legacy fallback.
- Added alpha-safe logo preparation path to avoid hard black-tile rendering on fallback assets.
- Reworked bottom two-card strip layout to preserve footer safe-zone and keep footer/page rail readable.
- Added explicit footer safe-zone metadata for pages 6, 16, 17.
- Reworked source-map row layout with wrapped values and dynamic row heights for REPORT ID/SOURCE URL.
- Added source-map layout metadata proving row separation and URL/statement separation.
- Emitted `layout_safety` metadata from renderer for gate assertions.

### Gate changes
- Extended strict gate to fail closed on renderer visual safety violations:
  - `visual_defect_logo_black_tile_risk`
  - `visual_defect_logo_blend_failed`
  - `visual_defect_footer_safe_zone_failed:page_6|16|17`
  - `visual_defect_source_map_rows_overlap`
  - `visual_defect_source_map_url_statement_overlap`
- Added gate status mapping:
  - `v29_visual_defect_failed` when visual defect violations are present.

## Validation
Compile:
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py`
- Result: pass

Tests:
- `python -m pytest operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py -q` -> 12 passed
- `python -m pytest operator_dashboard/test_button2_v29_template_sample_data_bleed_repair_v1.py -q` -> 11 passed
- `python -m pytest operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py -q` -> 15 passed
- `python -m pytest operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py -q` -> 10 passed
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q` -> 16 passed

## Live 5050 Proof
Batch route exercised with operator approval for:
- Bo Nickal vs Cody Brundage
- Sean Strickland vs Dricus du Plessis

Live proof result:
- `ok=true`
- `generated_count=2`
- `failed_count=0`
- `skipped_count=0`

Generated proof PDFs:
- `reports/bo_nickal_vs_cody_brundage_ufc_300_premium_20260520T015112Z_97374ea2ebaa.pdf`
- `reports/sean_strickland_vs_dricus_du_plessis_ufc_304_premium_20260520T015114Z_3122aefa7e9a.pdf`

Contact sheets (pages 1, 6, 14, 15, 16, 17, 23, 24):
- `ops/release_checks/button2_v29_template_visual_defect_polish_v1/bo_nickal_vs_cody_brundage_visual_defect_polish_contact_sheet.png`
- `ops/release_checks/button2_v29_template_visual_defect_polish_v1/sean_strickland_vs_dricus_du_plessis_visual_defect_polish_contact_sheet.png`

## Human Visual Scan (Post-fix)
Both generated PDFs:
- Page 1 premium cover and fighters/event: PASS
- Logo tile defect removed: PASS
- Page 6 footer/card collision: PASS
- Page 14 round-control readability: PASS
- Page 15 scenario-tree readability: PASS
- Page 16 footer/card collision: PASS
- Page 17 footer/card collision: PASS
- Page 23 source-map overlap removed and rows separated: PASS
- Page 24 disclaimer/risk control present: PASS

## Governance Confirmation
Preserved unchanged:
- Button 1 queue promotion behavior.
- Button 2 queue selection / bulk generation contract.
- Button 3 behavior.
- Event/source binding gate.
- Premium telemetry fail-closed gate.
- Sample-data bleed gate.
- Selected-matchup payload binding.

## Final Verdict
PASS - approved for controlled manual delivery.
