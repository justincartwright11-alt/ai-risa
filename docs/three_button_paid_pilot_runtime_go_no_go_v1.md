# three-button-paid-pilot-runtime-go-no-go-v1

## Slice Intent
Runtime GO/NO-GO paid-pilot rehearsal evidence only.
No feature additions, no redesign, no approval-gate weakening, no delivery automation, no learning/calibration writes.

## Baseline
- Button 2 repair baseline commit: `1cd6917`
- Button 2 repair baseline tag: `button2-real-queue-multiselect-and-bulk-pdf-generation-repair-v1`
- Button 2 usability polish commit: `14a1350`
- Button 2 usability polish tag: `button2-real-queue-bulk-generation-operator-usability-polish-v1`

## Runtime
- Dashboard URL: `http://127.0.0.1:5050/`
- Runtime port: `5050`
- BUTTON2_PDF_OUTPUT_ROOT: `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports`
- Stale port process handling: executed before run (clean start)

## Validation Tests
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q` -> `16 passed`
- `python -m pytest operator_dashboard/test_button2_real_queue_bulk_generation_operator_usability_polish_v1.py -q` -> `10 passed`
- Focused backend smoke: `python -m pytest operator_dashboard/test_button1_to_button2_readonly_dossier_handoff_api_smoke_v1.py -q` -> `2 passed`

## Button 1 Proof
- Button 1 panel visible in runtime: `true`
- Source-backed event card surface visible with runtime preview data.
- Evidence includes approved-source rows and event cards in panel text.
- Explicit preview/write-closed indications present:
  - `Live write disabled: Yes`
  - `No auto-save: Yes`
  - `Operator approval required: Yes`
  - `Read-only warning: Export disabled. Delivery disabled. File write disabled.`
- No explicit queue save approval action was executed in this slice.

## Button 2 Proof
- Button 2 opened successfully.
- Refresh Queue loaded canonical queue rows from real source (`queueRowsLoaded=6`, source-backed rows present).
- Queue controls visible:
  - Refresh Queue
  - Select All Ready
  - Clear Selection
  - Select Event Card
  - Generate Selected PDFs
- Single ready selection run:
  - requested=1, generated=1, failed=0, skipped=0
  - generated output path present in status panel.
- Multi-ready selection run:
  - requested=3, generated=3, failed=0, skipped=0
  - multiple output paths present in status panel.
- Select All Ready:
  - selected summary updated to `selected_rows=6`, `ready_selected=6`.
- Open PDF links:
  - two separate generated links verified as HTTP 200 with `application/pdf`.
- Row-level status/readability:
  - generated rows show `Generated`
  - non-generated rows remain clearly non-generated
  - result panel contains `Failed or skipped rows` section and clear reasons when applicable.

## Generated PDF Proof Paths
- `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\sean_strickland_vs_dricus_du_plessis_ufc_304_premium_20260519T101243Z_4c5e96745953.pdf`
- `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\ryan_curtis_vs_adam_borics_bellator_298_premium_20260519T101243Z_93cdf4353935.pdf`
- `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\zebaztian_kadestam_vs_john_kavanagh_one_169_premium_20260519T101243Z_6f72e7812807.pdf`

## PDF Text Extraction Proof
Extraction performed on at least two generated outputs via runtime extraction helper.

- PDF 1 matchup check (`Sean Strickland` vs `Dricus du Plessis`): `pass`
- PDF 2 matchup check (`Ryan Curtis` vs `Adam Borics`): `pass`
- PDF texts differ across outputs: `pass`
- Page counts observed: `24` and `24`

Representative snippets:
- PDF 1: `...Sean Strickland ... Dricus du Plessis ... UFC 304 ...`
- PDF 2: `...Ryan Curtis ... Adam Borics ... Bellator 298 ...`

## Button 3 Proof
- Button 3 panel visible in runtime: `true`
- Read-only preview executed via UI.
- Preview status language confirms non-mutation path:
  - `Preview-only comparison path: no apply, no learning, no calibration, no queue mutation, no external delivery/API.`
- Local preview summary confirms approval gate remains in flow (`Gate required: Yes`).

## Governance Proof
Confirmed false from live API evidence (Button 2 generation response):
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

Button 3 preview response confirms:
- `preview_only=true`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `queue_write_performed=false`
- `button3_mutation_performed=false`

## Operator Usability Proof
- Three main buttons visible in normal dashboard.
- Button 2 queue controls visible and actionable.
- Generate Selected PDFs visible and functional.
- Open PDF links visible and resolvable.
- Failed/skipped section present with reason surface.
- No extra debug-only controls introduced into normal 3-button panel.

## Blockers
- No hard blocker found for paid-pilot runtime rehearsal.
- Non-blocking caveat: runtime preflight still shows WeasyPrint import warning in this environment, but required Button 2 generation and PDF-open proof succeeded with configured output root.

## Verdict
**GO**

Rationale: required runtime rehearsal steps completed, governance remained closed, Button 2 generated and validated multiple queue-driven PDFs, Button 3 remained preview-only and gate-bound, and no hard blocker prevented paid-pilot operation within defined constraints.
