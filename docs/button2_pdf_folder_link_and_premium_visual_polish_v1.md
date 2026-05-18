# button2-pdf-folder-link-and-premium-visual-polish-v1

## Objective
Deliver a safe, operator-facing PDF library route and a premium visual polish upgrade for the selected-matchup Button 2 PDF output.

## Scope Implemented
- Added safe read-only PDF library route: `GET /api/button2/generated-report/library`.
- Route lists only `.pdf` files from configured `BUTTON2_PDF_OUTPUT_ROOT`.
- Route fails closed if output root is unavailable.
- Route rejects directory override query (`path`, `dir`, `folder`).
- Each row links through existing safe open endpoint: `/api/button2/generated-report/open?filename=...`.
- Added dashboard links in Button 2 panel:
  - `PDF Reports Folder`
  - `Open PDF Reports Library` after successful generation.
- Upgraded report composition visuals to premium dark-branded card layout with:
  - stronger cover presentation,
  - executive dashboard cards,
  - tactical/risk/energy/mental signal bars,
  - scenario pathway cards,
  - styled source traceability grid,
  - styled `Operator Traceability Appendix`.

## Governance and Safety
- No arbitrary filesystem browsing.
- No upload/delete/rename actions added.
- Library route remains read-only.
- Existing guarded generation governance flags preserved.

## Test Coverage Added
- New focused suite: `operator_dashboard/test_button2_pdf_folder_link_and_premium_visual_polish_v1.py`
  - Dashboard link presence.
  - Safe library listing behavior and newest-first order.
  - Query override rejection.
  - HTML composition premium marker assertions.
  - Guarded generation PDF page-count floor (`>=12`) and appendix marker.

## Runtime Confirmation Notes
- Library route intended to be opened from dashboard link, not raw filesystem path.
- Generated PDF open flow continues through safe route-only link policy.
