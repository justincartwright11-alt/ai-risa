# Button 2 Governed Internal PDF Artifact Inspection Live Route Proof

## Purpose

This record locks live localhost evidence for the read-only governed internal PDF artifact inspection endpoint. It records proof only and grants no additional implementation, mutation, release, deployment, or lifecycle authority.

## Locked implementation

- Implementation commit: `b517d8952b395074b95afdb24d23621f1d4efc66`
- Branch: `ai-risa-mainline`
- Endpoint: `POST /api/button2/governed-internal-pdf/inspect-v1`
- Planner: `build_button2_governed_internal_pdf_inspection_plan_v1`
- Adapter: `inspect_button2_governed_internal_pdf_artifact_v1`

## Proof environment

- Local fixture mode was enabled.
- The governed fixture source was validated.
- An external temporary output root was used outside the repository.
- Flask ran only at `http://127.0.0.1:5050`.
- The initial worktree contained 91 unrelated dirty entries.
- Those entries were preserved.

## Request contract

The endpoint request contained exactly:

- `fixture_id`
- `report_id`
- `report_version`

It did not contain an output root, output path, filename, overwrite, archive, removal, rename, regeneration, customer-ready authority, customer-release authority, or arbitrary report content.

## Absent-route proof

The absent-target request returned HTTP 200 with:

- `ok=true`
- `status=absent`
- `artifact_state=ABSENT`
- `artifact_exists=false`
- `inspection_performed=true`
- matching fixture, report, and report-version identity
- matching `governed_internal_test_pdf` classification
- generation false
- archive false
- removal false
- overwrite false
- customer release false
- queue write false
- permanent mutation false

## Absent filesystem proof

Before proof setup, the deterministic target did not exist. The output root remained empty. No file or subdirectory was created, no fallback artifact was inspected, and no filesystem mutation occurred.

## Proof-setup render

The existing render adapter was invoked separately from the endpoint solely to create one disposable governed internal PDF for present-target proof. Exactly one deterministic PDF was created inside the external temporary root. It had a valid `%PDF-` signature, non-trivial size, and a returned SHA-256. No second artifact existed.

This controlled setup write was not performed by the inspection endpoint, inspection planner, or inspection adapter.

## Present-route proof

The same request then returned HTTP 200 with:

- `ok=true`
- `status=present_valid`
- `artifact_state=ACTIVE_INTERNAL_TEST_ARTIFACT`
- `artifact_exists=true`
- `inspection_performed=true`
- regular file true
- path contained true
- filename matched true
- PDF signature valid true
- matching fixture identity, report ID, and report version
- matching `governed_internal_test_pdf` classification
- internal-only true
- test-fixture-only true

## Independent artifact verification

Independent verification using `pathlib`, `hashlib`, and `pypdf` confirmed the valid PDF signature, response SHA-256, actual file size, page count, required identity text, and internal-warning text. No OCR was used. The response hash matched the independently calculated hash; the exact transient proof hash was not retained in this closure record.

## Filesystem-disclosure proof

The HTTP response did not expose a proposed output path, proposed output directory, unrestricted output root, absolute target path, customer-directory information, or unrelated filesystem entries. Only bounded filename and artifact metadata were returned.

## Artifact immutability

After inspection, the artifact bytes, SHA-256, size, modification timestamp, filename, and page count were unchanged. Directory contents were unchanged, with no second PDF and no subdirectory created.

## Generation collision invariant

After the deterministic target existed, `build_button2_governed_internal_pdf_preflight_v1` continued to fail closed with `proposed_output_target_exists`. No overwrite authority was granted, no file was modified, and no second artifact was generated. The read-only inspection planner did not weaken generation semantics.

## Safety evidence

The inspection endpoint and inspection adapter result preserved all of these values as false:

```text
customer_ready_possible = false
customer_release_authorized = false
queue_write_performed = false
pdf_generation_performed = false
learning_applied = false
calibration_applied = false
accuracy_ledger_written = false
gcid_written = false
model_weights_changed = false
fighter_ratings_changed = false
prediction_logic_changed = false
artifact_archived = false
artifact_removed = false
artifact_overwritten = false
permanent_mutation_performed = false
```

## Shutdown and cleanup

- Flask stopped.
- Port 5050 was clear.
- The temporary proof root was removed.
- Repository HEAD remained `b517d8952b395074b95afdb24d23621f1d4efc66`.
- Branch remained `ai-risa-mainline`.
- Final status count remained 91.
- No source or proof file was changed during live proof execution.
- No file was staged during live proof execution.
- No commit or tag was created during live proof execution.

## Limitations

This proof covered a fictional governed fixture and a localhost read-only endpoint only. It did not add dashboard status control or authorize customer-ready classification, customer release, archive, removal, deletion, rename, movement, copy, overwrite, regeneration, lifecycle-state persistence, caller-controlled paths, canonical queue or report-ledger writes, learning, calibration, accuracy-ledger persistence, GCID persistence, or deployment.

## Closure verdict

BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_INSPECTION_LIVE_ROUTE_PROOF=PASS
