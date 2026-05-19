# Button 2 Global Selected-Matchup Template Path Regression Fix v1

## Slice
button2-global-selected-matchup-template-path-regression-fix-v1

## Root Cause
Selected-matchup generation in the Button 2 integration flow still allowed an HTML fallback branch when `template_renderer_profile` did not start with `premium_template_pack_v29`.

That fallback branch can occur if ingest/context profile values drift or are missing. In that state, generation routes can bypass the template-pack asset renderer and produce old crowded card-engine output.

## Branch/Path Causing Nadaka Drift
- File: `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
- Function: `generate_button2_report_render_gate_integration`
- Branch: non-template fallback branch (`build_button2_report_html` + `render_button2_pdf`) when `use_asset_backed_renderer` is false.

## Fix Applied
1. Added selected-matchup detection guard in generation integration.
2. Enforced template-pack rendering for all selected-matchup contexts regardless of profile drift.
3. Enforced selected-matchup renderer profile normalization to premium template-pack path.
4. Ensured selected-matchup context has template-pack root fallback set to:
   - `C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`
5. Removed legacy card-engine marker output from customer-facing renderer text:
   - SECTION LENS
   - MODEL STATUS
   - REPORT TYPE
   - ROUND BAND (replaced with Control Window language)
6. Preserved:
   - 24-page structure
   - safe open route
   - PDF library route
   - governance flags and no-mutation constraints

## Files Changed
- `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_global_selected_matchup_template_path_regression_fix_v1.py`
- `operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`
- `operator_dashboard/test_button2_premium_pdf_full_density_visual_layout_and_content_engine_v1.py`
- `operator_dashboard/test_button2_premium_pdf_final_visual_collision_and_depth_repair_v1.py`
- `scripts/button2_global_selected_matchup_template_path_regression_runtime_proof.py`
- `ops/release_checks/button2_global_selected_matchup_template_path_regression_fix_v1/global_template_path_regression_summary.json`

## Runtime Proof Artifacts
- Summary JSON:
  - `ops/release_checks/button2_global_selected_matchup_template_path_regression_fix_v1/global_template_path_regression_summary.json`
- Visual proof directory:
  - `ops/release_checks/button2_global_selected_matchup_template_path_regression_fix_v1/visual_proof/`

## Generated PDFs
- `reports/nadaka_yoshinari_vs_songchainoi_kiatsongrit_one_samurai_1_premium.pdf`
- `reports/rico_verhoeven_vs_tariq_osaro_glory_100_premium.pdf`
- `reports/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf`
- `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium.pdf`

## Validation
Executed tests:
- `operator_dashboard/test_button2_global_selected_matchup_template_path_regression_fix_v1.py`
- `operator_dashboard/test_button2_jbalia_reference_layout_parity_repair_v1.py`
- `operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`
- `operator_dashboard/test_button2_premium_pdf_full_density_visual_layout_and_content_engine_v1.py`
- `operator_dashboard/test_button2_selected_matchup_ares_24_section_customer_ready_parity_v1.py`
- `operator_dashboard/test_button2_customer_facing_defaults_cleanup_and_reference_report_parity_v1.py`
- `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`

Result:
- All listed tests passed.

Runtime proof summary flags:
- `all_24_pages: true`
- `all_required_present: true`
- `all_forbidden_absent: true`
- `all_open_routes_200: true`
- `all_template_pack_root_matches: true`
- `all_governance_false: true`

## Governance Confirmation
All runtime proof rows report these flags as false:
- `delivery_performed`
- `external_api_delivery_performed`
- `queue_write_performed`
- `learning_apply_performed`
- `calibration_write_performed`
- `button3_mutation_performed`
