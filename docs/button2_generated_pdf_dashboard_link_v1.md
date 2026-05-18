# button2-generated-pdf-dashboard-link-v1

## Objective
Add a safe dashboard link after successful Button 2 guarded PDF generation so the operator can open the generated PDF directly from the dashboard without enabling delivery, email, or external API actions.

## Scope
- Add safe Flask open route for generated PDFs.
- Add guarded-generation response fields for dashboard link rendering.
- Add Button 2 dashboard success-link rendering.
- Add tests for route safety and response/UI wiring.

## Route Added
- `GET /api/button2/generated-report/open?filename=<pdf_filename>`

### Route Safety Controls
- Accepts `filename` only (no raw absolute path).
- Rejects:
  - path separators (`/`, `\\`)
  - `..`
  - leading dot filenames
  - non-`.pdf` extensions
  - disallowed characters outside `[A-Za-z0-9._-]`
- Resolves against `BUTTON2_PDF_OUTPUT_ROOT` only.
- Uses safe Flask helper `send_from_directory`.
- Returns:
  - `400` for invalid filename or unavailable output root
  - `404` for missing file

## Guarded Generation Response Extension
On successful guarded generation:
- `output_filename`
- `pdf_open_url`

Example:
- `pdf_open_url: /api/button2/generated-report/open?filename=anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf`

## Dashboard UI Update
In Button 2 success status, show:
- success message
- output path
- output filename
- link label: `Open Generated PDF`

Link is rendered only for successful generation responses that include `pdf_open_url`.

## Governance Confirmation
- No auto-delivery added.
- No email send path added.
- No external API delivery added.
- No queue writes added.
- No learning/calibration writes added.
- No Button 3 mutation added.
- Operator approval gate remains required.

## Validation Summary
- Added route safety tests for:
  - valid existing PDF serving
  - path traversal rejection
  - non-PDF rejection
  - missing file rejection
  - missing output-root rejection
- Updated guarded-generation route tests for:
  - `output_filename` present on success
  - `pdf_open_url` present on success
  - dashboard label `Open Generated PDF` wired in template
