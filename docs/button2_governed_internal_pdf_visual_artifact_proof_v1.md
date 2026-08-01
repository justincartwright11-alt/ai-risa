# Button 2 Governed Internal PDF Visual Artifact Proof v1

## 1. Purpose

This record locks the structural, textual, visual, containment, and cleanup evidence for one governed fictional internal PDF artifact.

## 2. Locked implementation

- Render-adapter commit: `1d618f8`
- Preflight-adapter commit: `b7d6cf8`
- Branch: `ai-risa-mainline`

## 3. Artifact identity

- Filename: `internal_fixture_report_closed_loop_v1__DRAFT_INTERNAL_FIXTURE_v1.pdf`
- Classification: fixture-only fictional artifact
- Fixture identity: `closed_loop_governed_local_fixture_v1`
- Report ID: `internal_fixture_report_closed_loop_v1`
- Report version: `DRAFT_INTERNAL_FIXTURE_v1`
- Artifact classification: `governed_internal_test_pdf`

## 4. Preflight evidence

Before rendering:

- Preflight passed.
- `customer_ready_possible = false`
- `customer_release_authorized = false`
- `overwrite_allowed = false`
- `pdf_generation_performed = false`
- The proposed output path was contained inside the external temporary proof root.

## 5. Structural PDF evidence

- Exactly one PDF was generated.
- File size: `11,094 bytes`
- Page count: `1`
- `%PDF-` signature: valid
- SHA-256: `8b9ba89a04b2884313605b1c48e551ce8dc6176d3c2f228eea8587c0b8b19533`
- The returned hash matched the independently calculated hash.
- Exactly one PDF existed in the proof root.

## 6. Extracted-text evidence

Extracted text contained:

- `INTERNAL TEST FIXTURE`
- `NOT FOR CUSTOMER RELEASE`
- AI-RISA identity
- Fixture identity
- Report ID
- Report version
- `Fictional Fighter Alpha`
- `Fictional Fighter Beta`
- Structured prediction information
- Prediction schema/version
- Source provenance
- Report or prediction provenance
- Governed internal test PDF classification
- Customer-release false limitation

Extracted text did not claim:

- Customer ready
- Customer released
- Production approved
- Production validated
- Official commercial report

## 7. Visual QA evidence

The single page was rendered to PNG using PyMuPDF at 180 DPI.

Visual findings:

- No clipped heading
- No clipped footer or page-edge content
- No overlapping text
- No broken glyphs
- No missing fighter names
- No missing internal/test warning
- No blank or duplicated page
- Typography readable
- Spacing adequate
- Heading hierarchy coherent
- Report identity/version legible
- Provenance legible
- Internal/test classification prominent
- `NOT FOR CUSTOMER RELEASE` prominent

`VISUAL_DEFECT_COUNT=0`

## 8. Safety evidence

- `internal_only = true`
- `test_fixture_only = true`
- `customer_ready_possible = false`
- `customer_release_authorized = false`
- `queue_write_performed = false`
- `pdf_generation_count = 1`
- `artifact_overwritten = false`
- `permanent_mutation_performed = false`
- `learning_applied = false`
- `calibration_applied = false`
- `accuracy_ledger_written = false`
- `gcid_written = false`
- `model_weights_changed = false`
- `fighter_ratings_changed = false`
- `prediction_logic_changed = false`

The single controlled PDF write was limited to the external temporary proof directory and was not a governed system or database mutation.

## 9. Containment and cleanup

- Output root: `C:\Users\jusin\AppData\Local\Temp\ai_risa_button2_governed_internal_pdf_visual_proof_v1`
- One PDF and one rendered PNG were confined to that root.
- No output was written into the repository.
- The proof directory was removed after inspection.
- No repository file was edited, staged, committed, or tagged during proof execution.

## 10. Limitations

- Fictional fixture only
- Internal/test artifact only
- No dashboard route integration
- No customer-ready classification
- No customer release
- No production generation authority
- No bulk generation authority
- No canonical output-directory authority
- No queue or report-ledger persistence
- No learning or calibration authority
- No accuracy-ledger or GCID persistence
- No deployment authority

## 11. Closure verdict

BUTTON2_GOVERNED_INTERNAL_PDF_VISUAL_ARTIFACT_PROOF=PASS
