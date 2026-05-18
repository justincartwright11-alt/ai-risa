# operator-dashboard-windows-launch-script-and-runtime-env-guard-v1

## Objective
Ensure AI-RISA dashboard starts correctly on Windows with required runtime environment for Button 2 PDF generation and WeasyPrint dependencies.

## Delivered
- Added Windows launcher script:
  - `scripts/start_ai_risa_dashboard_windows.ps1`
- Added lightweight runtime warning surface on dashboard:
  - `PDF output root missing - start dashboard with Windows launch script.`
- Warning appears only when `BUTTON2_PDF_OUTPUT_ROOT` is missing.

## Launcher Behavior
The launch script sets:
- repository root to `C:\Users\jusin\OneDrive\Documents\Custom Office Templates`
- `PATH` with `C:\msys64\ucrt64\bin` prepended
- `PYTHONDONTWRITEBYTECODE=1`
- `BUTTON2_PDF_OUTPUT_ROOT=C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports`
- Python runtime `C:\Users\jusin\AppData\Local\Python\pythoncore-3.14-64\python.exe`

And starts app via:
- `os.add_dll_directory(r'C:\msys64\ucrt64\bin')`
- `from operator_dashboard.app import app`
- `app.run(debug=False, port=5050)`

## Safety / Governance
No changes were made to:
- delivery behavior
- email behavior
- external API delivery behavior
- queue mutation behavior
- learning/calibration behavior
- Button 3 mutation behavior
- report generation logic
- source discovery logic

## Tests
Added:
- `operator_dashboard/test_operator_dashboard_windows_launch_script_and_runtime_env_guard_v1.py`

Validation includes:
- launch script exists
- launch script includes `BUTTON2_PDF_OUTPUT_ROOT`
- launch script includes `C:\msys64\ucrt64\bin`
- launch script includes `os.add_dll_directory`
- missing output-root warning text exists
- warning is absent when output root is configured
