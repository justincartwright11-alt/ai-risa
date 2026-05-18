# button3-result-comparison-controlled-preview-dashboard-runtime-confirmation-v1

## Objective
Confirm the newly locked Button 3 controlled preview path works in live runtime conditions with governance flags intact.

## Runtime Confirmation Performed
Environment start:
- Command: `./scripts/start_ai_risa_dashboard_windows.ps1`
- Startup confirmed:
  - dashboard on `http://127.0.0.1:5050`
  - `BUTTON2_PDF_OUTPUT_ROOT` printed on startup

Live checks:
- `GET /` returned 200
- `POST /api/button3/result-comparison/preview-v1` returned 200
- Live route response included:
  - `preview_only=true`
  - `comparison_status=ready_to_compare`
  - `accuracy_preview.winner=hit`
  - `accuracy_preview.overall=hit`
  - `mutation_performed=false`
  - `learning_apply_performed=false`
  - `calibration_write_performed=false`
  - `queue_write_performed=false`
  - `button3_mutation_performed=false`
- Dashboard HTML includes preview-only language:
  - `Preview-only comparison path`

## Governance Outcome
No apply endpoint was opened for result comparison.
No learning/calibration path was opened.
No durable mutation path was opened.

## Notes
A browser automation click on Button 3 timed out in the shared-page tool state, but runtime confirmation succeeded via live HTTP checks and route execution.
