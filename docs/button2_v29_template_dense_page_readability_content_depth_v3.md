# button2-v29-template-dense-page-readability-content-depth-v3

## Scope
Commercial-readiness repair pass for the still-blocking dense-page defects that remained visible after the locked v2 baseline.

Baseline carried forward:
- Commit: `e9735dd`
- Tag: `button2-v29-template-readability-overlap-hardening-v2`

Open repair slice:
- `button2-v29-template-dense-page-readability-content-depth-v3`

## Delivery Rule
Hold delivery unless all of the following are true:
- no customer-visible `Operator Note`
- no generic lens placeholder text
- no dense-page readability failures on pages 2, 6, 14, 16, and 17
- no selected-matchup bleed across live proofs
- page 23 traceability binds the correct event, sport, promotion, report id, and source url

## Root Causes
### Dense-page scaffold and placeholder leakage
Owning renderer:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`

Defects fixed:
- customer-visible scaffold-note panels on dense pages
- generic command-footer placeholder phrases leaking from the template pack
- shallow dashboard lens text that could pass geometry but still fail commercial depth

Corrections:
- removed customer-visible scaffold-note panels from pages 6, 16, and 17
- deepened page 2 Control / Danger / Command copy and recorded lens-depth metadata
- overrode template footer placeholder copy at runtime for the selected-matchup renderer path
- extended the strict gate to reject scaffold-note and generic-lens placeholder text fail-closed

### Selected-matchup bleed on live non-Callum proofs
Owning paths:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/button2_dossier_handoff_report_context_preview.py`

Live proof exposed two real binding defects after the first green test run:
- pages 6, 16, and 17 still contained hardcoded `Austin Williams` / `Walsh` strings when rendering Ben/Willy and Ryan/Adam
- the live handoff preview stripped `promotion`, which forced page 23 to fall back to `UFC`, while the renderer also hardcoded `sport = MMA`

Corrections:
- replaced the remaining hardcoded dense-page names with selected-matchup bindings
- preserved `promotion` and `source_type` through `build_button2_dossier_handoff_report_context_preview`
- inferred sport from selected matchup promotion/source url and bound that value into page 23
- added a focused v3 regression for alternate-matchup bleed and boxing source-map binding

## Gate Behavior
Strict gate status mapping added for this slice:
- `v29_dense_page_readability_failed`

Dense-page blockers enforced:
- scaffold-note text present in extracted PDF text
- generic lens placeholder text present in extracted PDF text
- renderer-reported operator-note presence
- dashboard lens-depth metadata not deep enough
- round heading/body overlap reported by renderer

## Files Changed
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/button2_dossier_handoff_report_context_preview.py`
- `operator_dashboard/test_button2_v29_template_dense_page_readability_content_depth_v3.py`
- `operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py`
- `ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/render_live_dense_page_proof_v3.py`

## Validation
### Required Matrix
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py` -> pass
- `python -m pytest operator_dashboard/test_button2_v29_template_dense_page_readability_content_depth_v3.py -q` -> `18 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_readability_overlap_hardening_v2.py -q` -> `3 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_visual_defect_polish_v1.py -q` -> `12 passed`
- `python -m pytest operator_dashboard/test_button2_v29_template_sample_data_bleed_repair_v1.py -q` -> `11 passed`
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q` -> `16 passed`

### Live 5050 Proof
Route used:
- `http://127.0.0.1:5050/api/button2/generate-selected-batch`

Cases rendered:
- Callum Walsh vs Austin Williams
- Ben Whittaker vs Willy Hutchinson
- Ryan Curtis vs Adam Borics

Pages inspected:
- `2, 6, 14, 16, 17, 23`

Confirmed in final live proof:
- `customer_ready=true` for all three cases
- `visual_gate_status=premium_template_confirmed` for all three cases
- no `Operator Note` in extracted text
- no generic lens placeholder phrases in extracted text
- no live bleed of Callum/Austin copy into Ben/Willy or Ryan/Adam
- page 23 binds boxing for Matchroom and Bellator for Bellator correctly
- event name, report id, and source url match the selected queue row

## Proof Artifacts
Live proof summary:
- `ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/live_proof_summary.json`

Live contact sheets:
- `ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/callum_walsh_vs_austin_williams_dense_page_contact_sheet.png`
- `ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/ben_whittaker_vs_willy_hutchinson_dense_page_contact_sheet.png`
- `ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/ryan_curtis_vs_adam_borics_dense_page_contact_sheet.png`

Live PDFs:
- `reports/callum_walsh_vs_austin_williams_joshua_vs_dubois_premium_20260520T043439Z_f3574083526a.pdf`
- `reports/ben_whittaker_vs_willy_hutchinson_joshua_vs_dubois_premium_20260520T043442Z_76d7c6deafb5.pdf`
- `reports/ryan_curtis_vs_adam_borics_bellator_298_premium_20260520T043445Z_7ec037184afb.pdf`

## Governance/Boundary Confirmation
Preserved unchanged:
- Button 1 queue approval model
- Button 2 operator-approval gate
- Button 2 bulk generation contract
- Button 3 mutation/write protections
- fail-closed customer-ready behavior

## Final Verdict
PASS - the dense-page readability/content-depth v3 slice cleared the required matrix and live 5050 contact-sheet proof.