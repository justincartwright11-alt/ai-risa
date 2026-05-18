# button2-selected-matchup-guarded-pdf-generation-runtime-confirmation-v1

## Scope
- Real localhost runtime confirmation for Button 2 selected-matchup guarded PDF generation.
- Confirms Button 1 selection to Button 2 guarded generation works end-to-end in the configured dashboard runtime.
- Governance preserved: no auto-delivery, no queue write, no learning/calibration, no Button 3 mutation.

## Source Dependency Checkpoint
- `button2-selected-matchup-pdf-render-runtime-dependency-confirmation-v1`

## Dashboard URL Tested
- `http://127.0.0.1:5050/`

## Runtime Path Confirmed
1. Live dashboard root loaded at localhost.
2. Button 1 runtime preview returned full-card event rows.
3. Full-card event cards remained visible in runtime payload (`full_card_confirmed` count = 4).
4. Explicit selection preview succeeded from Button 1 into Button 2.
5. Guarded Button 2 route called: `/api/button2/selected-matchup/generate-guarded-v1`.
6. PDF generation completed successfully.

## Selected Event And Matchup
- Event: `ONE SAMURAI 1`
- Matchup: `Nadaka vs Songchainoi Kiatsongrit`

## PDF Generation Result
- Result: success
- Message: `PDF generated and saved successfully.`

## PDF Output Path
- `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\nadaka_vs_songchainoi_kiatsongrit_one_samurai_1_premium.pdf`

## PDF File Exists
- `True`

## Governance Flags
- `delivery_performed=False`
- `external_api_delivery_performed=False`
- `queue_write_performed=False`
- `learning_apply_performed=False`
- `calibration_write_performed=False`
- `button3_mutation_performed=False`

## Runtime Environment Requirement
- Flask runtime required GTK DLL availability from `C:\msys64\ucrt64\bin`.
- Flask runtime required `BUTTON2_PDF_OUTPUT_ROOT` to be set to an absolute output directory.
- Successful localhost confirmation used an app-process bootstrap with:
  - `os.add_dll_directory(r'C:\msys64\ucrt64\bin')`
  - `BUTTON2_PDF_OUTPUT_ROOT=C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports`

## AI-RISA Code Change
- Yes.
- Narrow Windows-only runtime bootstrap added in `operator_dashboard/button2_pdf_render_gate_v1.py` so WeasyPrint can register the MSYS2 GTK DLL directory before import.
- Narrow unit coverage added in `operator_dashboard/test_button2_pdf_render_gate_integration_preview_v1.py`.

## Validation
- Live localhost runtime confirmation: passed
- Focused tests:
  - `operator_dashboard/test_button2_explicit_operator_generate_from_selected_matchup_guarded_v1.py`
  - `operator_dashboard/test_button2_pdf_render_gate_integration_preview_v1.py`
  - `operator_dashboard/test_button2_pdf_output_root_config_preview_v1.py`
  - `operator_dashboard/test_button1_button2_event_card_matchup_selector_v1.py`
- Result: `78/78 passed`

## Next Safe Recommendation
- Persist `BUTTON2_PDF_OUTPUT_ROOT` in the runtime environment used to launch AI-RISA for future operator sessions.
- Restart VS Code before additional live dashboard runs so the runtime environment remains consistent.
