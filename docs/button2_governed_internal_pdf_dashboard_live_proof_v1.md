# Button 2 Governed Internal PDF Dashboard Live Proof

## Purpose

This record locks end-to-end localhost operator evidence for the governed Button 2 internal fictional PDF dashboard workflow.

## Locked implementation

- Implementation commit: `ae3d24a3b5689eb1d493df08af8d8fa84323693d`
- Branch: `ai-risa-mainline`
- Route: `POST /api/button2/governed-internal-pdf/generate-v1`
- Dashboard control: `Generate Internal Test PDF`

## Proof environment

- Local fixture mode enabled.
- Governed fixture file validated.
- External temporary output root used.
- Output root existed outside the repository.
- Flask ran only on `http://127.0.0.1:5050`.

## Queue-response proof

- HTTP 200.
- `ready_count=0`.
- `internal_preview_count=1`.
- Exactly one governed internal-preview row.
- Fixture ID: `closed_loop_governed_local_fixture_v1`.
- `fixture_only=true`.
- Report ID: `internal_fixture_report_closed_loop_v1`.
- Report version: `DRAFT_INTERNAL_FIXTURE_v1`.
- Internal-only true.
- Test-fixture-only true.
- Read-only true.
- Structured prediction present.
- Prediction schema/version present.
- Source provenance present.
- Prediction/report provenance present.
- Customer-ready false.
- Customer-release false.
- Queue-write false.

## Internal-preview selection proof

- Governed preview rendered successfully.
- Fictional Fighter Alpha and Fictional Fighter Beta appeared.
- Selection for internal PDF succeeded.
- No required-metadata error appeared.
- Selected state preserved fixture ID, fixture-only governance, report ID, and report version.
- Selection alone sent no generation request.
- Customer batch selection remained unchanged.
- Button 3 selected-report state remained unchanged.

## Warning and acknowledgement proof

The panel displayed:

- `INTERNAL TEST FIXTURE`.
- `NOT FOR CUSTOMER RELEASE`.
- Internal/test classification.
- Customer ready false.
- Customer release false.
- Configured internal-output status.

The proof also established:

- No unrestricted absolute output path was displayed.
- Acknowledgement was unchecked by default.
- Generation was disabled without acknowledgement.
- Generation became enabled only after acknowledgement.
- Acknowledgement did not grant customer-ready or release authority.

## Generation request proof

Exactly one POST was sent to:

`/api/button2/governed-internal-pdf/generate-v1`

The request contained only:

- `fixture_id`.
- `report_id`.
- `report_version`.
- `internal_test_artifact_acknowledged = true`.

The request did not contain:

- Output root.
- Output path.
- Filename.
- Extension.
- Overwrite.
- Customer-ready authority.
- Customer-release authority.
- Arbitrary report content.

## Generation response proof

- HTTP 200.
- `ok=true`.
- Status: `generated_governed_internal_test_pdf`.
- PDF generation count: `1`.
- Artifact classification: `governed_internal_test_pdf`.
- Customer-ready false.
- Customer-release false.
- Queue-write false.
- Overwrite false.
- Permanent mutation false.

## Artifact verification

- Exactly one PDF.
- File size: `11,094 bytes`.
- Page count: `1`.
- Valid `%PDF-` signature.
- SHA-256: `8b9ba89a04b2884313605b1c48e551ce8dc6176d3c2f228eea8587c0b8b19533`.
- Independently calculated hash matched.
- Extracted text contained `INTERNAL TEST FIXTURE`, `NOT FOR CUSTOMER RELEASE`, `AI-RISA`, Fictional Fighter Alpha, Fictional Fighter Beta, the report ID, and the report version.

## Customer-flow isolation

- Customer `ready_count` remained zero.
- Customer selected-row count remained zero.
- Customer batch generation was not called.
- No report became customer ready.
- No customer delivery or release control was enabled.
- Customer result state was not modified by internal generation.

## Button 3 isolation

- Button 3 selected-report state remained unchanged.
- Internal PDF generation did not select, clear, or replace Button 3 state.
- The Button 3 internal-preview selector remained available and separate.

## Duplicate-generation protection

- Generation control was disabled after successful generation.
- Client-side duplicate prevention passed.
- No bypass was used.
- No second PDF was created.
- Original artifact size and SHA-256 remained unchanged.
- No rename, suffix, retry, or overwrite path was offered.

## Safety evidence

```text
customer_ready_possible = false
customer_release_authorized = false
queue_write_performed = false
learning_applied = false
calibration_applied = false
accuracy_ledger_written = false
gcid_written = false
model_weights_changed = false
fighter_ratings_changed = false
prediction_logic_changed = false
artifact_overwritten = false
permanent_mutation_performed = false
```

## Shutdown and cleanup

- Flask stopped cleanly.
- Ctrl+C process-interruption status was expected.
- Port 5050 was clear.
- Temporary output directory was removed.
- No repository artifact was created.
- No source file was edited.
- No file was staged.
- No proof commit or tag was created during live execution.
- Final worktree matched the initial dirty baseline.

## Limitations

- Fictional governed fixture only.
- Internal/test PDF only.
- Localhost operator proof only.
- One deterministic artifact only.
- No customer-ready classification.
- No customer release.
- No production authority.
- No bulk generation.
- No overwrite.
- No caller-controlled path.
- No authorised artifact deletion or archival workflow.
- No canonical queue or report-ledger write.
- No learning or calibration.
- No accuracy-ledger or GCID persistence.
- No deployment authority.

## Closure verdict

BUTTON2_GOVERNED_INTERNAL_PDF_DASHBOARD_LIVE_PROOF=PASS