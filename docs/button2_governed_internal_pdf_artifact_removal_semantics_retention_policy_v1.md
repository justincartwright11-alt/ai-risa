# Button 2 Governed Internal PDF Artifact Removal Semantics and Retention Policy v1

## 1. Executive status

`REMOVAL_RETENTION_POLICY_COMPLETE`

This policy defines future design evidence for removal semantics, retention, holds, archive prerequisites, restoration, audit, and fail-closed lifecycle decisions for a fictional governed internal/test PDF. Policy completion does not authorise implementation, planning, persistence, mutation, removal, deletion, quarantine, deactivation, restoration, archive, or release.

## 2. Locked baseline

- Archive destination contract commit: `8302cb7afd78a56c1c78096fe36f909fd0dd1e7b`.
- Lifecycle audit/authorization contract commit: `cbadefb9cf73236aa0786917f2c8ebb236be292a`.
- Archive/removal contract baseline: `bca19b763ef9af78c876f74db8157efd49404f5c`.
- The fixture is fictional and governed for internal/test use only.
- The artifact is an internal/test-only artifact, not customer-ready and not for customer release.
- The current inspection chain is read-only; no removal implementation currently exists.
- Permanent deletion remains blocked.

## 3. Policy purpose

This design-only policy identifies evidence required to determine what removal means, when an artifact is eligible, what must be retained first, whether archive is mandatory, whether a hold blocks action, whether restoration is possible, which actor and approval are required, what evidence proves an action, which outcome is permitted, and which removal forms remain prohibited. It does not implement or authorise removal.

## 4. Removal terminology

These terms are separate and are not interchangeable:

- **Active-source deactivation:** the governed active artifact is no longer treated as active while its bytes remain retained and recoverable.
- **Metadata-only deactivation:** a state or metadata projection marks the artifact inactive without changing its bytes or location. No persistence mechanism currently exists.
- **Controlled quarantine:** a separately approved, contained boundary isolates retained bytes from active use.
- **Move to retention boundary:** a governed transfer into a specified retention location. It is not deletion and requires its own destination and evidence contract.
- **Archive followed by active-source removal:** two separately requested actions; verified archive must complete before a separately authorised source action.
- **Filesystem deletion:** unlinking or removing a filesystem object. It is not automatically secure deletion and is not authorised here.
- **Secure deletion:** a separately validated claim that recovery is prevented across the relevant storage layers. Ordinary deletion does not prove it.
- **Logical tombstone:** a governed record that marks an identity unavailable without asserting that bytes were destroyed.
- **Inaccessible-but-retained artifact:** bytes remain preserved but are unavailable through the active path or normal active workflow.

## 5. Recommended initial removal semantics

The conservative initial position is:

- removal must not mean permanent deletion;
- removal should mean controlled deactivation or governed quarantine;
- bytes and evidence must remain recoverable;
- active-source unavailability must be explicit;
- archive or equivalent evidence preservation must occur first where policy requires it;
- removal must remain separate from archive;
- no customer classification, release authority, queue write, ledger write, learning, calibration, or production storage may result.

No default semantic is executable. The exact permitted semantic requires separate approval and capability review.

## 6. Permanently prohibited or blocked semantics

The following remain blocked until a separate authority and capability review, and are outside the initial roadmap: permanent filesystem deletion, secure deletion, silent unlink, recursive cleanup, wildcard deletion, delete-on-archive, overwrite with empty content, truncation, random movement, deletion without evidence preservation, deletion without durable audit, removal from customer or canonical output roots, and removal based only on age without identity validation. No cleanup operation may disguise one of these actions.

## 7. Proposed removal state model

Design-only states are:

- `ACTIVE_INTERNAL_TEST_ARTIFACT`;
- `REMOVAL_REVIEW_REQUIRED`;
- `RETENTION_HOLD_ACTIVE`;
- `REMOVAL_ELIGIBLE`;
- `REMOVAL_PLANNED`;
- `QUARANTINED_INTERNAL_TEST_ARTIFACT`;
- `DEACTIVATED_INTERNAL_TEST_ARTIFACT`;
- `REMOVED_INTERNAL_TEST_ARTIFACT`;
- `REMOVAL_BLOCKED`;
- `RESTORATION_ELIGIBLE`; and
- `RESTORED_INTERNAL_TEST_ARTIFACT`.

These states are not implemented, none is persisted, and no transition may occur automatically. `REMOVED_INTERNAL_TEST_ARTIFACT` must not imply destroyed bytes unless a future approved policy explicitly says so.

## 8. Allowed design-only transitions

The conservative removal path is:

`ACTIVE_INTERNAL_TEST_ARTIFACT -> REMOVAL_REVIEW_REQUIRED -> REMOVAL_ELIGIBLE -> REMOVAL_PLANNED -> QUARANTINED_INTERNAL_TEST_ARTIFACT`

or:

`ACTIVE_INTERNAL_TEST_ARTIFACT -> REMOVAL_REVIEW_REQUIRED -> REMOVAL_ELIGIBLE -> REMOVAL_PLANNED -> DEACTIVATED_INTERNAL_TEST_ARTIFACT`

A restoration path is:

`QUARANTINED_INTERNAL_TEST_ARTIFACT` or `DEACTIVATED_INTERNAL_TEST_ARTIFACT` `-> RESTORATION_ELIGIBLE -> RESTORED_INTERNAL_TEST_ARTIFACT`.

Every transition must be explicit, approved, audited, identity-bound, and fail closed. No transition is selected or executed by this document.

## 9. Retention-policy classes

Design-only classes are:

- `proof_evidence_retention`;
- `superseded_internal_draft_retention`;
- `temporary_fixture_retention`;
- `blocked_artifact_retention`;
- `quarantine_retention`;
- `audit_evidence_retention`; and
- `legal_or_governance_hold`.

No final duration is assigned because the inspected repository evidence does not establish one. Missing duration is a blocker, not permission to use a default.

## 10. Retention duration contract

Every future policy must define `policy_id`, `policy_version`, `policy_class`, `retention_start_event`, minimum retention duration, maximum-retention behavior where applicable, hold override behavior, archive prerequisite, permitted removal semantics, restoration window, evidence-retention duration, approval authority, and review frequency. Values must be explicit; missing or conflicting values fail closed.

## 11. Retention start events

The bounded candidates are artifact generation completion, official proof closure, supersession by a later internal version, archive completion, lifecycle closure approval, quarantine start, and manual governed declaration. The selected event must be explicit, timestamped, identity-bound, and auditable. Retention must not be calculated from arbitrary filesystem creation or modification time alone.

## 12. Retention-expiry calculation

A future calculation must use the approved policy and version, selected start-event ID, recorded timestamp, timezone convention, hold state, archive state, artifact identity, and policy version. Missing, stale, manipulated, or inconsistent evidence produces no expiry decision and blocks eligibility.

## 13. Retention holds

The following hold types must block removal regardless of ordinary expiry: `governance_hold`, `investigation_hold`, `proof_preservation_hold`, `audit_hold`, `incident_hold`, `legal_hold`, and `operator_review_hold`.

A hold contract requires `hold_id`, `hold_type`, fixture/report identity, artifact metadata binding, `placed_by`, authority, `reason_code`, `placed_at`, `review_at`, `expires_at` where applicable, status, release authority, `released_by`, `released_at`, and audit-event linkage. Browser-local or free-form-only holds are insufficient. Hold status unavailable is fail closed.

## 14. Archive-before-removal requirement

A verified copy-and-retain archive must exist before active-source deactivation or quarantine whenever the approved policy requires it. Archive identity, SHA-256, size, page count, classification, and warnings must match; archive completion audit must exist; and source removal must be a separate request, authorization, acknowledgement, and audit event. Archive may not implicitly remove its source.

Required archive evidence includes archive-root ID/version, archive policy ID, archive event ID, deterministic archived filename, archived SHA-256, archived size, archived page count, completion timestamp, source-retained result, audit-event ID, and idempotency evidence. Exceptions require a separately approved exception policy, stronger approval, explicit reason, proof of preservation elsewhere, durable audit, no customer/production artifact, and no active hold. There is no default exception, and no exception is approved here.

## 15. Removal eligibility contract

Future eligibility requires all of the following: fixture mode enabled; accepted governed fixture; exact fixture/report/version identity; `internal_only=true`; `test_fixture_only=true`; current state eligible; deterministic filename matched; source inside approved root; regular-file status; no link or reparse point; valid PDF signature; parse success; valid page count; classification and warnings matched; expected SHA-256, size, and page count matched; retention policy satisfied; no active hold; archive prerequisite satisfied where required; evidence preservation complete; selected removal policy; explicit approval; stronger operator permission; acknowledgement; reason code; request ID; idempotency key; audit sink available; and restoration or rollback policy evaluated.

## 16. Removal-policy request fields

A bounded future request contains: `fixture_id`, `report_id`, `report_version`, `requested_action`, `removal_policy_id`, `removal_semantics`, `expected_artifact_state`, `expected_filename`, `expected_sha256`, `expected_file_size_bytes`, `expected_page_count`, `retention_policy_id`, `retention_start_event_id`, `retention_expiry`, `archive_evidence_id`, `hold_check_result`, `restoration_policy_id`, `operator_id`, `approval_id`, `reason_code`, `request_id`, `idempotency_key`, and `explicit_removal_acknowledgement`.

The caller must not provide source or destination paths, wildcards, recursive flags, overwrite flags, or force flags. Server-side derivation and validation are mandatory.

## 17. Controlled deactivation semantics

Metadata-only or state-bound deactivation is design-only. A future implementation would require the active generation path to stop treating the artifact as active, unchanged and recoverable bytes, a deterministic governed location, an auditable deactivation state, and a defined restoration path. It must not create customer classification or release authority. No persistence mechanism currently exists.

## 18. Quarantine semantics and boundary

Controlled quarantine means transfer into a separately approved quarantine boundary; bytes remain retained, the artifact is no longer active, classification remains internal/test-only, warnings are preserved, overwrite is prohibited, deletion is not automatic, and restoration needs separate approval. No quarantine root or implementation currently exists.

A future quarantine root must be server-controlled, separately identified, outside active and customer roots, deterministic, contained, non-caller-controlled, link/reparse safe, collision safe, and audit bound. The archive root must not be reused implicitly without an approved policy.

## 19. Active-source removal after archive

Archive completion must be verified first, archive evidence must be immutable and auditable, a new removal request must be created, new authorization and acknowledgement must be obtained, current source metadata and hold status must be revalidated, the independent action must run, and completion must be audited. No archive request may remove, rename, overwrite, or deactivate the source.

## 20. Restoration contract and window

Future restoration design must define eligibility, source, destination, metadata validation, collision rules, actor and approval, reason code, audit evidence, resulting state, source preservation, and overwrite prohibition. Every deactivation or quarantine policy must define a restoration period, authorized actor, required evidence, post-window behavior, hold interaction, and audit retention after expiry. Expiry must never silently become permanent deletion. Restoration is not implemented.

## 21. Evidence preservation

Before action, retain fixture ID, report ID/version, filename, SHA-256, size, page count, signature and parse results, classification, warnings, provenance, current state, retention policy, hold result, archive evidence, requested semantics, requester, approver, reason, request ID, idempotency key, and timestamp.

After action, retain resulting state, source existence, quarantine/retained boundary ID where applicable, resulting filename, SHA-256, size, page count, restoration eligibility, action result, audit-event ID, and blocked reason where applicable.

## 22. Removal audit events

Design-only events are: `removal_review_started`, `removal_eligibility_evaluated`, `retention_expiry_evaluated`, `retention_hold_detected`, `archive_prerequisite_validated`, `removal_authorization_evaluated`, `removal_plan_created`, `removal_execution_started`, `removal_execution_completed`, `removal_execution_blocked`, `artifact_quarantined`, `artifact_deactivated`, `restoration_requested`, `restoration_completed`, and `partial_removal_incident_detected`.

Events must be durable, append-only, immutable, identity-bound, and linked to request, approval, expected/observed metadata, prior/resulting state, boundary IDs, result, blocked reason, and safety flags. No approved lifecycle audit sink currently exists.

## 23. Idempotency and concurrency

Removal idempotency binds requested action, semantics, fixture/report/version, current state, expected metadata, retention policy, hold result, archive evidence, approval ID, and restoration policy. Exact replay may return the prior bounded result. Any difference is an `idempotency_conflict` and must block.

Only one active lifecycle mutation may exist per deterministic artifact. Archive and removal, generation and removal, and restoration and removal may not overlap. Metadata and hold status must be revalidated immediately; stale inspection is not current authority. The lock mechanism is unresolved and not selected here.

## 24. Removal execution boundary

A future design-only sequence is: validate request; authenticate and authorize actor; validate approval and acknowledgement; inspect current artifact; compare expected metadata; evaluate retention; evaluate holds; verify archive prerequisite; verify evidence preservation; persist durable audit intent; perform only approved deactivation or quarantine; verify resulting state and retained bytes; persist completion audit; return a bounded response. Permanent deletion is excluded.

## 25. Failed-removal handling

Failure categories include no action performed, partial metadata transition, partial quarantine transfer, source unavailable after failed transfer, audit intent persisted but action incomplete, and action completed while completion audit failed. Every category requires a fail-closed response, no automatic retry, no automatic deletion, incident classification, manual governed review, and separately designed recovery.

A partial-removal incident is never completed removal. Evidence must capture before state, observed source state, retained/quarantine state, hashes and sizes where available, audit intent, error stage, and recovery status.

## 26. Permanent deletion and secure-deletion findings

Permanent deletion is not authorised. Before consideration, a separate contract would require legal/governance authority, evidence retention, archive prerequisite, secure-deletion capability, filesystem/storage guarantees, verification standard, multi-party approval, recovery-impossibility acknowledgement, audit durability, and incident handling. It is not the next implementation.

Ordinary deletion cannot prove secure erasure because of filesystem journaling, snapshots, SSD wear levelling, backups, cloud synchronization, caches, replication, and operating-system behavior. No secure-deletion claim may be made without validated platform capability.

## 27. Retention-policy response contract

A future bounded response contains `ok`, `status`, fixture/report/version, `current_state`, `proposed_state`, `removal_policy_id`, `removal_semantics`, `retention_policy_id`, `retention_start_event`, `retention_expires_at`, `retention_satisfied`, `hold_active`, permitted `hold_id`, `archive_required`, `archive_prerequisite_satisfied`, `restoration_supported`, `removal_eligible`, `planning_authorized`, `execution_authorized=false`, `action_performed=false`, `request_id`, `idempotency_key`, `approval_id`, `blocked_reason`, and safety flags. It must disclose no unrestricted paths or secrets.

## 28. HTTP behavior and blocked reasons

No endpoint is implemented. A separately authorised future endpoint may use `200` for non-mutating evaluation or exact replay, `400` for malformed contract, `403` for authorization/policy/fixture/hold/acknowledgement blocks, `409` for state/concurrency/hold/replay/archive conflicts, `422` for metadata/retention/semantics/restoration/evidence failures, `503` for audit/archive-evidence/quarantine-boundary/policy unavailability, and `500` only for unexpected internal faults.

Bounded reasons include: `removal_policy_missing`, `removal_policy_unresolved`, `removal_semantics_not_authorized`, `permanent_deletion_not_authorized`, `secure_deletion_not_supported`, `retention_policy_missing`, `retention_start_event_missing`, `retention_not_satisfied`, `retention_calculation_invalid`, `retention_hold_active`, `hold_status_unavailable`, `archive_prerequisite_missing`, `archive_evidence_invalid`, `evidence_preservation_incomplete`, `restoration_policy_missing`, `artifact_identity_mismatch`, `lifecycle_state_mismatch`, `filename_mismatch`, `sha256_mismatch`, `file_size_mismatch`, `page_count_mismatch`, `source_target_blocked`, `source_link_or_reparse_rejected`, `operator_not_authorized`, `approval_missing`, `acknowledgement_missing`, `reason_missing`, `idempotency_conflict`, `concurrency_conflict`, `audit_sink_unavailable`, `quarantine_boundary_missing`, `partial_removal_detected`, and `action_not_authorized`.

## 29. Safety flags

Every future planning or policy response must preserve:

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

## 30. Threat controls

- Semantics ambiguity: require an enumerated policy and explicit acknowledgement.
- Archive coupled to removal: separate requests, permissions, evidence, and audit events.
- Cleanup disguised as deletion: reject wildcard, recursive, force, truncation, and delete-on-archive inputs.
- Timestamp manipulation: use an approved auditable start event, never filesystem mtime alone.
- Hold bypass: evaluate server-bound holds immediately before action and fail closed when unavailable.
- Forged or stale archive evidence: bind archive identity, hash, metadata, event, policy, root, and idempotency evidence.
- Omitted restoration: require restoration policy and window before eligibility.
- Quarantine substitution: require a server-controlled, separately identified boundary.
- Path traversal, links, reparse points, ADS, Unicode, and platform ambiguity: server derivation, component validation, containment, and rejection on ambiguity.
- Replayed approval or idempotency conflict: bind approval and exact canonical request; accept only exact replay.
- Concurrency and generation overlap: one active lifecycle action and immediate revalidation.
- Partial transfer or audit failure: incident state, no completion classification, no automatic retry/deletion.
- Customer-root access: reject customer/canonical roots and preserve all release flags false.
- Permanent-deletion or secure-erasure overclaim: prohibit both without separate capability and authority evidence.

## 31. Open decisions

Unresolved decisions are approved removal semantics; retention policy owner; retention durations; retention start events; legal/governance hold authority; archive-before-removal exceptions; quarantine root; metadata-only deactivation persistence; restoration windows and approval; evidence-retention duration; permanent-deletion policy; secure-deletion capability; failed-removal recovery; concurrency mechanism; audit sink implementation; and policy-service location.

## 32. Implementation-readiness blockers

Implementation remains blocked until removal semantics, retention policy/durations/start events, hold contract and authority, archive prerequisite policy, quarantine or deactivation boundary, restoration policy, failed-removal recovery, audit sink, roles and permissions, lifecycle threat review, and a separately assessed removal planning-adapter readiness are approved. No missing value may be silently defaulted.

## 33. Smallest safe next slice

Recommend exactly one docs-only next slice: **Button 2 governed internal PDF lifecycle threat review**.

Proposed file: `docs/button2_governed_internal_pdf_artifact_lifecycle_threat_review_v1.md`.

## 34. Recommended sequencing

A. Removal semantics and retention policy.
B. Lifecycle threat review.
C. Archive planning-adapter readiness assessment.
D. Pure non-mutating archive planning adapter.
E. Focused archive-plan tests.
F. Live non-mutating archive-plan proof.
G. Archive implementation-readiness assessment.
H. Separately authorised copy-and-retain archive implementation.
I. Removal planning only after archive, policy, audit, restoration, and stronger authorization controls are proven.
J. Permanent deletion remains outside the initial roadmap.

## 35. Explicit non-authorization

This document does not authorise removal planning or implementation, quarantine, metadata deactivation, restoration, deletion, secure deletion, copy, movement, rename, overwrite, archive implementation, retention persistence, hold persistence, lifecycle endpoint, lifecycle UI, audit persistence implementation, customer-ready classification, customer release, production storage, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 36. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_REMOVAL_RETENTION=REMOVAL_RETENTION_POLICY_COMPLETE`
