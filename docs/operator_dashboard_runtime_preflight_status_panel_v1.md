# operator-dashboard-runtime-preflight-status-panel-v1

## Objective
Add a display-only runtime preflight panel to the main dashboard so operators can verify startup readiness immediately.

## Scope
Display-only runtime readiness signals at dashboard load:
- BUTTON2_PDF_OUTPUT_ROOT
- MSYS2 / GTK DLL path
- WeasyPrint render readiness
- reports output directory
- safe PDF open route availability
- current server port

## Implementation
- Added backend runtime preflight builder in `operator_dashboard/app.py`.
- Passed `runtime_preflight` into `index.html` render context.
- Added panel `Runtime Preflight Status (Display-Only)` in `operator_dashboard/templates/index.html`.
- Existing runtime warning remains for missing output root.

## Guarantees
No behavior changes to generation or routing flows:
- No auto-generation
- No auto-delivery
- No queue mutation
- No learning/calibration mutation
- No Button 3 mutation
- No Button 1 discovery changes

## Tests
Added:
- `operator_dashboard/test_operator_dashboard_runtime_preflight_status_panel_v1.py`

Validated:
- panel presence on load
- required signal labels present
- safe PDF open route label/value rendered
- current server port rendered
- missing output root warning and MISSING status rendered
