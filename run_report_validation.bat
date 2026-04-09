@echo off
REM Unified validation runner for standardized report pipeline

REM 1. Contract check
py -3.10 check_prediction_contract.py predictions/van_taira_baseline.json predictions/volkov_cortes_baseline.json predictions/volkov_cortes_sens2.json predictions/muhammad_bonfim_baseline.json predictions/muhammad_bonfim_sens2.json || exit /b 1

REM 2. Presentation regression
py -3.10 test_presentation_regression.py || exit /b 1

REM 3. Markdown export smoke test
py -3.10 -c "import json; from ai_risa_report_output_adapter import map_engine_output_to_report; from ai_risa_report_exporter import export_report; d=json.load(open('predictions/van_taira_baseline.json','r',encoding='utf-8')); report=map_engine_output_to_report(d); export_report(report, 'predictions/van_taira_visuals.md', fmt='md')" || exit /b 1

REM 4. PDF export smoke test
py -3.10 -c "import json; from ai_risa_report_output_adapter import map_engine_output_to_report; from ai_risa_report_exporter import export_report; d=json.load(open('predictions/van_taira_baseline.json','r',encoding='utf-8')); report=map_engine_output_to_report(d); export_report(report, 'predictions/van_taira_visuals.pdf', fmt='pdf')" || exit /b 1

echo All report pipeline validation checks passed.
