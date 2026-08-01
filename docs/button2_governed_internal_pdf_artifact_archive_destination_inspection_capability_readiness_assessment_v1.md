# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Capability Readiness Assessment v1

## 1. Executive verdict

`READY_FOR_DESTINATION_INSPECTION_CONTRACT_RESOLUTION`

The repository evidence is sufficient to begin a documentation-only contract-resolution slice for a future read-only destination-inspection capability. This positive finding authorizes only further documentation or contract work. It does not authorize implementation, archive-root configuration, filesystem inspection runtime, endpoint or dashboard exposure, archive execution, or mutation.

## 2. Locked baseline

- Direct-proof closure commit: `61bcdf47405833819681187bcf830ab154c8d929`
- Pure planner implementation commit: `b14ce73eef63c61c688a8110d55c01d8a205029f`
- Direct-proof closure verdict: `DIRECT_PROOF_CLOSED_PASS`
- The governed fixture is fictional only.
- The artifact is internal/test-only.
- No destination-inspection capability is currently implemented.
- No concrete archive root is approved.
- No archive mutation is implemented.

The pure planner consumes normalized in-memory evidence and returns `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION` when destination evidence is unavailable. Existing artifact inspection is read-only, but it inspects a deterministic active output target from a preflight plan; it is not an archive destination-inspection capability.

## 3. Assessment purpose

A future capability may, after separate authorization, accept bounded server-derived archive-root capability evidence and a bounded destination-relative identifier; derive a target inside an approved archive root; inspect existence, type, links, reparse state, containment, and source/destination separation read-only; inspect an existing regular PDF; compare identity and metadata; classify destination state; return normalized destination evidence; disclose no absolute path; and perform no mutation.

This assessment distinguishes contract readiness, adapter readiness, root configuration, evidence production, endpoint readiness, dashboard readiness, and mutation readiness. Missing implementation is not itself a contract defect; unresolved policy and evidence ownership are.

## 4. Capability ownership boundary

| Boundary | Proper responsibility | Destination adapter may do |
|---|---|---|
| Pure archive planner | Evaluate supplied normalized evidence and produce a bounded plan | Nothing filesystem-specific |
| Archive-root capability producer | Select and validate a server-controlled approved root; issue bounded identity and capability evidence | Consume its bounded output |
| Destination-inspection adapter | Derive and inspect one deterministic destination read-only | Inspect only its assigned target |
| Authorization producer | Authenticate and evaluate action authority | Remain separate |
| Audit-capability producer | Provide bounded sink capability evidence | Remain separate; no persistence |
| Concurrency-evidence producer | Provide current version/conflict evidence | Remain separate; no locking |
| Archive-execution adapter | Revalidate and copy/retain under separate authority | Never be called by inspection |

Destination inspection must remain separate from planning, authorization, audit persistence, locking, copy, archive execution, and source removal. Inspection evidence is observational and grants no execution authority.

## 5. Proposed read-only capability

A future function equivalent to:

```text
inspect_button2_governed_internal_pdf_archive_destination_v1(
    archive_root_capability,
    source_artifact_evidence,
    destination_request,
)
```

is conceptually appropriate. The three arguments are sufficient only if `archive_root_capability` contains server-derived root identity and hidden validated root configuration, `source_artifact_evidence` contains bounded source identity and metadata plus source boundary evidence, and `destination_request` contains the exact planner-bound logical identity and expected metadata. None may contain caller-selected absolute paths. Exact field types, versioning, platform policy, resource limits, parent-state taxonomy, and freshness semantics require contract resolution.

## 6. Proposed implementation scope

The smallest future implementation scope should be exactly:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

These files are not authorized in this slice. No producer, route, dashboard, fixture, archive root, or mutation file belongs in that future two-file slice unless separately authorized.

## 7. Strict read-only invariant

The future capability must perform no directory creation, file creation, write-open, temporary-file creation, copy, move, rename, replacement, finalization, overwrite, deletion, source removal, quarantine, deactivation, restoration, audit persistence, lifecycle persistence, queue write, or ledger write. It must return `action_performed=false` and all mutation flags false. It must not create a parent merely because the deterministic destination is absent.

## 8. Allowed read-only operations

The following operations are potentially justified, narrowly bounded, and target-specific:

- root configuration lookup: select the server-approved hidden root, never caller input;
- path joining: combine the approved root with already validated four-component identity;
- lexical containment: reject obvious traversal and root escape before filesystem access;
- resolved containment: detect symlink, junction, mount, reparse, and canonical escape;
- `lstat` and `stat`: classify each root, parent, and final target without following unsafe links;
- regular-file check: distinguish a PDF file from directories and special objects;
- link/reparse inspection: reject unsafe redirection at root, every parent, final target, and source where relevant;
- bounded read-open: read only an existing regular target under an approved bounded resource policy;
- PDF signature and parse validation: establish format and parse evidence;
- SHA-256, size, and page-count calculation: compare exact artifact metadata.

No recursive directory scan, newest-file lookup, wildcard resolution, or unrelated-entry enumeration is justified.

## 9. Destination-request contract readiness

A bounded request should contain equivalents of:

`destination_inspection_contract_version`, `requested_action`, `fixture_id`, `report_id`, `report_version`, `expected_filename`, `expected_sha256`, `expected_file_size_bytes`, `expected_page_count`, `source_boundary_id`, `archive_root_id`, `archive_root_version`, `archive_policy_id`, `archive_boundary_id`, `destination_relative_id`, `request_id`, and `idempotency_key`.

`requested_action` must equal `inspect_internal_pdf_archive_destination`. The request must use the planner-derived logical identity and exact expected metadata. No absolute path may be caller supplied.

## 10. Prohibited inputs

Reject `source_path`, `destination_path`, `archive_root_path`, absolute paths, UNC paths, drive paths, arbitrary directories, arbitrary filenames, wildcard, glob, recursive, overwrite, force, create, mkdir, copy, move, rename, delete, cleanup, skip-validation controls, caller-selected archive roots, raw PDF bytes, and customer paths. Also reject path-like aliases, ADS syntax, drive-relative forms, arbitrary report content, and fields that purport to grant authority.

## 11. Archive-root capability readiness

The capability contract should require:

`capability_contract_version`, `archive_root_id`, `archive_root_version`, `archive_policy_id`, `archive_boundary_id`, `configured`, `enabled`, `absolute_validated`, `server_controlled`, `customer_isolated`, `source_isolated`, `link_safe`, `platform`, `filesystem_policy_id`, and `sanitization_policy_id`.

The producer additionally requires a hidden server-side absolute root path or equivalent secure handle to perform inspection. That value must never enter planner-facing destination evidence, response data, logs, or dashboard output. The planner sees bounded identity and booleans, not filesystem authority.

## 12. Archive-root configuration status

No concrete archive root is approved; no root configuration source is approved; no root versioning mechanism is implemented; no root capability producer exists; and no platform validation proof exists. This blocks real contract closure for root-produced evidence, adapter implementation, direct proof against a real root, endpoint integration, and mutation. It does not block the requested documentation-only contract-resolution slice.

## 13. Destination-relative identity readiness

The locked logical structure is exactly:

`fixture_id/report_id/report_version/expected_filename`

It requires exactly four non-empty components, no leading or trailing separator, no empty component, no `.` or `..`, no drive form, no UNC form, no ADS syntax, no absolute interpretation, a bounded total length, and exact equality with the planner-derived identity. The planner returns a logical identifier only. The server-side destination capability may combine it with an approved root; the resulting absolute path must never be returned. The logical identifier alone grants no filesystem authority.

## 14. Path construction readiness

The contract direction is sufficient but not complete. It must resolve server-side root selection, validate every component before joining, construct one root-plus-four-component target, check lexical containment, check canonical/resolved containment, reject root escape, reject nested source/archive boundary conflicts, and avoid current-working-directory dependence. Parent creation is prohibited. Missing or inaccessible parents must produce bounded inspection outcomes, never an inferred absence.

## 15. Windows path semantics

The contract must explicitly resolve case-insensitivity, reserved device names, trailing spaces, trailing periods, ADS, drive-relative paths, UNC, long paths, junctions, reparse points, hard links, normalization collisions, and file-identity aliasing. Separator, reserved-name, ADS, root-escape, and normalization rules can be contract decisions now. Reparse behavior, hard-link identity, long-path behavior, and filesystem aliasing require implementation-level Windows proof. Unsupported or ambiguous conditions must fail closed.

## 16. Cross-platform policy

V1 should be platform-gated and fail closed on unsupported platforms. The repository evidence is Windows-oriented and does not establish portability. No silent claim of Windows/Posix equivalence is justified. A later platform requires a separately reviewed contract version, platform-specific tests, and direct proof.

## 17. Root and component link/reparse controls

The adapter must inspect the archive root itself, every existing intermediate directory, the final destination, and the source target when comparison is required. Any symlink, junction, mount redirection, reparse point, unsupported special object, or unclassifiable component must fail closed. A lexical path check alone is insufficient.

## 18. Source/destination separation

Required evidence must establish distinct source and archive boundary IDs, distinct resolved source and destination targets, no same resolved file, no same filesystem identity where detectable, no hard-link alias where detectable, no root nesting conflict, and no case or normalization alias. Ambiguous resolution must not become `DESTINATION_ABSENT` or `IDENTICAL_ARCHIVE_PRESENT`.

## 19. Destination classifications

Destination inspection owns:

- `DESTINATION_ABSENT`
- `IDENTICAL_ARCHIVE_PRESENT`
- `CONFLICTING_ARCHIVE_PRESENT`
- `DESTINATION_NON_REGULAR`
- `DESTINATION_LINK_OR_REPARSE`
- `DESTINATION_DIRECTORY_COLLISION`
- `DESTINATION_OUTSIDE_APPROVED_ROOT`
- `SOURCE_DESTINATION_SAME`
- `IDENTITY_NORMALIZATION_COLLISION`

`IDEMPOTENCY_CONFLICT`, authorization conflict, audit-capability unavailability, concurrency conflict, and lifecycle-state conflict belong to their respective producers or the pure planner. The destination adapter may report relevant evidence, but must not decide those unrelated authorities.

## 20. Existing-file inspection

For an existing regular destination PDF, the adapter should verify deterministic filename, PDF signature, parse validity, SHA-256, file size, and page count. Fixture/report/version identity, classification, internal warning, and provenance may be derivable from bounded PDF content only where the document contract defines reliable evidence; otherwise they require separate metadata evidence. Missing required identity or governance metadata must fail closed rather than be inferred.

## 21. Identical-archive criteria

`IDENTICAL_ARCHIVE_PRESENT` requires a regular file with no link/reparse condition, containment inside the approved root, source/destination distinctness, expected filename, matching SHA-256, size, page count, valid signature and parse, and matching classification and warning where required evidence supports them. Root identity, archive policy, and accepted idempotency evidence must also match. If any required evidence cannot be established, do not classify the archive as identical.

## 22. Conflicting-archive criteria

`CONFLICTING_ARCHIVE_PRESENT` applies when the filename exists but hash, size, page count, identity, classification, warning, parse, signature, policy, or expected evidence conflicts. No overwrite, replacement, alternate destination, suffix, rename, or cleanup may be suggested or attempted.

## 23. Absent destination criteria

`DESTINATION_ABSENT` is valid only when the approved root is valid, the parent chain is valid and contained, no link/reparse condition exists, the final target does not exist, no directory collision exists, and inspection completed successfully. Missing root, inaccessible parent, parent outside the root, parent non-directory, access denied, platform error, and unsupported filesystem must not be classified as absent.

Parent-specific bounded outcomes are required for `parent_missing`, `parent_non_directory`, `parent_link_or_reparse`, `destination_access_denied`, and `destination_inspection_failed`, with a separate policy decision for whether these map to blocked or unavailable response status.

## 24. Normalized destination-evidence output

The output should contain equivalents of: contract version; inspection completion; fixture/report/version; expected filename, SHA-256, size, and page count; source and archive boundary IDs; root ID/version and policy; destination-relative ID; destination status and collision classification; existence; regular-file status; link/reparse status; containment; source/destination distinctness; identity, hash, size, page, classification, and warning matches; PDF signature and parse results; request and idempotency identity; bounded blocked reason; `action_performed=false`; and all safety flags.

No absolute root, destination, source, parent, temporary, customer, or unrelated directory path may be returned.

## 25. Response statuses

Bounded response statuses should be:

- `DESTINATION_INSPECTION_COMPLETE`
- `DESTINATION_INSPECTION_BLOCKED`
- `DESTINATION_INSPECTION_UNAVAILABLE`
- `DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM`

These are response statuses only, not lifecycle states, permissions, execution approvals, or persisted transitions.

## 26. Blocked-reason readiness

The contract can resolve a closed registry around: `invalid_destination_inspection_contract`, `unexpected_destination_inspection_fields`, `unsupported_contract_version`, `archive_root_missing`, `archive_root_disabled`, `archive_root_invalid`, `archive_root_identity_mismatch`, `archive_policy_mismatch`, `archive_boundary_mismatch`, `unsupported_platform`, `invalid_destination_relative_id`, `invalid_path_component`, `reserved_path_component`, `non_ascii_path_component`, `path_component_too_long`, `relative_identifier_too_long`, `destination_outside_approved_root`, `parent_missing`, `parent_non_directory`, `parent_link_or_reparse`, `destination_link_or_reparse`, `destination_non_regular`, `destination_directory_collision`, `source_destination_same`, `identity_normalization_collision`, `destination_access_denied`, `destination_inspection_failed`, `pdf_signature_validation_failed`, `pdf_parse_validation_failed`, `destination_identity_mismatch`, `sha256_mismatch`, `file_size_mismatch`, `page_count_mismatch`, `classification_evidence_missing`, `warning_evidence_missing`, and `inspection_not_authorized`.

Final reason membership and precedence remain contract-resolution work; no unsupported reason is treated as implemented.

## 27. Error handling

Expected filesystem states must return bounded responses without raw exception text, absolute paths, stack traces, directory listings, or sensitive object details. Access denied and unsupported platform must fail closed. Unexpected internal faults must remain distinguishable through a bounded generic failure class and safe correlation, without disclosing paths or exception text.

## 28. TOCTOU, freshness, and concurrency

The contract must assess races between root validation and destination check, parent validation and target check, `lstat` and read-open, metadata check and response, and inspection and later archive execution. Destination evidence is observational, may become stale immediately, does not lock or reserve a path, and cannot grant execution authority.

Evidence should include a capability-generated evaluated-at value, destination version or metadata token, root capability version, and metadata fingerprint where available. A short validity window and mandatory reinspection before mutation require separate policy and producer support. The pure planner needs no current-clock logic. Mutation requires separate final reinspection and concurrency controls.

## 29. Disclosure and safety requirements

Responses may expose only boundary IDs, root identity/version, archive policy ID, bounded destination-relative ID, status, bounded metadata, and blocked reason. They must not expose absolute root, destination, source, parent, temporary, customer, or unrelated directory paths.

Every response must preserve exactly false:

`customer_ready_possible`, `customer_release_authorized`, `queue_write_performed`, `pdf_generation_performed`, `learning_applied`, `calibration_applied`, `accuracy_ledger_written`, `gcid_written`, `model_weights_changed`, `fighter_ratings_changed`, `prediction_logic_changed`, `artifact_archived`, `artifact_removed`, `artifact_overwritten`, `permanent_mutation_performed`, and `action_performed`.

## 30. Threat findings

The contract must control caller-controlled root substitution, traversal, UNC and drive injection, ADS, root escape, symlink/junction/reparse redirection, hard-link aliasing, case and normalization collision, source/destination aliasing, special-file inspection, stale absence evidence, access-denied misclassification, parse bombs, large-file hashing, path disclosure, exception leakage, and treating evidence as execution authority.

The strongest current controls are server-derived deterministic identity, prohibited path fields, bounded planner output, read-only artifact inspection, link/reparse rejection in the existing inspection path, collision taxonomy, and false mutation flags. The missing controls are approved root identity, destination-specific platform behavior, parent classification, file-identity strategy, resource limits, freshness contract, and implementation proof.

## 31. Resource-boundary readiness

A future adapter must define or consume approved maximum file size and page count, bounded read behavior, hashing cost, parser timeout or process isolation where applicable, and failure behavior for resource exhaustion. It must perform no recursive scan, newest-file lookup, or repeated unrelated hashing. It must inspect one deterministic destination only. Existing planner bounds page count and input sizes, but destination inspection limits and parser isolation are not yet resolved.

## 32. Testing readiness

Focused future tests can cover absent destination, identical archive, conflict, non-regular target, directory collision, target and parent link/reparse, root escape, source/destination same, reserved component, separator injection, case collision, access denied, missing or disabled root, unsupported platform, invalid signature, parse failure, hash/size/page mismatch, path non-disclosure, false safety flags, and no filesystem mutation.

Safe tests would use pytest temporary directories, a synthetic or existing internal PDF fixture, platform-gated Windows reparse/junction tests, monkeypatched server capability providers, and no customer or production directory access. The current test and inspection adapter do not establish the future destination contract; no tests are run in this docs-only slice.

## 33. Concrete prerequisites

| Prerequisite | Required stage |
|---|---|
| Archive-root capability schema and ownership | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Concrete approved archive-root fixture | `REQUIRED_BEFORE_DIRECT_PROOF` |
| Root capability producer | `REQUIRED_BEFORE_ADAPTER_IMPLEMENTATION` |
| Destination-request schema | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Path-resolution and containment policy | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Windows reparse and junction strategy | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Source/destination file-identity strategy | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Existing-file metadata comparison policy | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Closed bounded-reason registry and precedence | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Resource limits and parser policy | `REQUIRED_BEFORE_ADAPTER_IMPLEMENTATION` |
| Synthetic/internal test fixture strategy | `REQUIRED_BEFORE_ADAPTER_IMPLEMENTATION` |
| Evidence freshness contract | `REQUIRED_BEFORE_CONTRACT_RESOLUTION` |
| Live evidence producers and route contract | `REQUIRED_BEFORE_ENDPOINT` |
| Final reinspection, lock, and copy policy | `REQUIRED_BEFORE_MUTATION` |

## 34. Readiness matrix

| Area | Status |
|---|---|
| Capability ownership | READY |
| Input contract | PARTIALLY_READY |
| Prohibited fields | READY |
| Root capability | PARTIALLY_READY |
| Root configuration | NOT_READY |
| Destination identity | READY |
| Path construction | PARTIALLY_READY |
| Containment | PARTIALLY_READY |
| Windows semantics | PARTIALLY_READY |
| Link/reparse handling | PARTIALLY_READY |
| Source/destination separation | PARTIALLY_READY |
| Classification ownership | READY |
| Existing-file inspection | PARTIALLY_READY |
| Identical/conflicting criteria | PARTIALLY_READY |
| Response schema | PARTIALLY_READY |
| Blocked reasons | PARTIALLY_READY |
| Error handling | READY for contract definition |
| Freshness | PARTIALLY_READY |
| Concurrency | NOT_READY for mutation; READY for boundary definition |
| Disclosure | READY |
| Resource controls | PARTIALLY_READY |
| Test feasibility | READY for future focused tests |

## 35. Contract-resolution blockers

The unresolved design items preventing a complete destination-inspection contract are: exact versioned request and response schemas; archive-root capability ownership and hidden-path handling; root versioning and platform policy; component and normalization policy; path and canonical containment semantics; Windows reparse, junction, mount, hard-link, long-path, and file-identity strategy; parent-state and access-denied classifications; source/destination separation evidence; existing-file metadata and classification provenance; bounded reason precedence; evidence freshness and version tokens; and resource limits/parser isolation.

## 36. Adapter-implementation blockers

A future two-file adapter remains blocked until the contract resolves the items above, an approved root capability producer can supply bounded evidence, platform behavior is testable, resource limits are fixed, and the focused test strategy can run without customer or production paths. No implementation is authorized by this assessment.

## 37. Endpoint, dashboard, and archive-mutation status

- Endpoint: `NOT_READY_FOR_ENDPOINT`
- Dashboard: `NOT_READY_FOR_DASHBOARD`
- Archive mutation: `NOT_READY_FOR_ARCHIVE_MUTATION`

No endpoint can be assessed until a destination-inspection adapter, evidence producers, route contract, focused route test, and live non-mutating proof exist. Dashboard exposure remains later. Mutation additionally requires approved root, authorization, audit, concurrency, finalization, recovery, and copy-and-retain controls.

## 38. Residual-risk verdict

- Docs-only contract work: `ACCEPTABLE`
- Read-only adapter implementation: `ACCEPTABLE_WITH_BLOCKERS`
- Destination-inspection direct proof: `ACCEPTABLE_WITH_BLOCKERS`
- Endpoint integration: `UNACCEPTABLE`
- Archive mutation: `UNACCEPTABLE`

## 39. Smallest safe next slice

The smallest safe next slice is exactly: **Button 2 governed internal PDF archive destination-inspection contract blocker resolution.**

Proposed file: `docs/button2_governed_internal_pdf_artifact_archive_destination_inspection_contract_blocker_resolution_v1.md`

Because contract ambiguity remains, do not recommend implementation directly.

## 40. Recommended sequencing

A. destination-inspection capability readiness assessment; B. destination-inspection contract blocker resolution; C. destination-inspection implementation-readiness reassessment; D. separately authorised read-only destination-inspection adapter; E. focused adapter tests; F. direct read-only proof; G. supporting evidence-producer readiness; H. archive-planning endpoint readiness; I. endpoint and focused route test; J. live route proof; K. dashboard planning-control readiness; L. dashboard control and proof; M. archive-mutation implementation-readiness assessment; N. separately authorised copy-and-retain archive implementation.

## 41. Explicit non-authorization

This assessment does not authorize destination-inspection implementation, archive-root configuration, root capability producer, endpoint, route, dashboard, authorization producer, audit producer, concurrency producer, directory creation, file creation, temporary-file creation, copy, archive, finalization, source removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit persistence, lifecycle persistence, customer-ready classification, customer release, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 42. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_CAPABILITY_READINESS=READY_FOR_DESTINATION_INSPECTION_CONTRACT_RESOLUTION`
