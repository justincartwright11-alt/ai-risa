# Release Checklist: Standardized Report Pipeline

Before tagging or distributing a release, run the following:

1. **Contract Check**
   - Run: `py -3.10 check_prediction_contract.py predictions/van_taira_baseline.json predictions/volkov_cortes_baseline.json predictions/volkov_cortes_sens2.json predictions/muhammad_bonfim_baseline.json predictions/muhammad_bonfim_sens2.json`
   - All files must pass.

2. **Presentation Regression**
   - Run: `py -3.10 test_presentation_regression.py`
   - All checks must pass.

3. **Export Smoke Tests**
   - Run: `run_report_validation.bat`
   - All steps must pass.

4. **Batch Export**
   - Run: `py -3.10 batch_export_reports.py`
   - Confirm all outputs are written to `deliveries/v100-template-standardized/<fixture_slug>/` with deterministic filenames.

5. **Spot-Check Outputs**
   - Verify section and visual slot order in Markdown and PDF.
   - Confirm placeholders appear where data is absent.
   - Confirm no schema drift or unexpected changes.

6. **Tag Release**
   - Tag only after all checks pass.

---

**Never edit `execute_risa_v40` or engine scoring on this branch.**
**Never change the presentation schema except in a new, explicitly scoped branch.**
