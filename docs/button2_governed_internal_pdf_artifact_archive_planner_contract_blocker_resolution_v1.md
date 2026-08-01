# Button 2 Governed Internal PDF Artifact Archive Planner Contract Blocker Resolution v1

## 1. Executive status

`PLANNER_CONTRACT_BLOCKERS_PARTIALLY_RESOLVED`

This document resolves the planner-specific design ambiguity that can be resolved on paper. It does not authorize implementation, configuration, inspection, execution, persistence, or release.

## 2. Locked baseline

- The archive-planning readiness assessment is resolved from full commit `0d4b20f04f90fdc1eba5eb63f7079122d1d5e0e4`.
- Readiness verdict: `READY_WITH_BLOCKERS`.
- The governed fixture is fictional and internal/test-only.
- Inspection is proven read-only.
- No planner, endpoint, dashboard planning control, or archive mutation exists.

## 3. Contract purpose

This document defines the exact normalized data contracts required before a future pure archive planner can be reconsidered. It covers the planner input envelope, inspection evidence, archive-root capability, destination evidence, authorization evidence, audit capability, concurrency evidence, sanitization, boundary IDs, destination-relative identity, deterministic output, blocked reasons, and unexpected-field handling.

The contracts are design decisions only. They do not grant authority to inspect, configure, create, copy, archive, remove, persist, or release anything.

## 4. Planner architecture decision

Adopt the smallest-authority architecture:

- one pure planning function;
- no direct filesystem access;
- no environment-variable access;
- no HTTP dependency;
- no dashboard dependency;
- no authentication implementation;
- no audit persistence;
- no mutable global state.

The planner consumes only already validated, bounded data objects. It returns a bounded plan evaluation, never execution authorization or proof that conditions remain safe later.

## 5. Proposed public function

A future implementation may expose a function equivalent to:

```text
build_button2_governed_internal_pdf_archive_plan_v1(
    governed_row,
    artifact_evidence,
    archive_root_capability,
    destination_evidence,
    authorization_evidence,
    audit_capability,
    concurrency_evidence,
    request_envelope,
)
```

This function is specified but not implemented here.

## 6. Exact planner request envelope

Required fields, with no unknown fields:

```text
contract_version
requested_action
fixture_id
report_id
report_version
expected_artifact_state
expected_filename
expected_sha256
expected_file_size_bytes
expected_page_count
archive_root_id
archive_root_version
archive_policy_id
request_id
idempotency_key
```

Optional bounded fields:

```text
approval_id
requested_at
correlation_id
```

`requested_action` must equal `plan_internal_pdf_archive`. Unknown fields are rejected with `unexpected_plan_fields`. Prohibited request fields are rejected, including `source_path`, `absolute_source_path`, `archive_path`, `destination_path`, `archive_root_path`, `temporary_path`, `customer_path`, `arbitrary_filename`, `arbitrary_directory`, `wildcard`, `glob`, `recursive`, `overwrite`, `force`, `skip_validation`, `skip_authorization`, `skip_audit`, `raw_pdf_bytes`, `arbitrary_report_content`, customer-ready authority, and customer-release authority.

### 6.1 Field types and bounds

The supported planner contract version is `button2-governed-internal-pdf-archive-planner-v1`. All identifiers are non-empty ASCII strings, contain no NUL or control character, and are at most 128 characters unless a more specific limit applies. `request_id`, `idempotency_key`, and `correlation_id` are at most 128 characters; `approval_id` is at most 128 characters; `archive_root_id`, `archive_root_version`, and `archive_policy_id` are at most 96 characters.

`fixture_id` is at most 64 characters, `report_id` at most 96 characters, and `report_version` at most 32 characters. `expected_filename` is a basename at most 160 characters. `expected_sha256` is exactly 64 lowercase hexadecimal characters. `expected_file_size_bytes` is a non-negative integer no greater than `2^63 - 1`. `expected_page_count` is a positive integer no greater than 10,000. `requested_at` is an optional bounded canonical timestamp string at most 64 characters; the planner does not read current time.

Every identifier and filename is validated for the path-component policy below. Contract versions and enumerated fields must be supported exact values.

## 7. Governed-row normalized contract

The planner may consume only these fields from a previously validated governed row:

```text
fixture_id
fixture_only
internal_only
test_fixture_only
report_id
report_version
classification
internal_warning
customer_ready
customer_release_authorized
queue_write_authorized
schema_version
provenance_source_type
provenance_source_id
provenance_verified
provenance_fixture_bound
```

The row must identify a fictional, governed, internal/test-only artifact: `fixture_only=true`, `internal_only=true`, `test_fixture_only=true`, `customer_ready=false`, `customer_release_authorized=false`, and `queue_write_authorized=false`. `classification` and `internal_warning` must match the existing governed fixture contract. Provenance indicators must be present, true, and bound to the fixture. Exact fixture, report, and version identity must match the request envelope and artifact evidence. Extra row fields are ignored only before normalization; the planner receives a normalized object with exact fields.

## 8. Artifact-evidence normalized contract

Required fields are:

```text
inspection_contract_version
inspection_completed
artifact_state
fixture_id
report_id
report_version
expected_filename
observed_filename
sha256
file_size_bytes
page_count
pdf_signature_valid
pdf_parse_valid
identity_valid
classification_valid
internal_warning_valid
source_boundary_id
customer_ready_possible
customer_release_authorized
queue_write_performed
pdf_generation_performed
artifact_archived
artifact_removed
artifact_overwritten
permanent_mutation_performed
```

`artifact_state` must equal `ACTIVE_INTERNAL_TEST_ARTIFACT`. `inspection_completed` and every validation boolean must be true. Expected and observed filename, hash, size, page count, identity, classification, and warning must match the bound request and governed row. `source_boundary_id` is required. All release and mutation flags must be false. Absent, blocked, corrupt, mismatched, invalid-signature, parse-failure, identity-mismatch, or forbidden-release-claim evidence is not archive eligible.

## 9. Archive-root capability contract

Required bounded fields are:

```text
capability_contract_version
archive_root_id
archive_root_version
archive_policy_id
configured
enabled
absolute_validated
server_controlled
customer_isolated
source_isolated
link_safe
platform
filesystem_policy_id
sanitization_policy_id
archive_boundary_id
```

The capability must be configured, enabled, absolutely validated by an external capability, server controlled, customer isolated, source isolated, and link safe. Its IDs and policies must exactly match the request. `platform` is a bounded enum; v1 recognizes `windows` and `posix`, with Windows collision rules applied whenever the target is case-insensitive. No absolute path may be supplied to or returned by the pure planner.

## 10. Boundary-identifier contract

`source_boundary_id` and `archive_boundary_id` must be server-issued, opaque or bounded, stable for the relevant configuration version, non-path values, separator-free, and incapable of granting filesystem authority. They must not contain `/`, `\\`, `:`, NUL, control characters, or whitespace at either edge. They must be at most 96 characters. They are identity evidence only; they are not paths or capabilities.

`destination_relative_id` is a derived logical identifier and is never an executable filesystem path.

## 11. Sanitization and platform policy

V1 rejects unsafe identity components rather than silently rewriting them. `fixture_id`, `report_id`, and `report_version` permit only ASCII letters, digits, underscore, hyphen, and period where explicitly allowed. Fixture and report IDs allow letters, digits, underscore, and hyphen only. Report version allows letters, digits, underscore, hyphen, and periods. No component may be empty, begin or end with a period, contain repeated traversal-like sequences, or be silently normalized into acceptance.

The already deterministic filename is preserved only after basename validation. Filename characters are limited to ASCII letters, digits, underscore, hyphen, period, and one required `.pdf` suffix; it must be a basename, must not begin or end with a period or whitespace, and must not contain an additional path component.

### 11.1 Unicode

Planner v1 accepts ASCII-safe archive identity components only. Non-ASCII identity components are blocked with `non_ascii_path_component`. No Unicode normalization is performed. This is a bounded initial policy, not a universal product limitation; platform expansion requires a separately reviewed contract version.

### 11.2 Windows reserved names

Case-insensitively block `CON`, `PRN`, `AUX`, `NUL`, `COM1` through `COM9`, and `LPT1` through `LPT9`, including when followed by an extension as Windows semantics require.

### 11.3 Separators, drives, UNC, and ADS

Reject `/`, `\\`, drive-colon syntax, UNC prefixes, any colon, alternate-data-stream syntax, NUL, control characters, `.` or `..` as complete components, leading or trailing whitespace, and trailing periods. No component may be interpreted as an absolute path or a drive-relative path.

### 11.4 Explicit lengths

The deterministic limits are: fixture ID 64 characters; report ID 96; report version 32; filename 160; each logical destination component 160; and complete `destination_relative_id` 512 characters. These limits are measured after validation and before response serialization. Later platform expansion requires a separately reviewed version.

## 12. Deterministic destination-relative identity

The exact construction is:

```text
fixture_id/report_id/report_version/expected_filename
```

All components must be validated accepted components. Forward slash is used only as the bounded logical separator in the response. The value has no leading or trailing slash, no empty component, no `.` or `..`, no absolute-path interpretation, and no executable filesystem meaning. Identical normalized inputs produce identical output.

Because v1 rejects unsafe values rather than normalizing them, accepted distinct inputs remain distinct. On a case-insensitive target, inputs differing only by case must be blocked with `identity_case_collision` unless server configuration supplies a reviewed collision-safe identity policy. No random suffix or alternate directory is selected.

## 13. Destination-evidence normalized contract

Required fields are:

```text
destination_evidence_contract_version
archive_root_id
archive_root_version
archive_policy_id
destination_relative_id
destination_status
collision_classification
destination_regular_file
destination_link_or_reparse
destination_inside_approved_root
source_destination_distinct
identity_match
sha256_match
file_size_match
page_count_match
classification_match
warning_match
evidence_completed
action_performed
```

`action_performed` must be false. The permitted destination classifications are `DESTINATION_EVIDENCE_NOT_EVALUATED`, `DESTINATION_ABSENT`, `IDENTICAL_ARCHIVE_PRESENT`, `CONFLICTING_ARCHIVE_PRESENT`, `DESTINATION_NON_REGULAR`, `DESTINATION_LINK_OR_REPARSE`, `DESTINATION_DIRECTORY_COLLISION`, `DESTINATION_OUTSIDE_APPROVED_ROOT`, `SOURCE_DESTINATION_SAME`, `IDENTITY_NORMALIZATION_COLLISION`, and `IDEMPOTENCY_CONFLICT`.

If destination evidence is missing, incomplete, stale, or not evaluated, the planner may return `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION`; it must not infer absence, access the filesystem, or return execution authorization.

## 14. Authorization-evidence normalized contract

Required fields are:

```text
authorization_contract_version
authorization_status
requested_action
fixture_id
report_id
report_version
operator_id
operator_role
approval_id
request_id
idempotency_key
planning_authorized
execution_authorized
authorization_expires_at
blocked_reason
evidence_completed
```

The planner consumes this prior bounded evaluation but does not authenticate actors, resolve roles, or validate sessions. An approval ID alone is not authorization. `planning_authorized=true` is required for `ARCHIVE_PLAN_READY`; `execution_authorized` must remain false in every planner output.

## 15. Audit-capability normalized contract

Required fields are:

```text
audit_capability_contract_version
audit_sink_id
audit_sink_available
schema_supported
planning_event_supported
persistence_authorized
action_performed
```

The planner may require a planning capability and may return a bounded audit-event plan. It must not persist anything. `action_performed=false` is mandatory. Missing capability produces `ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY`.

## 16. Concurrency-evidence normalized contract

Required fields are:

```text
concurrency_contract_version
artifact_action_active
conflicting_action
artifact_version_token
source_evidence_current
destination_evidence_current
evaluated_at
evidence_completed
```

The planner blocks when another action is active, source evidence is stale, destination evidence is stale, evidence is incomplete, or a conflicting archive, removal, quarantine, deactivation, or restoration action exists. The planner does not implement locking or reservations.

## 17. Request and idempotency binding

The canonical fingerprint input sequence is: requested action; fixture ID; report ID; report version; expected artifact state; expected filename; SHA-256; size; page count; archive-root ID and version; archive policy; destination-relative ID; and approval ID where applicable. The planner compares supplied bounded evidence against this canonical sequence. A hashing implementation is not prescribed here. Conflicting reuse produces `idempotency_conflict`; identical accepted replay may produce `ARCHIVE_ALREADY_SATISFIED` when the destination evidence is identical.

## 18. Planner outcomes

Only these response statuses are permitted:

- `ARCHIVE_PLAN_READY`;
- `ARCHIVE_PLAN_BLOCKED`;
- `ARCHIVE_ALREADY_SATISFIED`;
- `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION`;
- `ARCHIVE_PLAN_REQUIRES_AUTHORIZATION`;
- `ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY`;
- `ARCHIVE_PLAN_REQUIRES_CURRENT_CONCURRENCY_EVIDENCE`.

These are response statuses only, not persisted lifecycle states. A ready response uses design-only proposed state `ARCHIVE_PLANNED`; it is not persisted, does not mean bytes were copied, and grants no execution authority.

### 18.1 Ready requirements

`ARCHIVE_PLAN_READY` requires a valid request, exact governed-row identity, active valid artifact evidence, matched metadata, valid archive capability, valid destination identity, `DESTINATION_ABSENT`, distinct source and destination, planning authorization, audit planning capability, current conflict-free concurrency evidence, valid idempotency evidence, and every mutation flag false.

### 18.2 Already satisfied requirements

`ARCHIVE_ALREADY_SATISFIED` requires `IDENTICAL_ARCHIVE_PRESENT`, matching identity and all metadata, accepted idempotency evidence, no copy required, no mutation performed, and an explicit statement that this is not a new archive action.

## 19. Deterministic plan response schema

The exact response fields are:

```text
contract_version
ok
status
requested_action
fixture_id
report_id
report_version
current_artifact_state
proposed_state
filename
expected_sha256
expected_file_size_bytes
expected_page_count
source_boundary_id
archive_boundary_id
archive_root_id
archive_root_version
archive_policy_id
destination_relative_id
destination_status
collision_classification
source_destination_distinct
authorization_status
audit_sink_available
concurrency_status
planning_authorized
execution_authorized
action_performed
request_id
idempotency_key
approval_id
blocked_reason
safety_flags
```

No response field may contain an absolute path, unrestricted source text, raw PDF bytes, filesystem path, or secret. Response field order, enum values, and safety flags are deterministic.

## 20. Closed blocked-reason registry

The canonical registry is:

```text
invalid_plan_contract
unexpected_plan_fields
unsupported_contract_version
fixture_governance_blocked
governed_row_identity_mismatch
artifact_state_not_archive_eligible
artifact_identity_mismatch
filename_mismatch
sha256_mismatch
file_size_mismatch
page_count_mismatch
signature_validation_failed
parse_validation_failed
classification_mismatch
internal_warning_missing
forbidden_release_claim_present
archive_root_missing
archive_root_disabled
archive_root_invalid
archive_root_identity_mismatch
archive_policy_missing
sanitization_policy_mismatch
invalid_path_component
non_ascii_path_component
reserved_path_component
path_component_too_long
relative_identifier_too_long
identity_case_collision
destination_evidence_missing
destination_evidence_stale
source_destination_same
archive_destination_collision
destination_link_or_reparse
destination_non_regular
destination_outside_approved_root
authorization_not_satisfied
approval_not_satisfied
authorization_evidence_stale
audit_capability_unavailable
audit_schema_unsupported
concurrency_evidence_missing
concurrency_evidence_stale
concurrency_conflict
idempotency_conflict
planning_not_authorized
```

Unknown blocked reasons fail validation and may not pass through as arbitrary text.

## 21. Safety flags

Every response contains exactly these flags, all false:

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

## 22. Purity, determinism, and validation order

Identical normalized inputs must produce identical output. The planner performs no current-time lookup, randomness, environment access, filesystem access, network access, directory scan, mutable module-level state, unrestricted-path logging, or hidden fallback.

Fail closed in this order:

1. contract version;
2. unexpected fields;
3. request types and bounds;
4. governed-row gates;
5. identity matching;
6. artifact state and evidence;
7. archive-root capability;
8. component policy;
9. destination-relative derivation;
10. destination evidence;
11. authorization evidence;
12. audit capability;
13. concurrency evidence;
14. idempotency binding;
15. safety flags;
16. deterministic response.

## 23. Testing contract

Focused tests must cover a valid ready plan; repeated deterministic output; identical archive; missing destination evidence; absent and blocked artifact; identity, filename, hash, size, page, signature, parse, classification, warning, and release-claim failures; missing, disabled, invalid, and mismatched archive root; boundary mismatch; separator, traversal, drive, UNC, ADS, non-ASCII, reserved-name, excessive-length, and case-collision inputs; destination collision, link/reparse, non-regular, outside-root, and same-source cases; missing authorization; unavailable audit capability; concurrency conflict and stale evidence; idempotency conflict; unexpected fields; every mutation flag false; no absolute-path output; and no filesystem changes.

## 24. Resolved blockers

This contract resolves, at the design level:

- normalized request schema;
- normalized inspection evidence;
- archive-root capability schema;
- boundary identifiers;
- destination-relative identity;
- path-component policy;
- Unicode v1 policy;
- Windows reserved-name policy;
- component and relative-path limits;
- destination-evidence schema;
- authorization input;
- audit-capability input;
- concurrency-evidence input;
- blocked-reason registry;
- deterministic response schema.

## 25. Remaining blockers

The remaining blockers are implementation dependencies, not unresolved contract choices:

- no approved concrete archive-root capability fixture;
- no approved concrete boundary IDs;
- no approved destination-inspection evidence producer;
- no approved authorization-evidence producer;
- no approved audit-capability producer;
- no approved concurrency-evidence producer;
- no implementation file;
- no focused tests;
- no direct proof.

## 26. Implementation-readiness effect

`CONTRACT_READY_FOR_IMPLEMENTATION_REASSESSMENT`

This means only that the contract blockers are sufficiently specified for a separate readiness reassessment. It does not directly authorize implementation.

## 27. Smallest safe next slice

Recommend exactly one docs-only slice: Button 2 governed internal PDF pure archive-plan adapter implementation-readiness reassessment.

Proposed file:

`docs/button2_governed_internal_pdf_artifact_archive_plan_adapter_implementation_readiness_reassessment_v1.md`

Do not recommend an endpoint, dashboard, or archive mutation in that slice.

## 28. Recommended sequencing

A. Planner contract blocker resolution.
B. Pure planner implementation-readiness reassessment.
C. Separately authorized pure archive-plan adapter.
D. Focused planner tests.
E. Direct non-mutating proof.
F. Planning endpoint readiness assessment.
G. Planning endpoint and route test.
H. Live route proof.
I. Dashboard planning-control readiness.
J. Dashboard control and test.
K. Live dashboard proof.
L. Archive mutation implementation-readiness assessment.
M. Separately authorized copy-and-retain archive implementation.

## 29. Explicit non-authorization

This contract does not authorize planner implementation; destination-inspection, authorization, audit-capability, or concurrency implementation; endpoint or dashboard implementation; archive-root configuration; directory or temporary-file creation; copy; archive; finalization; source removal; quarantine; deactivation; restoration; deletion; secure deletion; rename; movement; overwrite; audit persistence; lifecycle persistence; customer-ready classification; customer release; queue or ledger writes; learning; calibration; accuracy-ledger writes; GCID writes; model or fighter-rating changes; prediction-logic changes; or deployment.

## 30. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_ARCHIVE_PLANNER_CONTRACT_BLOCKERS=PLANNER_CONTRACT_BLOCKERS_PARTIALLY_RESOLVED`
