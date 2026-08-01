# Button 2 Governed Internal PDF Artifact Lifecycle Readiness Assessment

## Executive verdict

READY_WITH_BLOCKERS

The existing governed internal PDF generation contract is sufficiently bounded to design a narrow lifecycle workflow, but AI-RISA is not ready to implement archive, removal, or regeneration mutation. A read-only artifact inspection contract must be defined and proven first.

## Proven baseline

- Dashboard proof closure commit: `ec9ce99874ee9d3648cb005f1263afc8e311cdf9`.
- Implementation commit: `ae3d24a3b5689eb1d493df08af8d8fa84323693d`.
- Governed generation route: `POST /api/button2/governed-internal-pdf/generate-v1`.
- Deterministic filename contract: `{report_id}__{report_version}.pdf`.
- Overwrite is prohibited.
- Duplicate generation is prevented when the deterministic target already exists.
- Customer-ready and customer-release are false.

The live dashboard proof records one governed fictional internal PDF, explicit acknowledgement, metadata and hash verification, duplicate-generation blocking, customer-flow isolation, Button 3 isolation, and cleanup of the external temporary proof root.

## Existing artifact contract

The inspected preflight, renderer, route, dashboard, and focused tests establish these current properties:

- Artifact classification is `governed_internal_test_pdf`.
- Source is a fixture-only fictional source.
- Report identity is deterministic and includes fixture ID, report ID, and report version.
- Filename is deterministic: `{report_id}__{report_version}.pdf`.
- The output root is configured server-side through the internal PDF output-root configuration.
- The renderer performs exactly one controlled PDF write after successful preflight.
- The response includes SHA-256 metadata.
- The response includes file-size metadata.
- The renderer verifies the `%PDF-` signature before writing.
- The caller cannot provide an output root, output path, filename, extension, or overwrite option in the generation request.
- Overwrite is not allowed.
- Automatic rename, suffixing, and retry are not provided.
- No lifecycle mutation contract exists.

The preflight validates fixture authority flags, identity safety, root validity, target containment, and target absence. The renderer rechecks identity, classification, containment, root existence, and target absence before the controlled write.

## Lifecycle problem statement

Once the deterministic target exists, another generation request is blocked with `proposed_output_target_exists`. This is correct for safety: it protects the original artifact from overwrite, silent replacement, and accidental duplicate output.

Repeated governed use therefore requires a separate authorised lifecycle process. Generation code must not acquire implicit delete, archive, rename, overwrite, or regeneration authority merely because a target collision exists.

## Proposed lifecycle states

The following are non-authoritative design states only:

- `ABSENT`
- `ACTIVE_INTERNAL_TEST_ARTIFACT`
- `RETAINED`
- `ARCHIVE_ELIGIBLE`
- `ARCHIVED`
- `REMOVAL_ELIGIBLE`
- `REMOVED`
- `REGENERATION_ELIGIBLE`
- `BLOCKED`

These states do not yet exist in runtime. They must not be inferred as permission to mutate the filesystem or any ledger.

## Artifact discovery boundary

A future read-only inspection contract may verify only:

- The configured internal output root.
- The deterministic expected target.
- Whether that target exists.
- File type.
- Filename.
- Size.
- SHA-256.
- PDF signature.
- Report ID and report version.
- Artifact classification.

It must prohibit arbitrary directory browsing, recursive filesystem scanning, caller-supplied paths, customer-directory inspection, canonical queue inspection, and automatic deletion. On Windows, the contract must explicitly account for symbolic-link and reparse-point risks before treating a target as contained and eligible for any future action.

## Retention classification

Possible internal retention categories are:

- Ephemeral proof artifact.
- Retained internal evidence.
- Superseded internal artifact.
- Invalid or corrupt artifact.
- Archive candidate.

An operator must explicitly classify the artifact. This assessment does not prescribe retention periods because no applicable repository retention policy was established by the inspected files.

## Archive boundary

A future archive action should require explicit operator acknowledgement and remain internal/test-only. It should:

- Use a configured server-side archive root.
- Preserve the original filename or use a deterministic archival envelope.
- Preserve the source SHA-256.
- Record source and destination evidence.
- Refuse destination collisions.
- Refuse customer and canonical directories.
- Avoid silent overwrite.

Archive behavior is not implemented or authorised by this assessment.

## Removal boundary

Any future removal would require:

- Explicit operator approval.
- The exact deterministic target only.
- Pre-removal signature and hash verification.
- Fixture and report identity matching.
- No wildcard or recursive delete.
- No caller-provided path.
- No customer or canonical directory access.
- No deletion after failed verification.
- Post-removal absence verification.
- An evidence record.
- No automatic regeneration.

Permanent deletion should not be the default. Archive-first should be mandatory unless a separately authorised governance decision explicitly permits permanent removal for a defined internal/test case.

Removal behavior is not implemented or authorised by this assessment.

## Regeneration eligibility

Regeneration may become eligible only after:

- The previous artifact is absent through an authorised lifecycle operation.
- The configured output root remains valid.
- Fixture and report identity remain unchanged or are explicitly versioned.
- Operator acknowledgement is renewed.
- Preflight passes again.
- No overwrite authority is introduced.

An existing target must never be made regenerable by silently renaming, suffixing, overwriting, or retrying the generation request.

## Corrupt or mismatched-artifact handling

If the deterministic target is not a PDF, has an invalid signature, has an unexpected SHA-256, contains the wrong report identity or version, has an unexpected classification, is outside the approved root, or presents a symbolic-link or Windows reparse-point risk, the future workflow must fail closed.

No automatic repair, deletion, replacement, rename, archive, or regeneration may occur after failed verification. The result must expose a bounded blocked reason for operator review.

## Operator interface requirements

The minimum future UI should provide:

- Bounded artifact-present status.
- Filename.
- Size.
- SHA-256.
- Signature status.
- Report identity and version.
- Classification.
- Retention state.
- Explicit acknowledgement.
- `Archive Internal Test PDF` only when separately authorised.
- `Remove Internal Test PDF` only when separately authorised.
- No customer delivery.
- No unrestricted absolute path.
- No generic `Delete` button.
- Plain-language blocked reasons.

The current UI provides internal/test warnings, identity, configured-output status, acknowledgement, generation, result metadata, and collision messaging, but no lifecycle controls or artifact-status inspection panel.

## Audit evidence requirements

A future evidence record should contain:

- Operator action.
- Timestamp.
- Fixture and report identity.
- Artifact classification.
- Pre-action path-containment result.
- Pre-action SHA-256.
- Pre-action signature result.
- Action result.
- Post-action existence state.
- Archive destination evidence, if applicable.
- Customer release false.
- Queue write false.
- Permanent mutation classification.

The first inspection slice may return this evidence response-only if that is the authorised contract. Append-only persistence would be a separate mutation and requires separate authority, file scope, and validation.

## Mutation classification

- Archive is filesystem mutation.
- Removal is filesystem mutation.
- Regeneration after authorised removal is a new filesystem write.
- Audit-ledger persistence is a separate mutation.

None of these actions are authorised by this assessment.

## Proven blockers

### No read-only artifact-status endpoint

- Owning file: `operator_dashboard/app.py`.
- Owning section: governed internal PDF generation route.
- Observed limitation: the inspected route only accepts a generation POST; it does not expose bounded status for an existing deterministic artifact.
- Safety consequence: the operator cannot obtain a governed lifecycle status without entering generation flow.
- Smallest future remediation: add a separate read-only inspection adapter and narrowly scoped status endpoint that inspects only the expected target.

### No archive contract

- Owning files: `operator_dashboard/app.py`, `operator_dashboard/button2_governed_internal_pdf_render_adapter_v1.py`.
- Owning sections: governed generation route and single-write renderer.
- Observed limitation: no archive root, destination identity, collision policy, acknowledgement contract, or archive evidence exists.
- Safety consequence: archive behavior could otherwise introduce uncontrolled movement or overwrite authority.
- Smallest future remediation: define an archive-only contract in a separate design and authorization slice before implementation.

### No removal contract

- Owning file: `operator_dashboard/app.py`.
- Owning section: governed internal PDF generation route.
- Observed limitation: the route blocks an existing target and has no exact-target removal operation.
- Safety consequence: adding deletion ad hoc could permit path escape, wildcard deletion, or deletion after failed verification.
- Smallest future remediation: define exact-target, archive-first removal rules and a separate mutation authorization gate.

### No lifecycle state

- Owning files: `operator_dashboard/app.py`, `operator_dashboard/templates/index.html`.
- Owning sections: generation response and internal preview control.
- Observed limitation: runtime exposes generation and blocked-collision results but no lifecycle state model or retention classification.
- Safety consequence: archive, removal, and regeneration eligibility cannot be represented consistently.
- Smallest future remediation: add state derivation to the read-only inspection contract without granting mutation authority.

### No audit record

- Owning files: `operator_dashboard/app.py`, `operator_dashboard/templates/index.html`.
- Owning sections: generation route and dashboard result rendering.
- Observed limitation: the current response exposes safety metadata, but no lifecycle action evidence or append-only record contract exists.
- Safety consequence: future mutation actions would lack a defined operator and post-action evidence trail.
- Smallest future remediation: specify response-only evidence first; separately authorize persistence if required.

### No lifecycle UI controls

- Owning file: `operator_dashboard/templates/index.html`.
- Owning section: governed internal PDF control.
- Observed limitation: the UI contains acknowledgement and generation controls, but no bounded artifact status, retention classification, archive action, or authorised removal action.
- Safety consequence: operators have no governed interface for lifecycle review.
- Smallest future remediation: expose read-only inspection status before adding any mutation control.

### No path-safe lifecycle mutation tests

- Owning files: `operator_dashboard/test_button2_governed_internal_pdf_route_integration_v1.py`, `operator_dashboard/test_button2_governed_internal_pdf_dashboard_exposure_v1.py`.
- Owning sections: route and dashboard contract tests.
- Observed limitation: tests cover fixture validation, deterministic generation, collision blocking, cleanup on render failure, and dashboard exposure, but no archive/removal path-containment or lifecycle-state tests exist.
- Safety consequence: mutation behavior would be unproven and could weaken the current fail-closed boundary.
- Smallest future remediation: add focused inspection tests before any mutation tests or implementation.

## Recommended sequencing

A. Docs-only lifecycle contract.

B. Read-only artifact inspection adapter.

C. Focused inspection tests.

D. Live read-only proof.

E. Archive/removal readiness gate.

F. Separately authorised mutation adapter.

G. Focused mutation test.

H. Dashboard exposure.

I. Live operator proof.

Inspection and mutation must remain separate implementation slices.

## Smallest next implementation slice

The smallest non-mutating next slice is a read-only governed internal PDF artifact inspection adapter.

Suggested files:

- `operator_dashboard/button2_governed_internal_pdf_artifact_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_artifact_inspection_adapter_v1.py`

The adapter should accept a validated preflight plan or deterministic identity, inspect only the expected target, perform no directory scan, and perform no write, archive, delete, rename, or regeneration. It should return bounded metadata and safety flags.

## Proposed targeted test

Future validation command:

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_artifact_inspection_adapter_v1.py
```

This command must not be run during this assessment.

## Explicit exclusions

This assessment does not authorise:

- Archive execution.
- Deletion.
- Renaming.
- Movement.
- Overwrite.
- Regeneration.
- Customer-ready classification.
- Customer release.
- Production storage.
- Canonical queue writes.
- Report-ledger writes.
- Learning.
- Calibration.
- Accuracy-ledger writes.
- GCID writes.
- Deployment.

## Final verdict

BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_LIFECYCLE=READY_WITH_BLOCKERS