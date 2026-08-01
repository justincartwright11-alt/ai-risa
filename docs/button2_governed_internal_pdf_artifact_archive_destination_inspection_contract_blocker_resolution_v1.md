# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Contract Blocker Resolution v1

## 1. Executive status

`DESTINATION_INSPECTION_CONTRACT_BLOCKERS_PARTIALLY_RESOLVED`

This document resolves the destination-inspection contract decisions that are supportable from the locked planner, collision, threat, authorization, and read-only inspection evidence. It leaves a small set of explicitly named platform, resource, private-capability, parser, metadata, and test-authority decisions open. Resolution does not authorize implementation.

## 2. Locked baseline

- Readiness-assessment commit: `84d192a0bc7f69a6a214e91128ef6d8806010ea9`
- Readiness verdict: `READY_FOR_DESTINATION_INSPECTION_CONTRACT_RESOLUTION`
- Direct-proof closure: `61bcdf47405833819681187bcf830ab154c8d929`
- Pure planner commit: `b14ce73eef63c61c688a8110d55c01d8a205029f`
- The governed fixture is fictional only.
- Referenced artifacts are internal/test-only.
- No destination-inspection adapter exists.
- No concrete archive root is approved.
- No endpoint, dashboard control, or archive mutation exists.

## 3. Contract purpose

This document defines the exact bounded contracts required for a future read-only destination-inspection capability. It resolves the public boundary, request and source evidence, archive-root capability, private root handling, logical identity, target derivation, containment, Windows policy, component and parent inspection, link/reparse handling, source/destination separation, destination classifications, existing-file verification, response schema, blocked reasons, validation order, freshness, resource boundaries, and focused tests.

It defines future intent and evidence contracts only. It does not implement or authorize inspection, root configuration, endpoint exposure, or mutation.

## 4. Capability architecture decision

A. The archive-root capability producer resolves approved server configuration and produces bounded root identity plus a private inspection capability.

B. The destination-inspection adapter performs one bounded read-only inspection of one deterministic target.

C. The pure archive planner consumes normalized destination evidence and performs no filesystem access.

D. The archive-execution adapter remains nonexistent and separately governed.

The destination inspector must not plan, authenticate users, approve requests, persist audit events, acquire lifecycle locks, create or modify filesystem objects, or execute an archive. Destination evidence is observational and never execution authority.

## 5. Proposed public function

A future adapter may expose one function equivalent to:

```text
inspect_button2_governed_internal_pdf_archive_destination_v1(
    archive_root_capability,
    source_artifact_evidence,
    destination_request,
)
```

The function accepts exactly three normalized dictionaries and returns exactly one bounded dictionary. It must reject unknown fields and malformed nested contracts. It must not expose or return an absolute path.

## 6. Public-argument ownership

`archive_root_capability` is server-produced. It contains bounded IDs and booleans plus a private server-side target capability. It is never browser-produced or caller-selected.

`source_artifact_evidence` is normalized from the proven active-artifact inspection chain. It contains bounded source identity, metadata, boundary evidence, and a private server target reference where source comparison is required. It contains no caller-selected source path.

`destination_request` contains bounded identities and expected metadata only. It contains no absolute path, root path, parent path, file bytes, or authority claim.

## 7. Strict read-only invariant

The future adapter may not create directories or files, open for write, create temporary files, copy, move, rename, replace, finalize, overwrite, truncate, delete, remove, quarantine, deactivate, restore, persist lifecycle state, persist audit state, or write queues or ledgers. It may not acquire a lock or reserve a destination. It must return `action_performed=false` and every safety flag false.

## 8. Allowed imports and operations

The minimum future authority is limited to:

- `pathlib` or equivalent bounded path handling for one derived target;
- `os.lstat` and `os.stat` or equivalent read-only object metadata;
- read-only file open after regular-file and link checks;
- SHA-256 calculation over bounded file content;
- bounded PDF signature and parse validation;
- platform detection for the explicit Windows gate;
- file-identity comparison using supported read-only metadata.

Each operation must be target-specific and justified by the normalized output. Mutation-capable modules may not be used for mutation even if imported for a read-only helper. No `mkdir`, `makedirs`, write, unlink, remove, rmdir, rename, replace, copy, move, tempfile creation, subprocess mutation, recursive scan, wildcard expansion, network, environment-selected root, or database access is permitted.

## 9. Contract-version constants

The future contract must use these exact versions:

- destination request: `button2-governed-internal-pdf-destination-inspection-v1`
- source-artifact evidence: `button2-governed-internal-pdf-artifact-inspection-v1`
- archive-root capability: `button2-governed-internal-pdf-archive-root-capability-v1`
- destination-evidence response: `button2-governed-internal-pdf-destination-evidence-v1`
- filesystem policy: `windows-safe-v1`
- sanitization policy: `ascii-reject-v1`

Unknown, missing, or future versions fail closed as `unsupported_contract_version`.

## 10. Exact destination-request schema

The request has no unknown fields and contains exactly:

```text
contract_version
requested_action
fixture_id
report_id
report_version
expected_filename
expected_sha256
expected_file_size_bytes
expected_page_count
source_boundary_id
archive_root_id
archive_root_version
archive_policy_id
archive_boundary_id
destination_relative_id
request_id
idempotency_key
```

`requested_action` must equal `inspect_internal_pdf_archive_destination`.

## 11. Field types and bounds

- All identifiers are non-empty ASCII strings with no NUL, control characters, or edge whitespace.
- `fixture_id` is at most 64 characters.
- `report_id` is at most 96 characters.
- `report_version` is at most 32 characters.
- `expected_filename` is a basename at most 160 characters and must end in `.pdf`.
- `source_boundary_id` and `archive_boundary_id` are bounded non-path strings at most 96 characters.
- `archive_root_id`, `archive_root_version`, and `archive_policy_id` are at most 96 characters.
- `request_id` and `idempotency_key` are at most 128 characters.
- `expected_sha256` is exactly 64 lowercase hexadecimal characters.
- `expected_file_size_bytes` is an actual integer, not a boolean, from 0 through `2^63 - 1`.
- `expected_page_count` is an actual integer, not a boolean, from 1 through 10,000.
- `destination_relative_id` is at most 512 characters.

No implicit coercion, trimming into acceptance, or boolean-as-integer acceptance is allowed.

## 12. Prohibited request fields

Reject `source_path`, `destination_path`, `archive_root_path`, `absolute_path`, `parent_path`, `temporary_path`, UNC and drive paths, arbitrary directory or filename, wildcard, glob, recursive, create, mkdir, overwrite, force, copy, move, rename, delete, cleanup, raw PDF bytes, caller-selected archive root, customer path, skip validation, skip authorization, and arbitrary report content. Reject all aliases that could carry these meanings.

## 13. Source-artifact evidence contract

The normalized source evidence requires:

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
source_capability_id
customer_ready_possible
customer_release_authorized
queue_write_performed
pdf_generation_performed
artifact_archived
artifact_removed
artifact_overwritten
permanent_mutation_performed
```

`source_capability_id` is a bounded opaque reference to a server-held source target, not a path. The inspector may compare source and destination through private server capabilities and filesystem identity, but may return only boundary IDs and bounded comparison results. It must never return the source absolute path.

## 14. Archive-root capability and private root contract

Planner-facing bounded fields are:

```text
capability_contract_version
archive_root_id
archive_root_version
archive_policy_id
archive_boundary_id
configured
enabled
server_controlled
customer_isolated
source_isolated
link_safe
platform
filesystem_policy_id
sanitization_policy_id
```

The private server-side inspection capability additionally contains an approved absolute root target or opaque capability handle, produced only from trusted server configuration. It is never accepted from browser input, placed in destination evidence, returned in responses, logged, or exposed to the planner. Where feasible it must be structurally or cryptographically bound to the bounded root ID, version, policy, and boundary.

The private-handle representation remains an implementation design decision and must be resolved before implementation reassessment; no handle is selected here.

## 15. Concrete archive-root status

No concrete root is approved in this slice. The contract can be resolved without selecting a production or local root. A later adapter may use a separately approved test-only capability fixture. Endpoint and mutation integration require a separately approved configured root, owner, isolation proof, versioning source, and platform validation.

## 16. Platform policy

V1 is Windows-only. The capability must report `platform=windows`; all other platforms fail closed with response status `DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM` and reason `unsupported_platform`. No portability claim is made. A later platform requires a new reviewed contract version and platform-specific direct proof.

## 17. Component policy

V1 is ASCII-only and rejects unsafe input rather than normalizing it into acceptance. Fixture and report IDs use ASCII letters, digits, underscore, and hyphen. Report versions additionally permit periods. Filenames use ASCII letters, digits, underscore, hyphen, and periods, with a required `.pdf` suffix.

Reject separators, colons, ADS syntax, NUL, controls, non-ASCII characters, leading or trailing whitespace, trailing periods, `.` and `..`, empty components, reserved Windows device names, excessive lengths, and any drive or UNC interpretation. No random suffix, alternate identity, or alternate directory is selected.

## 18. Destination-relative identity

The exact logical construction is:

`fixture_id/report_id/report_version/expected_filename`

It has exactly four components separated only by logical forward slashes. It has no leading or trailing slash, empty component, dot component, absolute interpretation, drive form, UNC form, or ADS syntax. The adapter reconstructs this value from the validated request and compares it byte-for-byte with the request value before target derivation. A mismatch returns `invalid_destination_relative_id`.

The value is a logical identifier, not a filesystem path. Only the private server-side inspector may combine it with the approved root. It grants no authority on its own.

## 19. Root-to-target derivation

The exact order is:

1. validate the root capability contract;
2. obtain the private approved root capability;
3. validate all four logical components;
4. reconstruct the logical destination identifier;
5. compare it with the request;
6. join the four components to the approved root without current-working-directory dependence;
7. perform lexical containment;
8. inspect every existing root and parent component for links/reparse and object type;
9. perform resolved containment where safe;
10. inspect the parent chain and final target read-only;
11. compare source and destination boundaries and file identity;
12. verify an existing target's bounded PDF and metadata.

No directory creation or fallback target selection occurs.

## 20. Lexical and resolved containment

The derived target must be a strict descendant of the approved root. Equality with the root, `..`, drive changes, UNC changes, alternate-prefix substitution, and root escape are blocked before filesystem inspection. Lexical containment is necessary but never sufficient.

The approved root is validated first. Every existing parent is inspected. Any symlink, junction, mount redirection, reparse point, unsupported special object, access-denied condition, or resolution failure blocks or returns unavailable; none is treated as absence. The final resolved target must remain below the approved resolved root.

## 21. Archive-root object controls

The root must be present for a real inspection, be a directory, not be a file, symlink, junction, reparse point, mount redirection, or unsupported special object, and match configured ID, version, policy, boundary, and platform. An absent root may appear only in contract-only test data and must never be reported as a valid destination inspection.

## 22. Parent-chain classifications

The exact parent conditions are:

- valid parent chain: continue;
- `parent_missing`: inspection unavailable or blocked; never `DESTINATION_ABSENT`;
- `parent_non_directory`: blocked;
- `parent_link_or_reparse`: blocked;
- parent outside approved root: blocked as `destination_outside_approved_root`;
- `parent_access_denied`: unavailable;
- `parent_inspection_failed`: unavailable.

A missing parent cannot establish that the approved destination boundary was fully inspected, so it is not destination absence.

## 23. Final-target classifications and ownership

The destination inspector may emit exactly: `DESTINATION_ABSENT`, `IDENTICAL_ARCHIVE_PRESENT`, `CONFLICTING_ARCHIVE_PRESENT`, `DESTINATION_NON_REGULAR`, `DESTINATION_LINK_OR_REPARSE`, `DESTINATION_DIRECTORY_COLLISION`, `DESTINATION_OUTSIDE_APPROVED_ROOT`, `SOURCE_DESTINATION_SAME`, and `IDENTITY_NORMALIZATION_COLLISION`.

`IDEMPOTENCY_CONFLICT`, authorization, audit, concurrency, and lifecycle-state conflicts remain outside this adapter and belong to their respective producer or the pure planner.

## 24. Existing-target object inspection

Use `lstat` before following the final target. Block links/reparse points, directories, devices, sockets, pipes, and other non-regular special objects. Open read-only only after object validation, and revalidate identity after open where platform support permits. No write, lock, reservation, or mutation occurs.

## 25. Source/destination separation and aliases

Compare source and archive boundary IDs; logical source and destination identity; resolved private targets; volume/file identifiers where available; hard-link indicators where available; and Windows case-folded identity. If safe file-identity comparison is unavailable, return `source_destination_identity_unavailable` and do not claim identical or absent safety. Block same resolved target, same file identity, hard-link alias where detectable, root nesting conflict, and normalization alias.

Windows v1 compares accepted identity case-insensitively for collision detection. Inputs differing only by case may return `IDENTITY_NORMALIZATION_COLLISION`; no suffix or alternate destination is permitted. No Unicode normalization occurs because v1 is ASCII-only. Complete hard-link and file-identity semantics require implementation-level Windows proof.

## 26. Existing PDF and trusted metadata verification

For a regular existing target, require expected filename, PDF signature, bounded parse validity, SHA-256, size, page count, and source/destination distinction. Classification, internal warning, and provenance must be supplied through separate trusted bounded metadata evidence. They must not be inferred from arbitrary PDF text.

The first adapter therefore consumes trusted destination metadata evidence when identity/classification/warning comparison is required. If that evidence is absent or invalid, it must not return `IDENTICAL_ARCHIVE_PRESENT`; it returns `classification_evidence_missing`, `warning_evidence_missing`, or `trusted_metadata_invalid` according to the first failed rule. The exact trusted metadata envelope remains a blocker before implementation.

## 27. Identical, conflicting, and absent criteria

`IDENTICAL_ARCHIVE_PRESENT` requires a regular contained file with no link/reparse condition; distinct source and destination; matched filename, SHA-256, size, page count, signature, parse, identity, classification, warning, root identity, policy, and complete trusted metadata. It cannot be returned when required evidence is unknown.

`CONFLICTING_ARCHIVE_PRESENT` applies to an existing regular target with any required identity, hash, size, page, signature, parse, classification, warning, provenance, policy, or expected-evidence mismatch. No overwrite, alternate name, suffix, removal, or cleanup is suggested.

`DESTINATION_ABSENT` requires valid root, valid complete parent chain, no links/reparse, contained target, no access error, no directory collision, completed inspection, and a non-existent final target. Missing or inaccessible parent/root never becomes absence.

## 28. Destination-evidence response schema

The bounded result contains exactly these conceptual fields:

```text
contract_version
ok
status
requested_action
inspection_completed
fixture_id
report_id
report_version
expected_filename
expected_sha256
expected_file_size_bytes
expected_page_count
source_boundary_id
archive_root_id
archive_root_version
archive_policy_id
archive_boundary_id
destination_relative_id
destination_status
collision_classification
destination_exists
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
pdf_signature_valid
pdf_parse_valid
evidence_version_token
evaluated_at
request_id
idempotency_key
blocked_reason
action_performed
safety_flags
```

No absolute path, private handle, raw bytes, exception text, directory listing, or unrelated entry is returned.

## 29. Response statuses

Permit exactly:

- `DESTINATION_INSPECTION_COMPLETE`
- `DESTINATION_INSPECTION_BLOCKED`
- `DESTINATION_INSPECTION_UNAVAILABLE`
- `DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM`

`status` is the response status. `destination_status` is the bounded target classification. Neither is a lifecycle state, permission, execution approval, or persisted transition.

## 30. Closed blocked-reason registry

The exact proposed registry is:

```text
invalid_destination_inspection_contract
unexpected_destination_inspection_fields
unsupported_contract_version
source_artifact_evidence_invalid
source_artifact_state_not_eligible
source_artifact_identity_mismatch
archive_root_missing
archive_root_disabled
archive_root_invalid
archive_root_not_directory
archive_root_link_or_reparse
archive_root_identity_mismatch
archive_policy_mismatch
archive_boundary_mismatch
unsupported_platform
invalid_destination_relative_id
invalid_path_component
reserved_path_component
non_ascii_path_component
path_component_too_long
relative_identifier_too_long
identity_normalization_collision
destination_outside_approved_root
parent_missing
parent_non_directory
parent_link_or_reparse
parent_access_denied
parent_inspection_failed
destination_link_or_reparse
destination_non_regular
destination_directory_collision
destination_access_denied
destination_inspection_failed
source_destination_same
source_destination_identity_unavailable
pdf_signature_validation_failed
pdf_parse_validation_failed
destination_identity_mismatch
sha256_mismatch
file_size_mismatch
page_count_mismatch
classification_evidence_missing
classification_mismatch
warning_evidence_missing
warning_mismatch
trusted_metadata_invalid
resource_limit_exceeded
inspection_not_authorized
```

Unknown internal reasons map to the bounded generic `destination_inspection_failed` and disclose no exception details.

## 31. Error mapping and validation order

Malformed request, unknown field, invalid evidence, identity mismatch, or unsafe component returns `DESTINATION_INSPECTION_BLOCKED`. Unsupported platform returns `DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM`. Missing or unavailable trusted configuration, root capability, parent access, or inspection capability returns `DESTINATION_INSPECTION_UNAVAILABLE`. A successfully inspected collision may return `DESTINATION_INSPECTION_COMPLETE` with its bounded destination classification. Unexpected faults return unavailable with `destination_inspection_failed`.

Validation order is:

1. contract versions;
2. unexpected fields;
3. request types and bounds;
4. source-artifact evidence;
5. cross-object identity;
6. archive-root capability;
7. platform gate;
8. destination-relative identity;
9. component policy;
10. root object validation;
11. lexical containment;
12. parent-chain inspection;
13. final-target object inspection;
14. resolved containment;
15. source/destination separation;
16. signature and parse;
17. metadata calculation;
18. trusted classification/warning evidence;
19. destination classification;
20. freshness fields;
21. safety flags;
22. deterministic response.

The first failed validation determines the canonical reason unless an explicitly owned destination classification applies.

## 32. Freshness and time policy

The capability producer supplies `evaluated_at`, `evidence_version_token`, root capability version, source artifact version token where available, destination metadata fingerprint, request ID, and idempotency key. The adapter does not obtain current time; producer-supplied time is evidence data. Browser time is never trusted.

The evidence is observational, may become stale immediately, does not reserve the path, and requires mandatory reinspection before any separately authorized mutation. Exact validity-window duration remains a later concurrency/policy decision and is not silently assumed by the pure planner.

## 33. Resource and parser controls

The adapter inspects exactly one deterministic destination, performs no recursive scan, newest-file search, or wildcard expansion, and enforces the already locked 512-character logical identifier and 10,000-page maximum where applicable. The existing evidence does not support a safe new numeric maximum file size, hash-byte budget, parser timeout, or decompression limit, so those values remain implementation-readiness blockers rather than invented contract facts.

The parser must be bounded, perform no embedded-content execution, resolve no external resources, use no network, and apply bounded decompression. Process isolation or a timeout policy is required if the selected parser cannot guarantee those properties; the implementation choice remains open.

## 34. TOCTOU boundary

Inspection is observational. Absence may become stale immediately; links, parents, target identity, metadata, root configuration, or authorization may change after inspection. Later mutation must revalidate root, parents, target, identity, metadata, collision, authorization, audit, and concurrency immediately before finalization. Destination evidence never grants execution authority.

## 35. Safety flags and path non-disclosure

Every response preserves exactly false:

```text
customer_ready_possible
customer_release_authorized
queue_write_performed
pdf_generation_performed
learning_applied
calibration_applied
accuracy_ledger_written
gcid_written
model_weights_changed
fighter_ratings_changed
prediction_logic_changed
artifact_archived
artifact_removed
artifact_overwritten
permanent_mutation_performed
action_performed
```

Responses may contain bounded IDs, versions, policy IDs, logical destination identity, metadata results, statuses, and reasons only. They never contain archive-root, destination, source, parent, resolved, temporary, customer, or unrelated paths, raw exception text, or directory listings.

## 36. Focused testing contract

Future focused tests must cover valid absent destination; identical archive; conflict; missing/disabled/invalid root; root non-directory or reparse; unsupported platform; invalid identifier, traversal, separator, reserved name, and case collision; missing, non-directory, reparse, or inaccessible parent; final directory, special object, reparse, or outside-root target; same source/destination and hard-link alias where supported; valid PDF; signature and parse failure; hash, size, and page mismatch; missing trusted classification or warning; resource-limit failure; path non-disclosure; all safety flags false; and no filesystem mutation.

Use only pytest temporary directories or separately approved test-only capability fixtures. Never inspect customer or production paths. Windows-specific reparse and junction tests are platform-gated and require separate test authority where the OS requires it. Tests create only synthetic internal/test files and perform no archive copy or removal.

Static tests must inspect the adapter source or AST for absence of `mkdir`, `makedirs`, `touch`, write, unlink, remove, rmdir, rename, replace, copy, move, tempfile creation, and subprocess mutation calls, while allowing only explicitly approved read operations.

## 37. Contract blockers resolved

This document resolves, at the design level: public function boundary; argument ownership; strict read-only invariant; exact version identities; request field set and reusable bounds; prohibited fields; source evidence boundary; bounded root fields and private-root principle; Windows-only fail-closed policy; ASCII component policy; four-component logical identity; target derivation order; lexical and resolved containment principles; root and parent controls; destination classification ownership; source/destination alias categories; output shape; response statuses; blocked-reason candidates; validation order; producer-supplied freshness; path non-disclosure; false safety flags; and focused-test scope.

## 38. Remaining contract blockers

The following are the only remaining design blockers before implementation reassessment:

- exact trusted destination metadata envelope for classification, warning, and provenance;
- private server capability-handle representation and binding mechanism;
- approved numerical file-size, hash-cost, parser, and decompression limits;
- parser timeout or process-isolation selection;
- Windows file-identity and hard-link API strategy;
- authority and feasibility of reparse/junction direct tests;
- exact parent-missing and access-denied mapping where a producer cannot distinguish unavailable from blocked.

These are contract or implementation-readiness decisions, not missing-code findings.

## 39. Implementation dependencies

Later work requires an approved test-only archive-root capability fixture, a root capability producer, trusted destination metadata fixture, the separately authorized read-only adapter, focused tests, and direct proof. No endpoint or mutation work may begin from this document.

## 40. Contract effect

`CONTRACT_READY_WITH_REMAINING_BLOCKERS`

The resolved contract decisions are sufficient to narrow the next assessment, but the remaining blockers prevent a clean implementation-readiness recommendation.

## 41. Endpoint, dashboard, and archive-mutation status

- `NOT_READY_FOR_ENDPOINT`
- `NOT_READY_FOR_DASHBOARD`
- `NOT_READY_FOR_ARCHIVE_MUTATION`

## 42. Smallest safe next slice

The smallest safe next slice is exactly: **Button 2 governed internal PDF archive destination-inspection trusted metadata and resource-boundary contract resolution.**

Proposed file: `docs/button2_governed_internal_pdf_artifact_archive_destination_inspection_trusted_metadata_resource_contract_resolution_v1.md`

Do not recommend implementation, endpoint, dashboard, or mutation.

## 43. Recommended sequencing

A. destination-inspection contract blocker resolution; B. trusted metadata and resource-boundary contract resolution; C. destination-inspection implementation-readiness reassessment; D. separately authorised read-only destination-inspection adapter; E. focused adapter tests; F. direct read-only proof; G. supporting capability-producer readiness; H. archive-planning endpoint readiness; I. endpoint implementation and route test; J. live route proof; K. dashboard planning-control readiness; L. dashboard implementation and proof; M. archive-mutation readiness; N. separately authorised copy-and-retain archive implementation.

## 44. Explicit non-authorization

This contract does not authorize destination-inspection implementation, root configuration, capability producer, metadata producer, test fixture creation, endpoint, route, dashboard, directory creation, file creation, temporary-file creation, PDF generation, copy, archive, finalization, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit persistence, lifecycle persistence, customer-ready classification, customer release, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 45. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_CONTRACT_BLOCKERS=DESTINATION_INSPECTION_CONTRACT_BLOCKERS_PARTIALLY_RESOLVED`
