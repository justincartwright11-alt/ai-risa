# button2-template-pack-sample-asset-backed-pdf-renderer-v1

## Root Cause
Previous Button 2 output remained primarily HTML/CSS composition with premium markers, which did not bind to the actual template sample pack assets/modules as the visual source of truth.

## Template Pack Bound Path
- Default: `C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`
- Override: `BUTTON2_TEMPLATE_PACK_ROOT`

## Template Pack Files Discovered
- `AI-RISA Logo.png`
- `ai_risa_logo_clean_blend.png`
- `ai_risa_logo_watermark_blend.png`
- `ai_risa_report_template_v29_bar_alignment_fix.py`
- `AI-RISA_Premium_Fight_Intelligence_Report_v29_bar_alignment_fix.pdf`
- `AI-RISA_Premium_Report_Template_v29_bar_alignment_fix.zip`
- `contact_sheet_v29.png`
- `extracted_text_v29.txt`

## Implementation Summary
- Added governed resolver/validator and asset-backed renderer adapter:
  - `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- Updated generation integration to route premium selected-matchup flow through asset-backed renderer:
  - `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
- Updated selected-matchup ingest preview to use explicit resolver state:
  - `operator_dashboard/app.py`
- Added focused test suite:
  - `operator_dashboard/test_button2_template_pack_sample_asset_backed_pdf_renderer_v1.py`

## Customer-Facing Content Guarding
- Internal/debug-style text is filtered out of customer-facing executive body.
- Removed exposure of internal markers as primary body content:
  - template renderer profile
  - raw ingest mode
  - controlled export eligibility markers
  - visual QA rollup/missing-layer confidence internals
- Placeholder fallback phrases are blocked by tests.

## Runtime Proof
Generated via live guarded route:
- `reports/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf` (14 pages)
- `reports/rico_verhoeven_vs_tariq_osaro_glory_100_premium.pdf` (14 pages)
- `reports/jiri_prochazka_vs_carlos_ulberg_ufc_320_premium.pdf` (14 pages)

Live checks:
- Dashboard contains `PDF Reports Folder` and `Open PDF Reports Library`.
- `/api/button2/generated-report/open?filename=...` returns `200` for generated files.
- `/api/button2/generated-report/library` lists generated files.

## Visual Proof Artifacts
- `ops/release_checks/button2_template_pack_sample_asset_backed_pdf_renderer_v1/visual_proof/visual_proof_summary.json`
- Contact sheets:
  - `ops/release_checks/button2_template_pack_sample_asset_backed_pdf_renderer_v1/visual_proof/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium_contact_sheet.png`
  - `ops/release_checks/button2_template_pack_sample_asset_backed_pdf_renderer_v1/visual_proof/rico_verhoeven_vs_tariq_osaro_glory_100_premium_contact_sheet.png`
  - `ops/release_checks/button2_template_pack_sample_asset_backed_pdf_renderer_v1/visual_proof/jiri_prochazka_vs_carlos_ulberg_ufc_320_premium_contact_sheet.png`

Visual QA checks recorded:
- page 1/2/3/final-page renders captured
- no off-page text detected in sampled pages
- cover/section hierarchy/source traceability pages present

## Governance Confirmation
All validated generation outputs preserve:
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

## Test Result
- Focused + regression suite executed: `31 passed, 0 failed`
