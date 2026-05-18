# button2-generated-pdf-dashboard-link-live-ui-repair-v1

## Objective
Repair live dashboard rendering so successful Button 2 generation visibly shows clickable `Open Generated PDF` link.

## Root Cause
- Backend response fields were present in successful guarded-generation responses (`output_filename`, `pdf_open_url`).
- Frontend link rendering condition was stricter than required: it required both `pdf_open_url` and `output_filename` before rendering link.
- In live conditions where `pdf_open_url` existed but filename handling was inconsistent at render time, link could be suppressed.

## Fix
- Updated Button 2 result renderer in dashboard JS:
  - render anchor whenever `pdf_open_url` exists
  - keep filename display optional
  - keep link rendering inside success branch only
- Safe route unchanged:
  - `/api/button2/generated-report/open?filename=<pdf_filename>`

## Safety/Governance
- No delivery logic changed.
- No email/external API/queue mutation logic changed.
- No learning/calibration logic changed.
- No Button 1 and Button 3 behavior changed.
- Operator approval gate unchanged.

## Runtime Diagnostics
- Guarded route response (test-client diagnostic) confirms:
  - `ok=true`
  - `output_path` present
  - `output_filename` present
  - `pdf_open_url` present
- Live safe-route check attempted on localhost returned 404 at time of check (environment/runtime state issue), while route logic and tests validate safe serving behavior.

## Tests
- Added focused test file:
  - `operator_dashboard/test_button2_generated_pdf_dashboard_link_live_ui_repair_v1.py`
- Coverage includes:
  - successful response includes `pdf_open_url` and `output_filename`
  - dashboard renderer contains clickable anchor logic
  - fallback behavior based on `pdf_open_url`
  - failure branch remains no-link
  - safe route serves existing file
  - safe route rejects traversal and non-PDF
  - governance flags remain false
