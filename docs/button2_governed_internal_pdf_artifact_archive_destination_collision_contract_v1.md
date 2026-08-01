# Button 2 Governed Internal PDF Artifact Archive Destination and Collision Contract v1

## 1. Executive status

`ARCHIVE_DESTINATION_CONTRACT_COMPLETE`

This design-only contract defines evidence and fail-closed requirements for a possible future governed archive copy of a fictional internal/test PDF. Contract completion does not authorise implementation, planning, copying, finalization, directory creation, persistence, removal, deletion, overwrite, or release.

## 2. Locked baseline

- Lifecycle audit/authorization contract commit: `cbadefb9cf73236aa0786917f2c8ebb236be292a`.
- Archive/removal contract commit: `bca19b763ef9af78c876f74db8157efd49404f5c`.
- The fixture is fictional and governed only for internal/test use.
- The artifact is internal/test-only and not customer-ready or approved for customer release.
- The conservative archive design is copy, independently verify, and retain the active source.
- Archive and removal remain unimplemented and separately unauthorized.

## 3. Contract purpose

This contract defines the evidence required to prove which server-controlled archive boundary is approved, how a deterministic destination is derived, that source and destination are distinct and contained, that path components are safe, that overwrite cannot occur, that an identical existing archive is handled idempotently, that conflicting content is blocked, that partial copies cannot appear complete, that bytes and metadata are independently verified, and that audit evidence binds source, destination, request, approval, and result.

All classifications and transitions below are design-only. They do not create an archive plan, perform a copy, or authorize any filesystem mutation.

## 4. Archive-root identity contract

A future server-side archive boundary must expose only bounded identity fields equivalent to:

- `archive_root_id`;
- `archive_root_version`;
- `archive_root_classification`;
- `archive_root_enabled`;
- `archive_root_configured`;
- `archive_root_absolute`;
- `archive_root_server_controlled`;
- `archive_root_customer_isolated`;
- `archive_root_source_isolated`;
- `archive_root_link_safe`; and
- `archive_root_policy_id`.

`archive_root_absolute` is an internal validation attribute, not a caller or dashboard response field. Responses must return the root ID and version, never an unrestricted absolute archive path.

## 5. Archive-root configuration boundary

A future root must be configured server-side, absolute, separately identified from the active internal output root, outside all customer and canonical output roots, outside queue and ledger storage, and controlled by the server. It must not be derived from request JSON, overridden by the browser, or silently defaulted. It must be validated before any planning or execution evaluation. Missing, disabled, non-absolute, ambiguous, customer-conflicting, source-conflicting, or otherwise invalid configuration fails closed.

## 6. Source-root separation

The server must prove that the source root and archive root are different paths, that the archive root is not inside the active source artifact directory where recursion or ambiguity could result, and that the source root is not inside the archive root. Resolved source and destination targets must not be identical or alias through a link, reparse point, mount, or redirection. Archive planning must never target the active deterministic file itself.

## 7. Deterministic destination structure

The design-only destination is:

```text
approved archive root/
  sanitized fixture ID/
    sanitized report ID/
      sanitized report version/
        deterministic original filename
```

The destination remains bound to the fixture ID, report ID, report version, original deterministic filename, archive policy, and archive-root identity. Date-only, newest-file, random, caller-selected, timestamp-suffixed, counter-suffixed, and alternate-directory destinations are prohibited.

## 8. Path-component sanitization

Fixture ID, report ID, report version, and filename require bounded validation before destination derivation. The future policy must reject or deterministically normalize empty components, `.` and `..`, separators, drive prefixes, UNC prefixes, NUL and control characters, reserved Windows device names, trailing spaces, trailing periods, unsupported Unicode normalization forms, excessive component lengths, and characters prohibited by the target filesystem. Colon syntax and equivalent alternate-data-stream addressing are prohibited.

Normalization must preserve unambiguous identity. It must not silently collapse two distinct identities into one destination. Rejection is preferred where normalization could lose identity, meaning, or auditability. Exact normalization form, allowed alphabet, and length limits remain open policy decisions.

## 9. Collision-resistant identity mapping

If two distinct source identities normalize to the same archive destination, the result is a deterministic `identity_normalization_collision`. The system must fail closed, select no alternate path, append no random suffix, and require a separately approved identity-mapping policy. A collision must remain visible in bounded audit evidence.

## 10. Destination-parent contract

Planning may describe missing approved parents but performs no creation. A future separately authorized execution may create only deterministic missing parents inside the approved archive root, after immediate containment and link/reparse checks for every parent. No broad recursive creation outside the deterministic chain is permitted. No directory creation is currently authorized.

Every existing parent must be inside the approved root, be a directory, not be a symlink, junction, reparse point, prohibited mount or redirection boundary, and satisfy future server ownership and write-authority policy. A parent that is unreadable, unclassifiable, or controlled by an unapproved authority fails closed.

## 11. Source target contract

The source target must be derived only through:

```text
validated governed row
-> approved internal source root
-> deterministic original filename
-> read-only inspection
-> exact metadata verification
```

Request-supplied paths, directory scans, newest-file selection, wildcards, recursive lookup, and similarly named fallbacks are prohibited.

## 12. Destination target contract

The destination must be derived only through:

```text
validated archive-root identity
-> archive policy
-> sanitized fixture/report/version components
-> deterministic original filename
```

Request-supplied archive paths, directories, filenames, random suffixes, timestamps, counters, and automatic alternate destinations are prohibited.

## 13. Source/destination equality checks

A future evaluator must compare lexical-normalized paths, absolute paths, resolved paths where safe, platform-appropriate case semantics, and filesystem identity where available. It must block identical paths, paths resolving to the same file, link/reparse aliases, unsafe-normalization equivalents, and case collisions on case-insensitive filesystems. Ambiguous resolution fails closed.

## 14. Archive-plan evidence

A future non-mutating plan may contain bounded equivalents of:

- `source_boundary_id`;
- `archive_boundary_id`;
- deterministic source filename;
- deterministic destination relative path or `destination_relative_id`;
- destination-parent status;
- `source_destination_distinct`;
- destination existence;
- collision status;
- expected SHA-256;
- expected size;
- expected page count;
- expected artifact state;
- archive policy ID;
- request ID;
- idempotency key;
- approval ID;
- `action_performed=false`; and
- all mutation flags false.

Absolute source, archive-root, destination, and unrelated directory paths must not be exposed.

## 15. Destination collision taxonomy

Design-only classifications are:

- `DESTINATION_ABSENT`;
- `IDENTICAL_ARCHIVE_PRESENT`;
- `CONFLICTING_ARCHIVE_PRESENT`;
- `DESTINATION_NON_REGULAR`;
- `DESTINATION_LINK_OR_REPARSE`;
- `DESTINATION_DIRECTORY_COLLISION`;
- `DESTINATION_OUTSIDE_APPROVED_ROOT`;
- `SOURCE_DESTINATION_SAME`;
- `IDENTITY_NORMALIZATION_COLLISION`; and
- `IDEMPOTENCY_CONFLICT`.

When the destination is absent and all checks pass, archive may be eligible for a future plan. Planning creates no file or directory and remains non-mutating. Execution remains separately blocked pending authorization, audit readiness, and implementation approval.

## 16. Identical archive present

An existing archive is identical only when fixture ID, report ID, report version, deterministic filename, SHA-256, size, page count, PDF signature, classification, internal warnings, originating request or accepted idempotency evidence, archive policy, and root identity all match. An exact replay may return a prior bounded idempotent result. No second copy, overwrite, or alternate destination is permitted.

## 17. Conflicting archive present

Any identity, hash, size, page-count, classification, warning, policy, request, or idempotency difference is `archive_destination_collision`. The future action must fail closed, return no unrestricted paths, overwrite nothing, delete or rename neither artifact, append no suffix, move no source, and require manual governed review.

A destination that is a directory, device, socket, pipe, symlink, reparse point, unsupported special file, unreadable object, or unclassifiable object is blocked as non-regular or unsafe.

## 18. Temporary-copy boundary

A future execution design may use a temporary destination only inside the approved archive root and deterministic destination parent. It must be server-controlled, non-caller-controlled, uniquely bound to request ID and idempotency key, distinct from the final destination, non-overwriting, and link/reparse safe. An incomplete temporary artifact must be removed or quarantined only under a separately approved recovery policy. It must never be reported as a completed archive.

A bounded temporary name may follow a pattern equivalent to `<deterministic-filename>.<request-or-idempotency-binding>.partial`, using an approved character set, no separators, bounded length, no final-name collision, and no reuse across conflicting requests. The naming policy is design-only and not implementation authority.

## 19. Copy execution boundary

A future design-only execution sequence is:

1. Revalidate authorization and audit-sink availability.
2. Re-inspect the source and compare approved metadata.
3. Revalidate the archive root and every destination parent.
4. Confirm destination absence or an exact idempotent prior result.
5. Persist durable audit intent.
6. Open the source without following unsafe links.
7. Create a new non-overwriting temporary file.
8. Copy bytes.
9. Flush and close under an approved durability policy.
10. Verify temporary bytes and metadata.
11. Finalize atomically to the deterministic destination without overwrite.
12. Verify final destination metadata.
13. Persist completion audit.
14. Retain the active source.

These stages are not implemented.

## 20. Finalization contract

Finalization may occur only after temporary-copy verification. It must use no-overwrite semantics, fail if the final destination appears concurrently, remain inside the approved archive root, preserve the deterministic filename, and never replace an existing destination or delete the source.

## 21. Copied-byte verification

Completion must not be recorded until independent verification passes for byte identity where practical, SHA-256, file size, PDF signature, parse success, page count, fixture/report identity, classification, internal warnings, provenance, and absence of forbidden release claims.

## 22. Metadata preservation

At minimum, retained archive evidence must preserve or intentionally regenerate under policy:

- original deterministic filename;
- source SHA-256;
- source size;
- source page count;
- fixture/report identity;
- internal classification;
- provenance;
- archive timestamp;
- archive policy;
- source boundary ID; and
- destination boundary ID.

Unsafe or unnecessary filesystem metadata must not be required without a separate policy.

## 23. Partial-copy detection and recovery

Partial-copy indicators include a temporary file without completion audit, temporary size or hash mismatch, final destination absent after execution begins, final destination present without verification, audit intent without completion, or process termination before finalization. A partial copy must never be classified as `ARCHIVED_INTERNAL_TEST_ARTIFACT`.

Recovery requires a separately approved design. Until then, automatic retry, deletion, finalization, and cleanup are blocked; the temporary artifact is neither active nor archived; an incident is recorded through the lifecycle audit system; and manual governed review is required.

## 24. Audit-boundary identifiers and linkage

Bounded identifiers must exist for `source_boundary_id`, `archive_boundary_id`, `destination_relative_id`, and `temporary_copy_id`. Audit planning and execution events must bind archive root ID/version, archive policy ID, deterministic destination relative identity, collision classification, temporary-copy ID, expected metadata, observed temporary and final metadata, `source_retained`, request and idempotency identity, approval ID, and the completed or blocked result. Unrestricted absolute paths are not required and must not be disclosed where bounded identifiers suffice.

## 25. Idempotency contract

Idempotency binds requested action, fixture/report/version, expected source state, source filename, source SHA-256, source size, source page count, archive root ID/version, archive policy ID, deterministic destination, and approval ID. Exact replay may return a prior verified result without a second copy. Any difference is `idempotency_conflict`, not a new destination.

## 26. Concurrency contract

Future controls must ensure one archive plan/execution per deterministic source and destination, prevent simultaneous archive and removal, prevent generation overwrite during archive execution, reject stale inspection evidence, and revalidate source and destination immediately before finalization. A reservation or equivalent conflict mechanism is required in future design, but no implementation lock is selected here.

## 27. Platform and path rules

The future policy must explicitly handle Windows case-insensitive comparison, path normalization, Unicode normalization, reserved names, long paths, alternate data streams, UNC paths, drive-relative paths, junctions, mount points, symlinks, and reparse points. Drive-relative and UNC ambiguity fails closed. Colon syntax or equivalent addressing that could target an alternate data stream is rejected. Source, destination, temporary targets, and every relevant parent component must be link/reparse safe and component-validated.

## 28. Filesystem disclosure boundary

Responses may return archive root ID/version, archive policy ID, deterministic relative destination identity, filename, collision classification, and bounded metadata. They must not return unrestricted absolute archive-root, source, or destination paths, customer directory details, or unrelated directory entries.

## 29. Archive-plan response contract

A future bounded response may include:

- `ok`;
- `status`;
- `requested_action`;
- `fixture_id`;
- `report_id`;
- `report_version`;
- `current_state`;
- `proposed_state`;
- `filename`;
- `expected_sha256`;
- `expected_file_size_bytes`;
- `expected_page_count`;
- `archive_root_id`;
- `archive_root_version`;
- `archive_policy_id`;
- `destination_relative_id`;
- `destination_status`;
- `collision_classification`;
- `source_destination_distinct`;
- `parents_valid`;
- `request_id`;
- `idempotency_key`;
- `approval_id`;
- `audit_sink_available`;
- `planning_authorized`;
- `execution_authorized=false`;
- `action_performed=false`;
- safety flags; and
- `blocked_reason`.

## 30. HTTP behavior design

No endpoint is implemented. If a future endpoint is separately authorized, the design recommendation is:

- `200` for successful non-mutating evaluation or exact prior idempotent result;
- `400` for malformed contract input;
- `403` for fixture, authorization, or archive-policy block;
- `409` for destination, identity, concurrency, or idempotency conflict;
- `422` for invalid path, source/destination, metadata, or policy evidence;
- `503` for archive-root or audit service unavailability; and
- `500` only for an unexpected internal fault.

## 31. Deterministic blocked reasons

Bounded future reasons include:

`archive_root_missing`, `archive_root_disabled`, `archive_root_invalid`, `archive_root_not_absolute`, `archive_root_customer_boundary_conflict`, `archive_root_source_boundary_conflict`, `invalid_path_component`, `reserved_path_component`, `path_component_too_long`, `identity_normalization_collision`, `source_target_absent`, `source_target_blocked`, `source_outside_approved_root`, `destination_outside_archive_root`, `source_destination_same`, `destination_parent_invalid`, `destination_parent_link_or_reparse`, `destination_non_regular`, `destination_link_or_reparse`, `archive_destination_collision`, `archive_identity_mismatch`, `archive_sha256_mismatch`, `archive_file_size_mismatch`, `archive_page_count_mismatch`, `archive_classification_mismatch`, `archive_warning_validation_failed`, `temporary_destination_collision`, `temporary_copy_verification_failed`, `finalization_collision`, `partial_copy_detected`, `idempotency_conflict`, `concurrency_conflict`, `audit_sink_unavailable`, and `action_not_authorized`.

## 32. Safety flags

Every planning response must preserve:

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

## 33. Threat analysis and controls

- **Archive-root substitution:** use server-controlled identity, version, classification, and policy validation; reject caller-selected roots.
- **Path injection and traversal:** reject separators, traversal, drive and UNC forms, controls, NUL, reserved names, ADS syntax, and unsafe components.
- **Unicode and case collisions:** use approved normalization and platform-aware comparisons; fail closed on identity collapse.
- **Symlink, junction, mount, and reparse redirection:** validate every relevant component immediately before use and reject unsafe boundaries.
- **Source/destination aliasing:** compare lexical, absolute, resolved, case-aware, and filesystem identity forms.
- **Overwrite and race attacks:** require absent-or-exact-idempotent destination, no-overwrite finalization, and immediate revalidation.
- **Partial or temporary-file substitution:** use a bound non-final temporary file, independently verify it, and require completion audit before archive classification.
- **Random-suffix proliferation and replay duplicates:** derive one deterministic destination and return exact prior idempotent results only.
- **Audit/path identity mismatch:** bind bounded source, destination, request, approval, policy, and observed metadata identifiers in append-only events.
- **Archive-root disclosure:** return identifiers and relative identities, not unrestricted paths.
- **Coupled source removal:** require copy-and-retain-active as the conservative initial design; removal is separate and independently authorized.
- **Customer-directory access:** isolate the root from customer and canonical outputs and reject boundary conflicts.

## 34. Open decisions

The following remain unresolved: approved archive-root location; owner and permissions; root versioning; archive policy identifiers; sanitization versus rejection; maximum path and component lengths; Unicode normalization form; destination-parent creation policy; temporary naming policy; durability and flush requirements; atomic-finalization mechanism; partial-copy retention and recovery; archive retention duration; restore policy; backup policy; capacity monitoring; concurrency mechanism; and filesystem support matrix.

## 35. Implementation-readiness blockers

Implementation remains blocked until the archive root, root identity contract, sanitization policy, parent-creation policy, temporary-copy policy, finalization semantics, partial-copy recovery, retention and restore policy, audit sink, actor roles and permissions, lifecycle threat review, and archive planning-adapter readiness assessment are separately approved and proven.

## 36. Smallest safe next slice

Recommend exactly one docs-only slice: Button 2 governed internal PDF removal semantics and retention policy design.

Proposed file:

`docs/button2_governed_internal_pdf_artifact_removal_semantics_retention_policy_v1.md`

No implementation is recommended.

## 37. Recommended sequencing

A. Archive destination and collision contract.
B. Removal semantics and retention policy.
C. Lifecycle threat review.
D. Archive planning-adapter readiness assessment.
E. Pure non-mutating archive-plan adapter.
F. Focused planning tests.
G. Live non-mutating planning proof.
H. Archive implementation-readiness assessment.
I. Separately authorized copy-and-retain archive implementation.
J. Removal implementation only after archive and stronger controls are proven.

## 38. Explicit non-authorization

This contract does not authorize archive-root creation, directory creation, archive planning implementation, archive copying, temporary-file creation, finalization, archive implementation, source removal, source deletion, source rename, source movement, overwrite, quarantine, removal, regeneration, lifecycle endpoints, lifecycle UI, audit-persistence implementation, customer-ready classification, customer release, production storage, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, model or fighter-rating changes, prediction-logic changes, deployment, or any other permanent mutation.

## 39. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_ARCHIVE_DESTINATION_COLLISION=ARCHIVE_DESTINATION_CONTRACT_COMPLETE`
