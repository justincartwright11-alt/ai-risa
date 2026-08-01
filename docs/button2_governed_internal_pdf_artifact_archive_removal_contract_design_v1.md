# Button 2 Governed Internal PDF Artifact Archive and Removal Contract Design v1

## 1. Executive status

`CONTRACT_DESIGN_COMPLETE`

This document defines a future governance contract for controlled archive and removal actions on a fictional governed internal/test PDF. Contract completion does not authorise implementation, planning, mutation, persistence, deletion, or release.

## 2. Locked baseline

- Latest lifecycle reassessment commit: `90b8413ce28c0eec7d0deb2f3cee1667d755deee`.
- Inspection dashboard closure: `f48dd2e7027c9e07b3d25ba03eaf2ef0c5839a49`.
- The baseline is a fictional governed fixture only.
- The artifact is internal/test-only, not customer-ready, and not for customer release.
- Current observational states are `ABSENT`, `ACTIVE_INTERNAL_TEST_ARTIFACT`, and `BLOCKED` / `BLOCKED_ARTIFACT`.
- The current inspection chain is read-only. It does not persist lifecycle transitions or provide archive/removal authority.

## 3. Contract purpose

This contract defines future controlled lifecycle actions without granting mutation authority. It establishes the boundaries for:

- archive eligibility;
- removal eligibility;
- operator authorization;
- request identity;
- expected artifact evidence;
- deterministic paths;
- collision behavior;
- audit evidence;
- idempotency;
- bounded response shape; and
- fail-closed behavior.

The contract is design-only. No transition, plan, endpoint, adapter, UI control, audit sink, or filesystem operation is implemented by this document.

## 4. Terminology

**Inspection** reads and verifies the deterministic artifact and performs no mutation.

**Archive** preserves artifact bytes and evidence and transfers the artifact into an approved governed retention boundary. Archive must not silently overwrite or destroy the source.

**Removal** makes the active artifact unavailable from its active location. It may involve deletion, quarantine, or controlled transfer depending on a separately approved policy. Removal is higher risk than archive.

**Deletion** is permanent destruction of bytes. Deletion is not synonymous with removal and is not authorised by this contract unless separately defined and approved.

**Quarantine** is controlled isolation of a blocked artifact. Quarantine is not automatically equivalent to archive.

## 5. Current and proposed lifecycle states

Current supported observational states:

- `ABSENT`;
- `ACTIVE_INTERNAL_TEST_ARTIFACT`; and
- `BLOCKED_ARTIFACT`.

Design-only proposed states:

- `ARCHIVE_ELIGIBLE`;
- `ARCHIVE_PLANNED`;
- `ARCHIVED_INTERNAL_TEST_ARTIFACT`;
- `REMOVAL_ELIGIBLE`;
- `REMOVAL_PLANNED`;
- `REMOVED_INTERNAL_TEST_ARTIFACT`; and
- `LIFECYCLE_ACTION_BLOCKED`.

The proposed states are not implemented. No transition is persisted. No state can be inferred solely from UI text. Archive and removal must never occur from `ABSENT` or `BLOCKED_ARTIFACT` without a separately approved policy and evidence contract.

## 6. Allowed state transitions

These are design-only transitions; no automatic transition is defined.

Archive path:

`ACTIVE_INTERNAL_TEST_ARTIFACT -> ARCHIVE_ELIGIBLE -> ARCHIVE_PLANNED -> ARCHIVED_INTERNAL_TEST_ARTIFACT`

Removal path:

`ACTIVE_INTERNAL_TEST_ARTIFACT -> REMOVAL_ELIGIBLE -> REMOVAL_PLANNED -> REMOVED_INTERNAL_TEST_ARTIFACT`

Every transition must fail closed when identity, metadata, authorization, destination, audit, or idempotency evidence is invalid. Inspection success alone does not create eligibility. A blocked result cannot be promoted by a caller, dashboard selection, or file existence.

## 7. Archive eligibility

Archive planning could succeed only when every condition below is true:

- local fixture mode is enabled;
- the source is an accepted governed fixture;
- fixture ID matches;
- `fixture_only`, `internal_only`, and `test_fixture_only` are true;
- read-only inspection completed successfully;
- current state is `ACTIVE_INTERNAL_TEST_ARTIFACT`;
- deterministic source filename matches;
- source is contained inside the approved internal root;
- source is a regular file;
- no link or reparse point exists in the relevant path;
- the PDF signature is valid;
- PDF parsing succeeds;
- page count is valid;
- artifact identity matches;
- classification matches;
- required internal warnings are present;
- no forbidden release claim is present;
- supplied SHA-256 matches;
- supplied size matches;
- supplied page count matches;
- an archive root is configured and approved;
- explicit operator approval is present;
- a reason code is supplied;
- a request ID is supplied;
- an idempotency key is supplied; and
- an approved audit sink is available.

## 8. Removal eligibility

Removal requires every archive-grade identity and evidence check plus stronger gates:

- a removal policy is explicitly selected;
- removal semantics are resolved;
- irreversible-action acknowledgement is present where applicable;
- actor authorization is adequate;
- the retention obligation is satisfied;
- archive-before-removal is satisfied where policy requires it;
- evidence preservation is complete;
- an audit sink is available;
- rollback or restoration policy has been evaluated;
- no legal, governance, or operational hold exists; and
- no customer-ready or release claim exists.

Removal must not be enabled merely because an artifact exists. Permanent deletion remains blocked by this contract.

## 9. Request envelope

A future design-only request envelope contains bounded fields equivalent to:

- `fixture_id`;
- `report_id`;
- `report_version`;
- `requested_action`;
- `expected_artifact_state`;
- `expected_filename`;
- `expected_sha256`;
- `expected_file_size_bytes`;
- `expected_page_count`;
- `operator_id`;
- `operator_role`;
- `approval_id`;
- `reason_code`;
- `reason_text`;
- `request_id`;
- `idempotency_key`;
- `requested_at`; and
- `explicit_action_acknowledgement`.

Archive additionally requires `archive_policy_id` and `expected_archive_root_id`. Removal additionally requires `removal_policy_id`, `removal_semantics`, and `archive_evidence_id` where policy requires it.

The caller may not supply absolute source or destination paths.

## 10. Prohibited request fields

The following are prohibited: `source_path`, `output_path`, `archive_path`, `destination_path`, customer directory, wildcard, glob, recursive flag, arbitrary filename, arbitrary extension, `overwrite=true`, `force=true`, skip validation, skip audit, skip archive, customer-ready authority, customer-release authority, arbitrary report content, and arbitrary PDF bytes.

## 11. Operator authorization contract

A future action requires an authenticated local operator identity, bounded operator role, action-specific permission, approval ID, explicit acknowledgement, reason code, request timestamp, request ID, and idempotency key. Archive and removal are separate permissions. Removal requires stronger authority than archive.

No implicit authorization may be inferred from fixture mode, dashboard selection, generation acknowledgement, inspection success, or file existence. A design document, prior commit, proof, or test pass cannot approve an action.

## 12. Reason-code contract

Bounded archive reasons may be:

- `retention`;
- `proof_preservation`;
- `superseded_internal_draft`;
- `lifecycle_closure`; or
- `controlled_evidence_transfer`.

Bounded removal reasons may be:

- `approved_retention_expiry`;
- `duplicate_after_verified_archive`;
- `approved_test_fixture_cleanup`; or
- `governance_directed_deactivation`.

Vague reasons such as `cleanup`, `old`, `unwanted`, and `fix it` are prohibited. Optional reason text must remain bounded and must not contain credentials, secrets, paths, or personal data.

## 13. Source-target derivation

The source target must be derived only as:

`validated governed row -> deterministic lifecycle planning function -> approved internal output root -> deterministic filename`

Caller-controlled source, directory scans, newest-file selection, similarly named fallback, wildcard lookup, and recursive discovery are prohibited.

## 14. Archive destination contract

A future archive destination must be configured server-side, absolute, separately identified from the active internal output root, outside customer and canonical output roots, path-contained, deterministic, fixture/report/version-bound, link/reparse safe, non-caller-controlled, non-overwriting, and auditable.

A potential structure, without committing implementation, is:

`approved archive root / fixture ID / report ID / report version / original deterministic filename`

Fixture IDs, report IDs, versions, and filenames require strict identity validation, separator rejection, traversal rejection, bounded length, and safe normalization. A destination must be derived by the server and never echoed as an unrestricted path in a response.

## 15. Archive collision contract

Fail closed when the destination already exists, is a link or reparse point, is outside the archive root, resolves to the source, has an invalid parent, has mismatched archived identity, or conflicts with idempotency evidence.

The action must not overwrite, append a random suffix, silently version, delete a previous archive, or select another destination automatically.

An idempotent success is permitted only when the existing archive has exactly matching fixture/report identity, filename, SHA-256, size, page count, and originating request or accepted idempotency record. Any discrepancy is a conflict, not success.

## 16. Archive source-retention behavior

Two distinct designs are possible: copy-and-retain-active, or move-and-deactivate-active. The safer initial design is copy bytes into the governed archive boundary, independently verify copied bytes and metadata, and retain the active source. Archive must not remove or delete the source in the same action. Source removal is a separate independently authorised operation.

## 17. Removal-semantics contract

Possible semantics are metadata-only deactivation, controlled quarantine, movement to a retention archive, permanent filesystem deletion, and secure deletion. Permanent deletion is blocked for the initial design. Initial removal should mean controlled deactivation or quarantine only after evidence preservation, with exact semantics requiring a separate policy decision. Quarantine is not archive unless its policy explicitly provides equivalent retention and evidence guarantees.

## 18. Evidence-preservation contract

Before mutation, a before-state evidence record must contain fixture ID, report ID, report version, classification, filename, SHA-256, size, page count, signature validation, identity validation, warning validation, provenance, current lifecycle state, requested action, operator identity, approval ID, reason, request ID, idempotency key, and timestamp.

After mutation, evidence must contain action result, resulting lifecycle state, source existence state, destination existence state where applicable, resulting filename, resulting SHA-256, resulting size, resulting page count, destination classification, audit event ID, and blocked reason where applicable.

## 19. Audit-event contract

A design-only audit event contains:

- `event_id`;
- `event_type`;
- `request_id`;
- `idempotency_key`;
- `fixture_id`;
- `report_id`;
- `report_version`;
- `operator_id`;
- `operator_role`;
- `approval_id`;
- `reason_code`;
- `requested_action`;
- `previous_state`;
- `resulting_state`;
- expected metadata;
- observed metadata;
- source boundary ID;
- destination boundary ID where applicable;
- `timestamp_started`;
- `timestamp_completed`;
- result;
- blocked reason; and
- safety flags.

No approved lifecycle audit sink is currently implemented.

## 20. Audit persistence boundary

A separate approved lifecycle audit sink is required. The customer queue, report-generation ledger, accuracy ledger, GCID, learning store, calibration store, and application logs alone must not be reused implicitly. If the approved audit sink is unavailable, mutation must fail closed.

## 21. Idempotency contract

Each action requires a unique idempotency key bound to request identity, requested action, artifact metadata, and deterministic prior-result lookup. Conflicting replay is rejected. An exact replay with the same evidence may return the previous bounded result. The same key with a different action, identity, hash, size, or page count is blocked. Repeated archive must not create multiple copies, and repeated removal must not produce ambiguous success.

## 22. Concurrency contract

Only one active lifecycle action may exist per deterministic artifact. The design must detect conflicts, prevent archive/removal overlap, prevent generation during active lifecycle mutation, and require refreshed inspection after mutation. A stale inspection result cannot be treated as current. Immediate metadata revalidation is required to narrow any time-of-check/time-of-use gap; this document does not prescribe a lock mechanism.

## 23. Hash and metadata revalidation

Immediately before mutation, revalidate source existence, regular-file status, link/reparse rejection, path containment, filename, SHA-256, size, page count, identity, classification, warnings, and forbidden release claims. Any difference from the approved request fails closed.

## 24. Archive execution design boundary

Future archive execution would have these design-only stages:

1. Validate request.
2. Validate operator authorization.
3. Inspect the current artifact.
4. Compare expected metadata.
5. Validate the archive destination.
6. Create before-state audit intent.
7. Copy to a temporary destination inside the approved archive root.
8. Verify copied bytes and metadata.
9. Atomically finalize without overwrite.
10. Persist the audit result.
11. Return a bounded response.

These stages are not implemented or authorised.

## 25. Removal execution design boundary

Future removal execution would have these design-only stages:

1. Validate request.
2. Validate stronger authorization.
3. Inspect the current artifact.
4. Compare expected metadata.
5. Verify evidence preservation.
6. Verify archive prerequisite where required.
7. Create before-state audit intent.
8. Perform approved removal semantics.
9. Verify resulting state.
10. Persist the audit result.
11. Return a bounded response.

Permanent deletion remains blocked unless separately authorised.

## 26. Response contract

A bounded future response contains fields equivalent to:

- `ok`;
- `status`;
- `action`;
- `previous_state`;
- `resulting_state`;
- `fixture_id`;
- `report_id`;
- `report_version`;
- `filename`;
- expected and observed SHA-256;
- expected and observed file size;
- expected and observed page count;
- `request_id`;
- `idempotency_key`;
- `audit_event_id`;
- `blocked_reason`;
- `action_performed`;
- `source_exists_after`;
- `destination_exists_after` where applicable; and
- safety flags.

Responses must not return unrestricted absolute paths.

## 27. HTTP behavior design

If a future route is separately authorised, deterministic classifications should be:

- `200`: prior identical idempotent result;
- `201` or `200`: newly completed archive, according to route convention;
- `400`: invalid request contract;
- `403`: authorization or fixture governance blocked;
- `409`: identity, state, collision, concurrency, or idempotency conflict;
- `422`: artifact metadata, destination, evidence, or policy validation failure;
- `503`: required audit sink unavailable; and
- `500`: unexpected internal fault only.

No route is implemented by this contract.

## 28. Deterministic blocked reasons

The bounded reasons are:

`invalid_request_contract`, `unexpected_request_fields`, `fixture_mode_disabled`, `invalid_fixture_source`, `artifact_identity_mismatch`, `lifecycle_state_mismatch`, `source_target_absent`, `source_target_blocked`, `source_target_not_regular`, `source_link_or_reparse_rejected`, `source_outside_approved_root`, `filename_mismatch`, `sha256_mismatch`, `file_size_mismatch`, `page_count_mismatch`, `classification_mismatch`, `internal_warning_missing`, `forbidden_release_claim_present`, `operator_not_authorized`, `approval_missing`, `acknowledgement_missing`, `reason_missing`, `archive_root_missing`, `archive_destination_invalid`, `archive_destination_collision`, `source_destination_same`, `audit_sink_unavailable`, `evidence_preservation_incomplete`, `archive_prerequisite_missing`, `removal_policy_unresolved`, `retention_hold_active`, `concurrency_conflict`, `idempotency_conflict`, and `permanent_deletion_not_authorized`.

## 29. Safety flags

Every future plan and response must preserve:

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
artifact_archived = true only after verified archive completion
artifact_removed = true only after verified approved removal completion
artifact_overwritten = false
permanent_mutation_performed = true only after a separately authorised verified lifecycle action
```

For planning and validation responses, all mutation flags remain false.

## 30. Threat analysis and controls

- **Path traversal or caller-controlled destination:** derive both targets server-side, validate identities, contain paths, and reject separators and traversal.
- **Symlink/reparse redirection:** reject links and reparse points for source, destination, and relevant parents.
- **Source/destination substitution or TOCTOU:** revalidate immediately before mutation and compare identity, hash, size, page count, and containment.
- **Archive overwrite or collision:** require non-overwriting atomic finalization and fail closed on any existing destination.
- **Stale inspection evidence:** require a fresh inspection and exact expected metadata before action.
- **Forged operator identity or replay:** bind authenticated actor, role, approval, request ID, timestamp, and unique idempotency key.
- **Audit bypass or audit failure after mutation:** create audit intent before action, require an approved sink, and fail closed when the sink is unavailable; partial-action recovery needs policy.
- **Archive-then-delete coupling:** keep archive and removal as separate requests and permissions.
- **Accidental customer-directory access:** prohibit customer paths and enforce approved internal boundaries.
- **Unrestricted path disclosure:** return identifiers and bounded filename/metadata only.
- **Deletion without evidence preservation:** require complete before-state evidence and archive prerequisite where policy requires it.
- **Partial copy:** copy only inside an approved temporary destination, verify bytes and metadata, then finalize without overwrite.

## 31. Open decisions

Separate authorization is required for the approved archive root, copy versus move, retention duration, removal semantics, permanent deletion policy, quarantine policy, operator roles, approval workflow, audit storage, rollback/restore policy, legal or governance holds, recovery from partial mutation, and lifecycle concurrency mechanism.

## 32. Implementation-readiness blockers

No planning adapter or mutation implementation can be authorised until at minimum:

- the archive root is approved;
- the removal policy is resolved;
- the audit sink is approved;
- authorization roles are approved;
- retention policy is resolved;
- rollback/restore policy is resolved;
- a concurrency mechanism is designed;
- threat review is completed; and
- the planning-adapter contract is separately assessed.

## 33. Smallest safe next slice

Recommend exactly one docs-only next slice:

**Button 2 governed internal PDF lifecycle audit and authorization contract design**

Proposed file: `docs/button2_governed_internal_pdf_artifact_lifecycle_audit_authorization_contract_v1.md`

Implementation is not recommended yet.

## 34. Recommended sequencing

A. Archive/removal contract design.

B. Lifecycle audit and authorization contract.

C. Archive destination and collision design.

D. Removal-semantics and retention policy.

E. Docs-only threat review.

F. Planning-adapter readiness assessment.

G. Pure non-mutating lifecycle-plan adapter.

H. Focused planning tests.

I. Live non-mutating planning proof.

J. Separate mutation implementation readiness assessment.

K. Separately authorised archive implementation.

L. Removal implementation only after archive and stronger gates are proven.

## 35. Explicit non-authorization

This document does not authorise archive planning implementation, archive implementation, removal planning implementation, removal implementation, deletion, secure deletion, quarantine, rename, movement, copy, overwrite, regeneration, repair, lifecycle endpoint, lifecycle UI, lifecycle persistence, audit persistence implementation, customer-ready classification, customer release, production storage, queue writes, report-ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

It also does not authorise any filesystem mutation or grant authority to infer approval from inspection, dashboard state, fixture mode, file existence, proof, or test results.

## 36. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_ARCHIVE_REMOVAL_CONTRACT=CONTRACT_DESIGN_COMPLETE`
