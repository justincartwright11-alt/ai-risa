# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Injected Parser-Result Contract Resolution v1

## 1. Executive status

`INJECTED_PARSER_RESULT_CONTRACT_RESOLVED`

The parser-result boundary, ownership, placement, schemas, binding, validation order, and test authority are resolved. No implementation is authorized by this document.

## 2. Locked baseline

- Implementation-readiness commit: `dede3e43eddb9ca494c81197c045b5f2dd43ef74`.
- Readiness verdict: `READY_WITH_IMPLEMENTATION_BLOCKERS`.
- Windows capability contract: `026a250d8973277fed6ef5e60f4e09d82e944bf3`.
- Metadata/resource contract: `8203d34beee22508586e17d620a9d08a12d8ff2f`.
- Destination-inspection contract: `1e528befbce2a3b7722719ccc8865189c5ee4d03`.
- No adapter, focused test, parser worker, parser-result producer, production archive root, endpoint, dashboard, or mutation exists.

## 3. Contract purpose

This contract resolves only the parser-result boundary required by the destination-inspection adapter. It defines ownership, placement, production, invocation, versions, schemas, statuses, reasons, destination identity, freshness, resource results, validation order, response mapping, test abstraction, and implementation effect.

The parser result is evidence, not authority. It cannot select a target, classify a customer artifact, write a file, or authorize archive mutation.

## 4. Architectural options considered

| Option | Decision and security assessment |
|---|---|
| A. Evidence nested in `destination_request` | Rejected. It is caller-shaped and therefore caller-controllable, is supplied before target identification, weakens the trust boundary, and is not destination-specific evidence. It preserves three arguments but makes deterministic tests prove an unsafe input path. |
| B. Evidence nested in `source_artifact_evidence` | Rejected. Parser evidence concerns the destination, not the source. It creates cross-object confusion and permits stale evidence to travel with the source. It preserves three arguments but violates ownership. |
| C. Provider/capability nested in `archive_root_capability` | Rejected as the final ownership model. A root-only capability must not silently own parsing; it mixes authorities even if a private callable is server controlled. A bounded composite capability is required instead. |
| D. Module-global dependency | Rejected. It creates mutable global state, hidden authority, test order dependence, and process-wide configuration. |
| E. Fourth public argument | Rejected for this version. It changes the locked API, exposes dependency placement to callers, and requires a formal API revision. |
| F. Direct parser execution inside adapter | Rejected. It is unisolated, complicates timeout/memory proof, may import unsafe parser behavior, and makes the read-only adapter a parser worker. |
| G. Private composite inspection capability | Selected. Trusted server code constructs it; it combines root, identity, reparse, and parser sub-capabilities without browser serialization, preserves three public arguments, and permits bounded deterministic fakes. It requires no third implementation file for the core slice. |

## 5. Required architecture decision

Select option G: redefine the first argument conceptually as a private destination-inspection capability, while retaining the public function shape. The browser supplies none of its private fields. The capability is destination-specific only after the adapter derives and validates the target; the parser cannot receive a path from request data or choose another path.

The adapter receives a bounded parser request and invokes one private capability operation. It does not receive precomputed browser evidence and does not execute PDF parsing itself.

## 6. Three-argument API decision

`THREE_ARGUMENT_API_PRESERVED`

The public API remains:

```text
inspect_button2_governed_internal_pdf_archive_destination_v1(
    archive_root_capability,
    source_artifact_evidence,
    destination_request,
)
```

The first argument is contractually a private composite inspection capability, not merely a root dictionary. The public argument name remains for compatibility; its private capability contract is checked before inspection. No fourth argument and no public parser function are introduced.

## 7. Capability ownership and composite contract

The selected private contract version is:

`button2-governed-internal-pdf-archive-destination-private-inspection-capability-v1`

It contains no planner-facing private fields and is never serialized. Its required sub-capabilities are:

| Sub-capability | Exact version | Ownership |
|---|---|---|
| archive-root capability | `button2-governed-internal-pdf-archive-root-private-capability-v1` | approved server root producer |
| filesystem-object inspection capability | `button2-governed-internal-pdf-archive-destination-filesystem-object-inspection-capability-v1` | server Windows inspection producer |
| file-identity capability | `button2-governed-internal-pdf-windows-file-identity-v1` | server identity producer |
| parser-result capability | `button2-governed-internal-pdf-archive-destination-parser-result-capability-v1` | server parser-capability producer |

Each sub-capability requires `capability_contract_version`, `source_id`, `source_version`, `enabled`, `supported`, `action_performed=false`, and no release or mutation authority. The composite additionally requires a bounded capability ID, capability source/version, root identity/version, archive policy, boundary, platform, filesystem and sanitization policy IDs, validity evidence, `server_controlled=true`, and all safety flags false. Unknown fields and versions fail closed.

This corrects the ownership problem in the conservative root-plus-parser model: root ownership remains root-only inside the composite, while parser ownership remains with its own producer. A callable, if used internally, is a field of the parser sub-capability and never a field of request data.

## 8. Parser capability behavior

The private capability exposes exactly one bounded operation:

```text
inspect_validated_pdf_target(
    private_validated_target,
    parser_request,
)
```

It consumes only a target already validated by the adapter. It cannot select a path, receive an absolute path in the public request, write, network, render, execute active content, return an exception, or disclose process/command details. It returns one bounded parser-result dictionary. This operation is internal and is not a new public adapter function.

A callable must be trusted-internal, non-serializable, supplied only during trusted construction, never returned, and enclosed by a valid capability. There is no callback registry, dynamic import, string resolution, `eval`, plugin discovery, or environment lookup.

## 9. Parser request contract

Exact version: `button2-governed-internal-pdf-archive-destination-parser-request-v1`.

The request has exactly these required fields and no unknown fields:

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
destination_relative_id
destination_identity_version_token
resource_policy_id
maximum_file_size_bytes
maximum_page_count
parser_timeout_seconds
parser_memory_limit_bytes
request_id
idempotency_key
```

`requested_action` must equal `inspect_validated_internal_pdf_destination`. The request contains no absolute path, source path, target path, bytes, callable, root handle, process identifier, or authority claim. The validated target crosses only the private capability boundary.

The resource values must exactly be `104857600`, `10000`, `10`, and `268435456` for file size, page count, timeout, and memory ceiling. The request must also bind signature-read limit `1024`, hash chunk size `1048576`, and the exact resource-policy version `button2-governed-internal-pdf-archive-destination-resource-policy-v1` through `resource_policy_id` and capability policy validation.

## 10. Parser-result contract

Exact version: `button2-governed-internal-pdf-archive-destination-parser-result-v1`.

The required schema is exactly:

```text
contract_version
ok
status
inspection_completed
parser_source_id
parser_source_version
parser_policy_id
resource_policy_id
fixture_id
report_id
report_version
expected_filename
destination_relative_id
destination_identity_version_token
pdf_signature_valid
pdf_parse_valid
observed_page_count
encrypted_or_protected
embedded_files_detected
javascript_detected
external_resource_request_detected
rendering_performed
network_access_performed
filesystem_write_performed
process_isolation_claimed
timeout_enforced
memory_limit_enforced
timeout_occurred
memory_limit_exceeded
resource_limit_exceeded
blocked_reason
evidence_version_token
evaluated_at
request_id
idempotency_key
action_performed
safety_flags
```

Unknown fields are rejected. Optional fields are only `structural_validation_completed`, `object_count_limit_exceeded`, and `parser_correlation_id`. Prohibited fields include `path`, process ID, command line, stack trace, raw exception, arbitrary diagnostics, attachment names, extracted text, and rendered output.

## 11. Types, bounds, and status registries

All string fields are non-empty bounded ASCII identifiers unless a closed boolean/status value is specified. Reuse existing limits: fixture ID 64, report ID 96, report version 32, filename 160, destination-relative ID 512, request ID 128, idempotency key 128, source/version/policy IDs 96, evidence and identity tokens 128, evaluated-at 64, and correlation ID 128. `expected_sha256` is 64 lowercase hexadecimal characters. Integers are non-negative actual integers; booleans are strict booleans and never accepted as integers. `observed_page_count` is an integer from 0 through 10,000. No unbounded list/dictionary, raw bytes, nested diagnostics, or implicit coercion is allowed.

The exact parser statuses are:

- `PARSER_RESULT_COMPLETE`
- `PARSER_RESULT_BLOCKED`
- `PARSER_RESULT_UNAVAILABLE`
- `PARSER_RESULT_TIMED_OUT`
- `PARSER_RESULT_RESOURCE_LIMITED`
- `PARSER_RESULT_UNSUPPORTED`

The exact blocked-reason registry is:

```text
invalid_parser_request_contract
unexpected_parser_request_fields
invalid_parser_result_contract
unexpected_parser_result_fields
unsupported_parser_request_version
unsupported_parser_result_version
parser_capability_missing
parser_capability_disabled
parser_capability_unsupported
parser_capability_invalid
parser_result_missing
parser_result_invalid
parser_result_stale
parser_result_identity_mismatch
parser_result_request_mismatch
parser_result_idempotency_mismatch
parser_result_target_mismatch
parser_timeout
parser_memory_limit_exceeded
resource_limit_exceeded
pdf_signature_validation_failed
pdf_parse_validation_failed
encrypted_pdf_unsupported
embedded_content_unsupported
javascript_detected
external_resource_request_blocked
parser_isolation_not_enforced
parser_network_access_detected
parser_filesystem_write_detected
parser_rendering_detected
parser_internal_failure
```

Existing locked registries retain authority where they express the same meaning; no duplicate alias is introduced.

## 12. Success and isolation criteria

Success requires `PARSER_RESULT_COMPLETE`, completed inspection, valid signature and parse, page count 1 through 10,000, no encryption/protection, no unsupported embedded execution, no rendering, network, write, timeout, memory, or resource limit, `action_performed=false`, all safety flags false, all bindings equal, and current evidence.

Production evidence is accepted only when `process_isolation_claimed`, `timeout_enforced`, and `memory_limit_enforced` are all true. An ordinary in-process result cannot masquerade as production isolation.

For the core test slice, option B applies: a specifically versioned deterministic test-only capability may be accepted with explicit `internal_test_only=true`, `fixture_only=true`, and `production_capable=false` authority flags in its private capability. The common v1 result schema is retained; these authority flags are capability fields, not unbounded result fields. Test evidence must not claim real isolation, and every adapter response remains internal/test-only.

## 13. Binding, token, freshness, and resources

The parser request and result must match fixture ID, report ID, report version, expected filename, destination-relative ID, destination identity version token, request ID, idempotency key, resource policy, and parser policy. Results are not reusable across targets.

The destination identity version token is produced by destination inspection only after object, containment, reparse, and file-identity validation. It is opaque, bounded, non-path data, bound to the observed target, included unchanged in the request, returned unchanged by the parser, and compared before acceptance. The parser does not create it.

Freshness requires a trusted producer `evidence_version_token`, `evaluated_at`, parser source version, destination identity token, request ID, and idempotency key. Browser time is not trusted. Missing, expired, or mismatched evidence maps to `parser_result_stale` or the more specific binding reason.

The exact resource binding is file size `104857600`, page count `10000`, timeout `10`, memory `268435456`, signature read `1024`, hash chunk `1048576`, and the resource-policy version above. Parser evidence never replaces adapter byte hashing.

## 14. Signature, page count, and hash ownership

The adapter owns the first bounded 1,024-byte PDF signature check and must not invoke the parser on an invalid signature. The parser repeats signature validity. Any disagreement fails closed as `pdf_signature_validation_failed`.

The parser capability owns observed page count. The adapter validates that the count is a non-negative bounded integer, enforces the 10,000 limit, and compares it with the request and later trusted metadata. The adapter does not independently parse page count.

The adapter owns bounded SHA-256 hashing in 1 MiB chunks and remains authoritative for size and hash. The parser result cannot supply or replace the byte-level hash.

## 15. Outcome mappings

- Encrypted or password-protected PDF: `PARSER_RESULT_BLOCKED` or `PARSER_RESULT_UNSUPPORTED`, destination response `DESTINATION_INSPECTION_BLOCKED`, reason `encrypted_pdf_unsupported`; no prompt or decryption.
- Embedded files, multimedia, forms actions, JavaScript, or unsupported active content: block conservatively with `embedded_content_unsupported` or `javascript_detected`; mere presence blocks equality classification even if no action executed.
- External resource request: `PARSER_RESULT_BLOCKED`, destination `DESTINATION_INSPECTION_BLOCKED`, `external_resource_request_blocked`.
- Timeout: `PARSER_RESULT_TIMED_OUT`, destination `DESTINATION_INSPECTION_BLOCKED`, `parser_timeout`.
- Memory, object-count, decompression, or other resource overflow: `PARSER_RESULT_RESOURCE_LIMITED`, destination `DESTINATION_INSPECTION_BLOCKED`, `resource_limit_exceeded` or `parser_memory_limit_exceeded`.
- Page count above 10,000: `PARSER_RESULT_RESOURCE_LIMITED`, destination `DESTINATION_INSPECTION_BLOCKED`, `resource_limit_exceeded`.
- Missing, disabled, unsupported, unavailable, invalid fake, or producer failure: destination `DESTINATION_INSPECTION_UNAVAILABLE` with the corresponding closed parser capability/result reason. It is never absent, identical, or conflicting.
- Malformed PDF: `PARSER_RESULT_BLOCKED`, destination `DESTINATION_INSPECTION_BLOCKED`, `pdf_parse_validation_failed`.

## 16. Validation order and first-failure precedence

The exact order is:

1. request contracts and versions;
2. unexpected fields;
3. request types and bounds;
4. source evidence;
5. cross-object identity;
6. private composite inspection capability;
7. Windows platform;
8. logical destination identity;
9. component policy;
10. root;
11. lexical containment;
12. parent chain;
13. final target object;
14. resolved containment;
15. source/destination identity;
16. file-size limit;
17. adapter signature validation;
18. construct parser request;
19. invoke private parser capability;
20. parser-result contract validation;
21. parser identity, request, and freshness binding;
22. parser status and safety validation;
23. page-count limit;
24. adapter SHA-256;
25. trusted metadata;
26. destination classification;
27. final freshness;
28. safety flags;
29. deterministic response.

First failure is exact and stable: invalid request beats missing capability; invalid source beats parser evidence; invalid root, unsafe parent/target, source/destination same, oversize file, and invalid signature each prevent invocation. Invalid parser-result contract beats parser parse outcome. Timeout beats metadata validation. Page-limit failure beats hash mismatch. Hash mismatch beats trusted metadata classification mismatch. Missing trusted metadata is considered only after accepted parser evidence.

## 17. Invocation prohibitions and target behavior

The parser is not invoked for invalid request/source/capability, unsupported platform, invalid logical identity or components, invalid root, unsafe parent, absent/directory/reparse/non-regular/out-of-root target, source/destination identity failure or equality, oversize file, or invalid adapter signature.

For `DESTINATION_ABSENT`, no parser capability, parser result, or trusted destination metadata is required; valid root, parents, containment, and final absence complete inspection. For an existing validated regular PDF, parser evidence is mandatory. Missing evidence fails closed.

## 18. Non-disclosure and safety

No response exposes private target, source or destination path, process ID, command line, worker executable, stack trace, exception, logs, raw diagnostics, attachment names, extracted content, or secrets.

Every request, result, capability, and response preserves false: `customer_ready_possible`, `customer_release_authorized`, `queue_write_performed`, `pdf_generation_performed`, `learning_applied`, `calibration_applied`, `accuracy_ledger_written`, `gcid_written`, `model_weights_changed`, `fighter_ratings_changed`, `prediction_logic_changed`, `artifact_archived`, `artifact_removed`, `artifact_overwritten`, `permanent_mutation_performed`, and `action_performed`.

## 19. Determinism and error handling

Equal observations and deterministic fake evidence produce equal results. The adapter creates no random token and no current time; trusted evidence supplies freshness values. Inputs remain unchanged and no mutable global parser registration exists. Expected parser outcomes are bounded dictionaries. Only the capability boundary may catch a provider failure, mapping it to `parser_internal_failure`; exception text never crosses the boundary and programmer errors are not broadly swallowed.

## 20. Focused implementation-test contract

Future two-file tests must cover valid test-only capability, missing/disabled/invalid/unsupported capability, invalid and unexpected request/result fields, missing result, identity/target/request/idempotency mismatch, stale evidence, timeout, memory/resource limits, malformed/encrypted PDFs, embedded files, JavaScript, external requests, network/write/render flags, missing isolation claims, page counts 10,000 and 10,001, path-disclosure attempts, deterministic output, unchanged inputs, and no invocation for absent, unsafe, non-regular, or oversize targets.

Static tests must prove no global registry, dynamic import, `eval`, process creation, shell, network, write, environment-selected parser, parser path from request data, or unrestricted scan. They must prove no parser invocation in every prohibition case.

## 21. Two-file feasibility and worker status

The resolved boundary permits exactly these future files:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

A separate parser interface file is not mandatory for the core slice because the private capability contract is defined at the adapter boundary and the deterministic fake is test-local. A third file becomes mandatory only for a separately authorized production worker or producer; it must not be hidden in this two-file claim.

No parser worker, isolation enforcement, timeout proof, memory isolation proof, or production parser-capability producer exists. These are implementation blockers for production and direct-proof blockers for isolation, integration blockers for a producer, and endpoint blockers. A deterministic test-only capability is sufficient for core adapter contract implementation, focused branch tests, and direct proof of the adapter boundary only; it is not production parser proof.

## 22. Contract blockers resolved and remaining blockers

Resolved: parser ownership and placement; three-argument validity; composite capability model; request and result versions/schemas; field bounds; status and reason registries; success and isolation criteria; test-only authority; destination, target-token, request, idempotency, freshness, and resource binding; signature/page/hash ownership; failure mappings; validation order; first-failure precedence; invocation conditions; response non-disclosure; safety flags; determinism; error handling; focused tests; static authority; and two-file feasibility.

Remaining blockers are implementation and proof only: construction/integrity of real private capabilities, a real isolated parser worker with enforceable timeout and memory limits, production parser-result producer, Windows/reparse direct proof, trusted producer integration, and direct adapter proof. No remaining unresolved parser-boundary design choice changes the public contract.

## 23. Contract and readiness effect

`PARSER_RESULT_CONTRACT_READY_FOR_IMPLEMENTATION_REASSESSMENT`

The previous implementation-readiness reassessment must be superseded by a new final reassessment because the first argument is now explicitly a composite private inspection capability and the parser boundary is contractually fixed. This document does not automatically authorize implementation.

Endpoint: `NOT_READY_FOR_ENDPOINT`.

Dashboard: `NOT_READY_FOR_DASHBOARD`.

Archive mutation: `NOT_READY_FOR_ARCHIVE_MUTATION`.

## 24. Smallest safe next slice

Recommend exactly: **Button 2 governed internal PDF archive destination-inspection implementation-readiness final reassessment**.

Proposed file:

`docs/button2_governed_internal_pdf_artifact_archive_destination_inspection_implementation_readiness_final_reassessment_v1.md`

## 25. Recommended sequencing

A. injected parser-result contract resolution; B. final implementation-readiness reassessment; C. separately authorized core read-only destination-inspection adapter and focused tests; D. direct adapter proof; E. real parser-worker readiness and implementation; F. producer readiness; G. archive-planning endpoint readiness; H. endpoint implementation and route proof; I. dashboard readiness and proof; J. archive-mutation readiness; K. separately authorized copy-and-retain implementation.

## 26. Explicit non-authorization

This contract does not authorize a destination-inspection adapter, focused tests, parser worker, process creation, parser-capability producer, root producer, source-identity producer, trusted-metadata producer, archive-root configuration, endpoint, route, dashboard, directory/file/temporary-file creation, PDF parsing execution, PDF generation, network, hard-link or junction/reparse creation, copy, archive, finalization, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit/lifecycle persistence, customer-ready classification, customer release, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, model changes, or deployment.

## 27. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_INJECTED_PARSER_RESULT_CONTRACT=INJECTED_PARSER_RESULT_CONTRACT_RESOLVED`
