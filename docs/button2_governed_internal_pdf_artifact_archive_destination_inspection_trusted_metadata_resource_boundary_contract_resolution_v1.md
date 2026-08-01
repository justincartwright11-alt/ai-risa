# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Trusted Metadata and Resource Boundary Contract Resolution v1

## 1. Executive status

`METADATA_RESOURCE_BLOCKERS_RESOLVED`

This document resolves the trusted destination-metadata evidence schema and the v1 resource/parser boundary. Resolution does not authorise implementation, metadata production, parser execution, endpoint exposure, dashboard exposure, archive planning integration, or archive mutation.

## 2. Locked baseline

- Current destination-inspection contract commit: `1e528befbce2a3b7722719ccc8865189c5ee4d03`.
- Current contract verdict: `DESTINATION_INSPECTION_CONTRACT_BLOCKERS_PARTIALLY_RESOLVED`.
- Readiness-assessment commit: `84d192a0bc7f69a6a214e91128ef6d8806010ea9`.
- Pure planner commit: `b14ce73eef63c61c688a8110d55c01d8a205029f`.
- The governed fixture is fictional only.
- Referenced artifacts are internal/test-only.
- No destination-inspection implementation, metadata producer, parser worker, approved archive root, or archive mutation exists.

## 3. Contract purpose

This slice resolves only trusted destination-metadata evidence, its provenance and integrity, identity and request binding, identical/conflicting decisions, file and page limits, bounded hashing, parser scope, parser timeout and isolation, and resource-limit response handling. It does not implement a producer, parser, inspector, endpoint, route, dashboard control, archive root, or archive action.

## 4. Trusted-metadata ownership

A. The trusted metadata producer is server-controlled and internal/test-only. It creates normalized metadata evidence and has no archive execution authority.

B. The destination-inspection adapter validates and consumes that evidence. It does not manufacture missing metadata, persist metadata, or modify metadata.

C. The pure planner receives only normalized destination evidence and never consumes raw trusted metadata.

D. The archive executor remains nonexistent and separately governed.

## 5. Metadata source policy

The only approved v1 producer classes are `governed_internal_fixture_metadata`, `server_controlled_immutable_sidecar_metadata`, and `previously_verified_archive_metadata_record`. Browser-provided metadata, caller-authored classifications or warnings, arbitrary PDF text extraction, filename-only inference, directory-name inference, user-supplied provenance, and customer-output metadata are prohibited. Unknown producer classes fail closed.

The exact metadata contract version is `button2-governed-internal-pdf-archive-destination-trusted-metadata-v1`; unknown or missing versions fail closed.

## 6. Trusted metadata envelope

The required envelope has exactly these fields:

```text
contract_version
evidence_completed
metadata_source_type
metadata_source_id
metadata_source_version
metadata_integrity_token
fixture_id
report_id
report_version
filename
sha256
file_size_bytes
page_count
classification
internal_warning
provenance_source_type
provenance_source_id
provenance_verified
provenance_fixture_bound
archive_root_id
archive_root_version
archive_policy_id
archive_boundary_id
destination_relative_id
destination_evidence_version_token
evaluated_at
request_id
idempotency_key
action_performed
```

No absolute path is permitted. Optional fields are limited to `producer_correlation_id`, `source_artifact_version_token`, and `metadata_schema_id`. Unknown fields are rejected.

## 7. Field types and bounds

All identifiers are non-empty ASCII strings with no NUL, controls, or edge whitespace. The exact limits are: fixture ID 64 characters; report ID 96; report version 32; filename 160; destination-relative ID 512; metadata source ID 96; metadata source version 64; integrity token 256; provenance source ID 96; request ID 128; idempotency key 128; producer correlation ID 128; schema ID 96; destination evidence version token 128; archive root ID/version, policy ID, and boundary ID 96; classification 96; internal warning 256; source type 64; and evaluated-at 64. `sha256` is exactly 64 lowercase hexadecimal characters. `file_size_bytes` is an actual non-negative integer from 0 through `2^63 - 1`; `page_count` is an actual positive integer no greater than 10,000. Booleans are not accepted as integers. Timestamp syntax must be canonical and bounded; the consumer never trusts browser time.

`filename` is the inspected basename and must match the deterministic request filename. `destination_relative_id` is the exact four-component logical identity, not a filesystem path.

## 8. Metadata-integrity token

The token is opaque, server-produced, bounded, non-path data, deterministic or securely issued, and bound to the full normalized metadata envelope and its contract version. It cannot grant filesystem authority and cannot be browser-generated. The implementation must reassess the choice of signing or MAC mechanism before implementation; this contract does not prescribe a cryptographic construction. Invalid, missing, malformed, or mismatched tokens fail closed.

## 9. Identity and request binding

Trusted metadata must exactly match the destination-inspection request, approved archive-root capability identity and version, source-artifact evidence, derived destination-relative identifier, inspected filename, calculated SHA-256, calculated size, calculated page count, requested action, fixture ID, report ID, report version, archive policy, archive boundary, request ID, and idempotency key. It must also bind the source artifact version token where that optional evidence is available. A mismatch is never repaired by normalization or inference.

## 10. Classification, warning, and provenance

The required classification for the current fictional fixture is exactly `governed_internal_test_pdf`. Customer-ready, production, arbitrary user text, and PDF-body-inferred classifications are rejected. The required warning is exactly `INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE`; missing, shortened, rewritten, or caller-authored warnings are not equivalent.

Provenance must use a server-controlled source type and bounded source ID, with `provenance_verified=true`, `provenance_fixture_bound=true`, and exact fixture/report/version association. Provenance evidence does not grant archive execution authority.

## 11. Missing, invalid, and stale metadata

Missing metadata on an existing destination does not prove identity, does not infer classification or warning, does not overwrite, and does not select an alternate destination. The response is `DESTINATION_INSPECTION_BLOCKED`; the observed regular-file state is preserved, with `classification_evidence_missing` or `warning_evidence_missing` as applicable. `CONFLICTING_ARCHIVE_PRESENT` is reserved for a concrete disagreement, not unknown evidence.

Unsupported version, unknown field, malformed field, identity, hash, size, page-count, classification, warning, provenance, fixture-binding, root, destination-relative, request, idempotency, integrity-token, or `action_performed=true` failures map to `DESTINATION_INSPECTION_BLOCKED` with the corresponding closed reason. No raw metadata or producer exception text is returned.

Freshness requires matching `evaluated_at`, metadata source version, destination evidence version token, optional source artifact version token, root capability version, request ID, and idempotency key. Freshness is established by trusted server evidence, never browser time. Missing or expired required evidence maps to `trusted_metadata_stale`.

## 12. Identical and conflicting archive decisions

`IDENTICAL_ARCHIVE_PRESENT` is permitted only when all of the following hold: one contained regular destination PDF; no link or reparse; source and destination distinct; valid PDF signature and parse; matching SHA-256, size, page count, and filename; complete trusted metadata; matching classification and warning; valid provenance and fixture binding; valid request and idempotency binding; and valid metadata integrity.

`CONFLICTING_ARCHIVE_PRESENT` applies to a concrete disagreement in filename, hash, size, page count, signature, parse result, identity, classification, warning, provenance, fixture binding, archive-root binding, or destination-relative identity. No overwrite, deletion, alternate name, suffix, rename, or cleanup is recommended or attempted.

## 13. Normalized response and blocked reasons

Normalized destination evidence may return only: identity match, classification match, warning match, provenance validity, trusted-metadata completeness, metadata source type, metadata source version, and destination evidence version token, alongside the already locked bounded destination fields. It must not return raw sidecar contents, integrity secrets, private signing data, absolute paths, or arbitrary producer errors.

The closed additions are `trusted_metadata_missing` only when the contract needs a general missing marker, `trusted_metadata_invalid`, `trusted_metadata_stale`, `trusted_metadata_identity_mismatch`, `trusted_metadata_integrity_invalid`, `trusted_metadata_request_mismatch`, `trusted_metadata_idempotency_mismatch`, `provenance_evidence_missing`, `provenance_invalid`, and `provenance_fixture_binding_failed`. Existing classification and warning reasons are not duplicated. All blocked responses have `inspection_completed=false` when validation cannot complete, `action_performed=false`, all safety flags false, and no path disclosure.

## 14. Resource-policy decision

The exact resource-policy version is `button2-governed-internal-pdf-archive-destination-resource-policy-v1`; unknown versions fail closed. The v1 maximum file size is exactly `104857600` bytes (100 MiB). Files larger than this are rejected before full hashing or parsing as `resource_limit_exceeded`. The maximum page count is exactly 10,000; a higher count fails closed as `resource_limit_exceeded`.

Hashing is limited to one destination file, uses full SHA-256 only at or below the file limit, reads bounded chunks of exactly `1048576` bytes, never loads the complete file into memory, never recursively hashes, and never hashes unrelated files. Hashing stops if observed bytes exceed the limit. The initial PDF signature read is bounded to 1024 bytes and does not replace full parse validation.

## 15. Parser scope and isolation

The parser may perform only safe document opening, structural validation, page counting, and explicitly supported bounded metadata validation. It must not render, execute JavaScript or embedded actions, extract attachments or images, load external resources, access the network, install fonts, invoke a shell, or perform arbitrary decompression or export.

PDF parsing is required to run in a separately bounded worker process with a hard timeout of exactly 10 seconds. The worker has no network or filesystem write authority, receives one approved read-only target capability, and returns only bounded parse status and page count. This architecture is design-only and is not authorised here. A parser timeout maps to `resource_limit_exceeded`; malformed input maps to `pdf_parse_validation_failed`; a crash maps to a bounded failed/unavailable result without exception text; an external-resource request is blocked and not fulfilled.

The design memory ceiling is exactly `268435456` bytes (256 MiB). If the future environment cannot enforce it, parser implementation remains blocked. The inspector must not claim enforced isolation without direct proof.

Encrypted or password-protected PDFs are unsupported in v1: no prompt and no decryption attempt. They fail closed as `pdf_parse_validation_failed`. Embedded files, attachment traversal, multimedia, forms execution, JavaScript, external URI fetches, and rendering are prohibited and are not required for equality classification.

## 16. Single-target and directory boundary

Inspection is limited to one archive-root capability, one destination-relative identifier, one final destination, and the approved root, four deterministic components, required parent objects, and final target. There is no wildcard, glob, recursive scan, newest-file search, or alternate-path selection. Sibling enumeration is prohibited except minimum object checks for the deterministic target. No arbitrary directory contents are disclosed.

## 17. Resource responses and observability

Resource failures return `DESTINATION_INSPECTION_BLOCKED` or `DESTINATION_INSPECTION_UNAVAILABLE` according to the existing error model, with `resource_limit_exceeded`, `inspection_completed=false` where incomplete, `action_performed=false`, and every safety flag false. Bounded observability may include `resource_policy_id`, file-size and page limits, parser timeout, `parser_isolation_required`, signature and parse results, observed size and page count, and `resource_limit_exceeded`. It must exclude process IDs, command lines, paths, stack traces, parser internals, raw metadata, and secrets.

## 18. Validation order and TOCTOU

The first-failure validation order is:

1. request and source identity;
2. root and platform;
3. destination identity and containment;
4. object and source/destination checks;
5. file-size precheck;
6. bounded signature read;
7. bounded isolated parse;
8. page-count limit;
9. chunked SHA-256;
10. trusted metadata validation;
11. destination classification;
12. freshness;
13. safety flags;
14. deterministic response.

Metadata and resource validation are observational. No path reservation occurs, and the target may change immediately afterward. Trusted metadata may become stale. Any future mutation must revalidate the current file, metadata, root, parent chain, and target identity immediately before finalization. Identical classification grants no execution authority.

## 19. Focused future tests

Metadata tests must cover complete valid evidence, missing metadata, unsupported version, unknown field, malformed integrity token, identity/hash/size/page mismatch, classification and warning mismatch, missing or invalid provenance, false fixture binding, root and destination-relative mismatch, request and idempotency mismatch, stale evidence, `action_performed=true`, and absence of raw metadata disclosure.

Resource tests must cover below, exactly at, and one byte over the 100 MiB limit; exactly 10,000 and over-limit pages; bounded 1 MiB chunks; parser success, timeout, malformed input, encrypted PDF, attachment, external-resource attempt, memory-limit proof or explicit blocker, no rendering, network, write, and one-target behavior; and all-false safety flags.

## 20. Static-authority requirements

Future source/AST tests must prove no write-mode open, `mkdir`, file or temporary-file creation, copy, move, rename, replace, deletion, shell invocation from the main adapter, network library, environment-driven path selection, or unrestricted directory scan. They must prove exactly bounded parser-worker authority and no mutation or persistence. These are proof requirements, not implementation evidence.

## 21. Producer and parser status

No trusted metadata producer, sidecar schema file, integrity implementation, persistence store, parser worker, timeout mechanism, subprocess implementation, or memory-isolation proof exists. A separate readiness assessment is required before implementation choices or proof claims.

## 22. Blockers resolved

This document resolves the metadata envelope, producer ownership and classes, identity/request binding, classification/warning ownership, provenance, missing/invalid/stale behavior, identical/conflicting criteria, exact file/page/hash/signature limits, parser scope, timeout/isolation policy, memory ceiling, encryption and embedded-content policy, single-target boundary, resource response mapping, observability, validation order, TOCTOU effect, and focused metadata/resource test contract.

## 23. Remaining blockers

The following remain open: private root capability-handle representation; concrete metadata-integrity mechanism; Windows file-identity API selection; enforceable parser-worker architecture and memory isolation; reparse/junction test authority; and deterministic parent filesystem-error mapping. These are distinguished as policy resolved, implementation choice pending, implementation dependency, or direct-proof requirement. No approved archive root exists.

## 24. Contract effect and status

`METADATA_RESOURCE_CONTRACT_READY_WITH_BLOCKERS`

Resolution is policy only and does not authorise implementation. Endpoint status: `NOT_READY_FOR_ENDPOINT`. Dashboard status: `NOT_READY_FOR_DASHBOARD`. Archive-mutation status: `NOT_READY_FOR_ARCHIVE_MUTATION`.

## 25. Smallest safe next slice

The next slice is exactly **Button 2 governed internal PDF destination-inspection Windows capability and file-identity contract resolution**.

Proposed file: `docs/button2_governed_internal_pdf_artifact_archive_destination_inspection_windows_capability_file_identity_contract_resolution_v1.md`

## 26. Recommended sequencing

A. metadata/resource contract resolution; B. Windows capability and file-identity contract resolution; C. destination-inspection implementation-readiness reassessment; D. separately authorised read-only destination-inspection adapter and parser boundary; E. focused tests; F. direct read-only proof; G. capability-producer readiness; H. archive-planning endpoint readiness; I. endpoint and route test; J. live route proof; K. dashboard planning-control readiness; L. dashboard implementation and proof; M. archive-mutation readiness; N. separately authorised copy-and-retain archive implementation.

## 27. Explicit non-authorization

This contract authorises none of the following: trusted metadata producer, sidecar creation, metadata persistence, integrity signing, parser worker, process creation, destination-inspection implementation, root configuration, capability producer, fixture creation, endpoint, route, dashboard, directory or file creation, temporary files, PDF generation, copy, archive, finalization, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit or lifecycle persistence, customer-ready classification, customer release, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 28. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_METADATA_RESOURCE_BLOCKERS=METADATA_RESOURCE_BLOCKERS_RESOLVED`
