# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Windows Capability and File-Identity Contract Resolution v1

## 1. Executive status

`WINDOWS_CAPABILITY_FILE_IDENTITY_BLOCKERS_PARTIALLY_RESOLVED`

This document resolves the v1 design for private archive-root capabilities, Windows containment and object controls, file identity, alias detection, bounded filesystem errors, and focused-test authority. Resolution does not authorise implementation, Windows API invocation, capability production, filesystem inspection, endpoint exposure, or archive mutation.

## 2. Locked baseline

- Current metadata/resource contract is resolved from commit `8203d34`.
- Metadata/resource verdict: `METADATA_RESOURCE_BLOCKERS_RESOLVED`.
- Destination-inspection contract commit: `1e528befbce2a3b7722719ccc8865189c5ee4d03`.
- Destination-inspection readiness commit: `84d192a0bc7f69a6a214e91128ef6d8806010ea9`.
- The governed fixture is fictional only.
- Artifacts are internal/test-only.
- V1 is Windows-only.
- No concrete archive root is approved.
- No capability producer, destination-inspection implementation, endpoint, dashboard, or archive mutation exists.

## 3. Contract purpose

This document resolves only private archive-root capability representation, bounded root identity binding, target-capability ownership, Windows path and object inspection, reparse/junction policy, file-identity comparison, hard-link and alias detection, source/destination separation, Windows filesystem error mapping, Windows-specific test authority, and implementation/proof prerequisites.

## 4. Capability architecture

The authority separation is:

A. root configuration authority selects an approved server configuration;

B. the private capability producer validates that configuration and creates one immutable private capability;

C. the destination-inspection adapter consumes that capability and performs one bounded read-only inspection;

D. the pure archive planner receives normalized destination evidence only;

E. the future archive executor remains nonexistent and separately governed.

The planner never receives the private root target. The browser never supplies a root target. Responses expose only bounded root and boundary IDs. The private capability grants read-only destination-inspection authority only.

## 5. Private capability representation

V1 selects an immutable server-created private capability object rather than a browser-visible handle or planner-facing path. It contains:

```text
capability_contract_version
capability_id
archive_root_id
archive_root_version
archive_policy_id
archive_boundary_id
platform
filesystem_policy_id
sanitization_policy_id
private_approved_absolute_root_target
root_configuration_fingerprint
capability_source_id
capability_source_version
configured
enabled
server_controlled
customer_isolated
source_isolated
expiry_or_validity_evidence
action_performed
```

The absolute target exists only inside trusted server memory or protected server configuration. It is never serialized into HTTP, dashboard data, planner input, destination evidence, logs, exceptions, or responses. It is not accepted from caller input. `action_performed` is always false. The producer must not grant write, delete, rename, copy, or archive authority.

An opaque handle may be introduced later only through a separately reviewed contract. V1 uses the immutable private object because it gives a test-only fixture a bounded injection point while preserving the private boundary. This is a design decision, not an implementation authorization.

## 6. Capability version, bounds, and integrity

The exact capability version is `button2-governed-internal-pdf-archive-root-private-capability-v1`; unknown versions fail closed. The filesystem policy is `button2-governed-internal-pdf-archive-destination-windows-filesystem-policy-v1`; unknown policies fail closed.

All capability identifiers are non-empty ASCII strings with no NUL, controls, separators, or edge whitespace. Exact maximum lengths are: capability ID 128; capability source ID 96; capability source version 64; root ID 96; root version 96; policy ID 96; archive boundary ID 96; filesystem policy ID 96; sanitization policy ID 96; configuration fingerprint 128; expiry/validity evidence 128. Existing planner limits remain authoritative for shared IDs.

Capability integrity must structurally bind the capability version, root ID/version, policy, boundary, platform, filesystem and sanitization policies, private target, configuration fingerprint, producer ID/version, enabled/configured flags, and validity evidence. The production signing or MAC mechanism remains an implementation decision and is not selected here.

## 7. Private-target restrictions

The private target must be absolute, drive-qualified under approved Windows semantics, stable for the capability version, and independent of the current working directory. It must not be drive-relative, UNC, device-namespace, ADS, environment-variable-derived, caller-supplied, customer-bound, or silently normalized into a different root identity. V1 does not approve UNC roots. The private target is inaccessible to planner-facing serialization.

## 8. Platform and root policy

V1 requires `platform=windows`. Linux, macOS, unknown platforms, compatibility-layer ambiguity, and unsupported Windows filesystem semantics fail with status `DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM` and reason `unsupported_platform`.

Before inspection, the private root passes absolute-path, drive, no-relative-segment, no-ADS, no-device-namespace, no-environment-variable, no-current-working-directory, boundary-isolation, and identity-stability checks. The root must exist, be a directory, not be a regular file, symlink, junction, mount redirection, unsupported reparse object, or special object, and match the capability configuration fingerprint and identity evidence where supported. No concrete root is approved by this document.

## 9. Reparse, junction, mount, and parent controls

V1 is fail-closed and denies every reparse tag by default. The adapter must inspect Windows file attributes and reparse metadata for the root, fixture directory, report directory, report-version directory, final target, and source where comparison is required. Symbolic links, junctions, mount points, name-surrogate reparse points, cloud placeholders requiring hydration or redirection, unsupported tags, and unclassifiable redirection are blocked. No reparse target is silently followed.

Each existing parent must be the expected directory type, have sufficient access for bounded read-only inspection, remain within the approved resolved root, and have no alias or reparse condition. A missing parent maps to status `DESTINATION_INSPECTION_UNAVAILABLE`, reason `parent_missing`, `inspection_completed=false`, and `action_performed=false`; it is never `DESTINATION_ABSENT`. A non-directory parent maps to `parent_non_directory`. Any parent link, junction, mount, or unsupported reparse maps to `parent_link_or_reparse`. No parent is created.

## 10. Final-target object policy

Use lstat-equivalent inspection before following or opening a target. Classify only: absent after valid parent inspection, regular file, directory collision, link/reparse, non-regular special object, access failure, or unexpected inspection failure. A final link/reparse is blocked as `destination_link_or_reparse`; a directory is `DESTINATION_DIRECTORY_COLLISION`; another special object is `destination_non_regular`. A target is absent only after the root and complete parent chain have passed validation.

## 11. Windows file-identity strategy

V1 requires stable identity from read-only Windows file handles: volume identity plus file identifier obtained through a documented Windows file-information API or equivalent. Path text, size, timestamps, or hash alone are insufficient. Handles must not request write or delete authority and must not expose raw handle values.

The private identity evidence has this exact version: `button2-governed-internal-pdf-windows-file-identity-v1`. Its bounded schema is:

```text
identity_contract_version
volume_identifier
file_identifier
object_type
link_count_where_available
identity_completed
identity_supported
identity_version_token
blocked_reason
action_performed
```

Raw volume serials, file IDs, handles, and absolute paths remain private unless a separately reviewed response requires otherwise. The normalized response exposes booleans and opaque identity-version tokens.

## 12. Source/destination and alias handling

A trusted source-identity producer or source inspection supplies normalized identity evidence bound to source boundary, fixture, report, version, filename, SHA-256, size, and page count. The destination inspector derives destination identity from its own read-only opened target. Caller-provided source or destination paths and identity claims are never authoritative.

If volume and file identifiers match with complete supported evidence, classify `SOURCE_DESTINATION_SAME` with reason `source_destination_same`. A hard link has the same stable identity and therefore receives the same classification; it is not an identical archive and does not establish source isolation. If stable identity cannot be obtained, return `DESTINATION_INSPECTION_UNAVAILABLE` with `source_destination_identity_unavailable`; never infer distinctness from path text.

Different volume identifiers prove only that the file objects differ. Containment, boundary separation, and root validation remain mandatory. The archive root may not be inside the source boundary, the source boundary may not be inside the archive root, and equal or conflicting root identities map to `source_boundary_root_nesting_conflict` or the exact existing `archive_boundary_mismatch` reason.

## 13. Case, normalization, short-name, and containment policy

Windows logical components are compared case-insensitively for collision detection while preserving the validated original spelling. A case-only alternate existing identity maps to `IDENTITY_NORMALIZATION_COLLISION`; no alternate spelling is selected. V1 accepts ASCII-only components, performs no Unicode normalization, and rejects trailing spaces, trailing periods, reserved names, ADS syntax, separators, and traversal forms before target derivation.

Textual path inequality is never proof of distinctness. Short-name aliases are not enumerated and cannot establish identity; canonical-resolution ambiguity fails closed. Containment requires validated root-relative four-component construction plus resolved root/target relationship after reparse checks. Prefix comparison alone is insufficient. No wildcard, sibling search, or alternate path is allowed.

## 14. Filesystem error taxonomy and mapping

The closed internal error classes are: file-not-found, path-not-found, access-denied, sharing-violation, invalid-name, path-too-long, unsupported-filesystem, invalid-handle, device-not-ready, I/O-error, reparse-resolution-failure, identity-query-unsupported, and unexpected-OS-error.

Parent mappings are deterministic: path/file not found -> `parent_missing`; access denied -> `parent_access_denied`; non-directory -> `parent_non_directory`; reparse or redirection -> `parent_link_or_reparse`; unsupported object/filesystem -> `parent_inspection_failed`; all other parent OS errors -> `parent_inspection_failed`.

Final-target mappings are: not found after valid parent inspection -> `DESTINATION_ABSENT`; access denied -> `destination_access_denied`; sharing violation preventing required inspection -> `destination_inspection_failed`; invalid or overlong identity -> the owning component reason; unsupported filesystem -> `destination_inspection_failed`; unexpected OS error -> `destination_inspection_failed`.

Raw Windows text, numeric diagnostics, paths, device paths, handles, stack traces, and directory listings are never returned. Only closed bounded reasons may cross the response boundary.

## 15. Open handles, freshness, and TOCTOU

Future read-only handles may obtain object type, reparse attributes, stable identity, size, bounded content, and later authorized parser input. They may not request write, delete, truncate, create, append, rename, replace, or mutation authority.

Capability freshness requires capability source version, root configuration fingerprint, root identity version token, trusted producer-issued/evaluated validity evidence, and request binding where appropriate. Stale or mismatched capability evidence fails closed. Identity is observational: the object may change after handle release, no reservation occurs, and no execution authority is created. Any future mutation must reopen and revalidate the root, parent chain, reparse state, target identity, and collision immediately before finalization.

## 16. Blocked reasons and response evidence

Capability-specific additions are `invalid_private_root_capability`, `unsupported_private_root_capability_version`, `private_root_capability_stale`, `private_root_target_invalid`, `private_root_target_disclosure_attempt`, `root_configuration_fingerprint_mismatch`, `root_identity_unavailable`, `root_identity_mismatch`, and `source_boundary_root_nesting_conflict`.

Identity-specific additions are `unsupported_file_identity_contract`, `source_file_identity_missing`, `source_file_identity_invalid`, `destination_file_identity_unavailable`, `source_destination_identity_unavailable`, `source_destination_same`, `hard_link_alias_detected`, and `identity_normalization_collision`. `hard_link_alias_detected` may be retained as diagnostic evidence, but the canonical classification is `SOURCE_DESTINATION_SAME`.

Normalized evidence may add root capability version, bounded configuration-fingerprint ID or digest, root identity completion/version, source and destination identity completion, source/destination same, identity supported, hard-link alias detected, reparse state, and parent-chain completion. Raw IDs and paths remain private; all safety flags and `action_performed` remain false.

## 17. Test authority categories

Future tests are classified as:

A. `STANDARD_UNPRIVILEGED` for temporary-directory behavior, normal roots and parents, absent targets, regular targets, directory collisions, non-directory/missing parents, case-collision logic over normalized evidence, narrow error-mapping mocks, path non-disclosure, safety flags, and no mutation.

B. `WINDOWS_PLATFORM_GATED` for stable identity retrieval, same-file comparison, permitted temporary-scope hard links, reserved names, trailing-dot/space behavior, path length, and reproducible sharing violations.

C. `PRIVILEGED_OR_SEPARATELY_AUTHORIZED` for junctions, mount points, special reparse objects, device namespaces, privileged symlinks, and cloud-placeholder behavior unless the environment separately proves safe support.

D. `MOCK_ONLY_UNTIL_AUTHORIZED` for unsupported tags, junctions, mount redirection, cloud redirection, and reparse-query failures. Mocks prove mapping and fail-closed logic, not kernel/filesystem behavior.

A future test-only capability may point only to a pytest-owned temporary directory, be created inside the focused test, never be stored in the governed fixture JSON, never use an environment-selected root, and expire with the test. Hard links are permitted only inside that temporary scope when Windows supports them without elevated authority; otherwise they are platform-gated or mocked.

## 18. Reparse proof limitation

Mocked reparse tests do not prove Windows kernel behavior. Implementation readiness may proceed only with this explicit platform-proof dependency. Real junction, mount, device, cloud-placeholder, and privileged symbolic-link proof requires separate authority. Endpoint and mutation remain blocked until required real platform proof exists.

## 19. Static-authority requirements

Future source/AST checks must prohibit write-mode opens, mkdir/makedirs/touch/create, temporary-file creation, copy, move, rename, replace, delete, unlink, rmdir, shell or PowerShell invocation, unrestricted scans, environment-selected roots, and browser-provided paths. They must prove the main adapter is read-only and that any parser worker has only its separately bounded authority.

## 20. Blockers resolved

This contract resolves the private capability representation, root identity binding, target restrictions, Windows gate, root/object validation, default-deny reparse policy, parent controls, file-identity schema and strategy, source/destination comparison, hard-link policy, case and normalization aliases, short-name handling, root nesting, filesystem taxonomy, parent and target mappings, bounded response evidence, and test-authority categories.

## 21. Remaining blockers and implementation dependencies

Remaining blockers are the production capability-integrity mechanism, production trusted-metadata integrity mechanism, exact Windows API/library implementation choice, enforceable parser-worker and memory isolation, real privileged reparse proof, and source-identity producer implementation. These are respectively implementation choices, implementation dependencies, or proof requirements rather than unresolved policy.

Dependencies before implementation reassessment are an approved test-only private capability fixture, source file-identity evidence fixture, trusted metadata fixture, adapter design, parser boundary, focused tests, direct read-only proof, and Windows platform proof where required. No concrete archive root is approved.

## 22. Contract effect and status

`WINDOWS_CAPABILITY_CONTRACT_READY_WITH_BLOCKERS`

This is design-only and does not authorise implementation. Endpoint status: `NOT_READY_FOR_ENDPOINT`. Dashboard status: `NOT_READY_FOR_DASHBOARD`. Archive-mutation status: `NOT_READY_FOR_ARCHIVE_MUTATION`.

## 23. Smallest safe next slice

Recommend exactly: **Button 2 governed internal PDF archive destination-inspection implementation-readiness reassessment**.

Proposed file: `docs/button2_governed_internal_pdf_artifact_archive_destination_inspection_implementation_readiness_reassessment_v1.md`

## 24. Recommended sequencing

A. Windows capability/file-identity contract resolution; B. destination-inspection implementation-readiness reassessment; C. separately authorised read-only destination-inspection adapter and focused tests; D. direct read-only proof; E. private capability-producer readiness; F. source-identity and trusted-metadata producer readiness; G. archive-planning endpoint readiness; H. endpoint and focused route test; I. live route proof; J. dashboard planning-control readiness; K. dashboard implementation and proof; L. archive-mutation readiness; M. separately authorised copy-and-retain archive implementation.

## 25. Explicit non-authorization

This contract does not authorise a private capability producer, root configuration, source-identity producer, metadata producer, Windows API implementation, reparse or junction creation, hard-link creation outside a separately authorised test, parser worker, destination-inspection implementation, endpoint, route, dashboard, directory or file creation, temporary files, PDF generation, copy, archive, finalization, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit or lifecycle persistence, customer-ready classification, customer release, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 26. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_WINDOWS_CAPABILITY_FILE_IDENTITY_BLOCKERS=WINDOWS_CAPABILITY_FILE_IDENTITY_BLOCKERS_PARTIALLY_RESOLVED`
