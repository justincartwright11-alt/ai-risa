# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Implementation Readiness Reassessment v1

## 1. Executive verdict

`READY_WITH_IMPLEMENTATION_BLOCKERS`

The contract is sufficiently exact for a separately authorised, narrowly scoped read-only core adapter and focused-test slice using in-memory normalized evidence, pytest-owned temporary directories, Windows platform gating, and mocked reparse metadata. Parser isolation enforcement, production evidence producers, real privileged reparse proof, and direct proof remain blockers for later readiness stages. This positive readiness finding authorises nothing by itself.

## 2. Locked baseline

- Full latest commit: `026a250` (current baseline prefix verified before this slice).
- Windows capability/file-identity verdict: `WINDOWS_CAPABILITY_FILE_IDENTITY_BLOCKERS_PARTIALLY_RESOLVED`.
- Windows contract effect: `WINDOWS_CAPABILITY_CONTRACT_READY_WITH_BLOCKERS`.
- Metadata/resource contract commit: `8203d34beee22508586e17d620a9d08a12d8ff2f`.
- Destination-inspection contract commit: `1e528befbce2a3b7722719ccc8865189c5ee4d03`.
- Readiness-assessment commit: `84d192a0bc7f69a6a214e91128ef6d8806010ea9`.
- The governed fixture is fictional only and artifacts are internal/test-only.
- No destination-inspection adapter, parser worker, capability producer, source-identity producer, metadata producer, approved production archive root, endpoint, dashboard, or archive mutation exists.

## 3. Reassessment purpose

A future slice may contain exactly one read-only destination-inspection adapter and one focused test file. It may use in-memory normalized capability, source-identity, trusted-metadata, and request objects; pytest-owned temporary directories; Windows platform gating; controlled injected parser results; and mocked reparse metadata where real creation is not authorised. It may not implement production producers, endpoint integration, dashboard integration, or mutation.

## 4. Proposed implementation files and API

The minimum safe implementation files are exactly:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

No existing file requires modification for the core slice. The stable API is:

```text
inspect_button2_governed_internal_pdf_archive_destination_v1(
    archive_root_capability,
    source_artifact_evidence,
    destination_request,
)
```

Argument order is stable. The capability owns private root authority, source evidence owns trusted source identity and artifact evidence, and the request owns bounded expected identity. No caller absolute path, global configuration lookup, endpoint/session context, or browser authority is required. One bounded dictionary response is sufficient.

## 5. Private capability feasibility

Core tests may construct an immutable private capability containing bounded root identity, a pytest-owned absolute target, configuration fingerprint, capability/version/source identifiers, platform/policy identifiers, validity evidence, and false mutation flags. The private target must never enter the response, logs, planner data, or browser data.

A production integrity mechanism is not required for the in-memory core adapter slice, provided the adapter validates structure and fails closed. It is required before production capability integration, endpoint readiness, or direct proof against a producer.

## 6. Source identity and trusted metadata feasibility

Focused tests may construct normalized source identity in memory, bound to source boundary, fixture, report, version, filename, SHA-256, size, page count, and opaque volume/file identity values. A production source-identity producer is not required before the core adapter slice, but is required before producer readiness, endpoint readiness, and production proof.

Focused tests may provide dictionaries conforming to the locked trusted metadata envelope. The adapter must reject missing, malformed, stale, integrity-invalid, identity-mismatched, classification-mismatched, warning-mismatched, provenance-invalid, request-mismatched, and idempotency-mismatched metadata. A production metadata producer and cryptographic integrity mechanism are later dependencies, not core two-file prerequisites.

## 7. Windows API/library choice

The contract requires stable Windows volume/file identity and reparse inspection but does not require a particular API name in the public contract. Exact standard-library binding, narrow `ctypes`, or an already-installed approved dependency is an implementation choice only if it preserves the contract and test injection boundary. No new dependency may be invented or assumed. If the selected mechanism cannot obtain stable identity, inspect reparse state, and preserve read-only authority, implementation stops and the API choice becomes a blocker.

Acceptable future imports are bounded `pathlib`, `os`, `stat`, `hashlib`, `platform` or `sys`, `typing`, the repository-supported PDF parser through an injected boundary, and a narrow Windows binding. Network, shell, subprocess, environment-root, database, and mutation imports are prohibited.

## 8. Authority boundary

Production code must not write-open, create files/directories/temp files, copy, move, rename, replace, unlink, delete, rmdir, invoke shell or PowerShell, use an environment-selected root, accept browser paths, recursively scan, wildcard-resolve, choose alternate targets, or execute archives. Test code may create only pytest-owned temporary objects required for focused observation.

## 9. Root, component, parent, target, identity, and containment readiness

The contract is implementation-ready for validating capability version and fields, private target type, absolute drive-qualified target, root ID/version/policy/boundary, configuration fingerprint, configured/enabled/server-controlled flags, source/customer isolation, Windows platform, filesystem policy, and sanitization policy.

It is implementation-ready for ASCII-only components, planner bounds, separator/colon/ADS/control/traversal rejection, trailing-space/period rejection, reserved-name rejection, exact four-component reconstruction, exact request comparison, and no current-working-directory dependence.

It is implementation-ready for root existence/type/reparse checks, deterministic parent-chain inspection, missing-parent, non-directory, reparse, access-denied, and unexpected-failure outcomes without sibling enumeration. It is implementation-ready for absent, regular, directory, reparse, special, access-denied, sharing-violation, and unexpected final targets.

It is implementation-ready for opaque source identity, destination identity from read-only observation, volume/file comparison, same-object and hard-link handling, identity-unavailable handling, no raw handle/path disclosure, lexical plus resolved containment, root equality rejection, root nesting rejection, and fail-closed resolution errors. Exact Windows API selection remains an implementation choice constrained by these requirements.

## 10. Resource-policy readiness

The exact limits are implementable: 100 MiB file precheck, 1,024-byte signature read, 1 MiB SHA-256 chunks, no complete-file memory load, maximum 10,000 pages, and one deterministic target. Resource overflow maps to `resource_limit_exceeded`; no recursive or unrelated hashing is allowed.

## 11. Parser-boundary finding

The core adapter may proceed before a real isolated parser worker exists only through an injected/internal bounded parser-result dependency. The test fake may return bounded signature, parse, page-count, encryption, and resource outcomes; it must not claim process isolation. The adapter contract must preserve the mandatory future worker design: 10-second timeout, no network/write authority, one read-only target capability, and 256 MiB design ceiling.

This is option B, not a weakening of isolation. A real parser worker is not part of the two-file slice. Its separate future readiness assessment must identify the worker module, worker-focused tests, timeout/isolation proof, and memory-limit proof; no worker files are authorised here.

## 12. Metadata, classification, response, and blocked-reason readiness

Metadata validation is ready against the exact version, closed fields, bounds, integrity-token shape, fixture/report/version, hash/size/page, exact classification, exact warning, provenance, root/destination, request, idempotency, freshness, and false action flag.

The destination classifications are deterministic: `DESTINATION_ABSENT`, `IDENTICAL_ARCHIVE_PRESENT`, `CONFLICTING_ARCHIVE_PRESENT`, `DESTINATION_NON_REGULAR`, `DESTINATION_LINK_OR_REPARSE`, `DESTINATION_DIRECTORY_COLLISION`, `DESTINATION_OUTSIDE_APPROVED_ROOT`, `SOURCE_DESTINATION_SAME`, and `IDENTITY_NORMALIZATION_COLLISION`.

The response schema is implementable with stable bounded keys, no private target, absolute path, raw Windows identity, raw metadata envelope, or exception text. Every safety flag and `action_performed` remains false.

The merged reason registry is usable with first-failure precedence. Base reasons remain authoritative; metadata/resource reasons cover trusted evidence and limits; Windows reasons cover capability, root, parent, identity, alias, and reparse outcomes. Duplicate meanings must be represented once. Runtime-dependent cases use bounded unavailable/failed responses. Any unresolved precedence discovered in focused tests is an implementation stop condition.

## 13. Validation order and error mapping

The merged implementation order is unambiguous:

1. request contract and versions;
2. unexpected fields;
3. types and bounds;
4. source evidence;
5. cross-object identity;
6. private capability;
7. platform;
8. destination logical identity;
9. component policy;
10. root object;
11. lexical containment;
12. parent chain;
13. final target object;
14. resolved containment;
15. source/destination identity;
16. file-size limit;
17. signature;
18. injected parser result;
19. page limit;
20. SHA-256;
21. trusted metadata;
22. destination classification;
23. freshness;
24. safety flags;
25. deterministic response.

Missing root, disabled/invalid/reparse root, missing/non-directory/reparse/access-denied/failing parent, access-denied/sharing-violation/absent/directory/special/reparse target, unavailable identity, parser failure, resource failure, and unexpected internal fault each have bounded mappings from the locked contracts. Expected outcomes return dictionaries without raw text. Development programmer errors may raise in focused tests, but broad exception swallowing and path-containing serialization are prohibited.

## 14. Test-only filesystem authority and readiness

The focused test may use `pytest` `tmp_path`, synthetic internal PDF bytes, ordinary directories and regular files, permitted hard links inside pytest-owned temporary scope, narrow monkeypatches for identity/reparse metadata, and no repository, customer, environment-selected, or global archive root.

Standard tests are ready for valid absent/identical/conflicting targets; root, platform, component, parent, target, containment, identity, resource, signature, parser-result, metadata, classification, warning, provenance, request, idempotency, disclosure, safety, and no-mutation cases.

Windows platform-gated tests may cover real identity, same-file comparison, hard links, reserved names, trailing-dot/space behavior, path length, and sharing violations. Normal Windows CI may run supported cases; optional platform tests remain subject to environment proof. Real junction, mount, device, cloud-placeholder, and privileged symlink tests remain separately authorised. Mocked reparse tests are ready for branch and response validation only.

Static AST/source tests must prohibit all production mutation, subprocess, PowerShell, network, environment-root, browser-path, and unrestricted-scan authority. Determinism tests must prove equal responses for equal observations, no random IDs, no internally generated current time, no environment variation, no mutable global state, and unchanged inputs.

## 15. Two-file scope and producer dependencies

The core adapter/test implementation can remain exactly two files when the parser is injected and test-local evidence is used. A third file is a blocker unless a separate slice authorises it.

Dependency classification:

- private capability producer: required before production integration, endpoint, and direct producer proof;
- source-identity producer: required before producer readiness, endpoint, and direct producer proof;
- trusted-metadata producer: required before producer readiness, endpoint, and direct producer proof;
- parser worker: required before parser isolation proof and production/direct parser proof;
- root configuration source: required before real-root inspection, endpoint, and mutation.

None is required before the narrowly scoped core two-file implementation/tests when evidence is constructed in memory and the parser boundary is injected.

## 16. Residual proof dependencies

Residual proof dependencies are real Windows identity and hard-link proof, real reparse/junction proof, parser timeout and memory-isolation proof, path non-disclosure proof, no-mutation proof, and direct read-only adapter proof. These do not authorize a production root, producer, endpoint, dashboard, or mutation.

## 17. Proposed focused command and implementation authority

The later implementation slice may run exactly:

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py
```

Its authority must be restricted to exactly:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

## 18. Stop conditions

Stop without commit if a third source file is required, parser isolation is silently weakened, a production producer must be created, a test capability cannot remain local, mutation is required, exact identity cannot be obtained or safely abstracted, reason precedence is ambiguous, an absolute path appears in output, focused tests fail, or any unrelated file must change.

## 19. Readiness matrix

| Area | Status |
|---|---|
| Public API | READY |
| Private capability input | PARTIALLY_READY |
| Source identity input | READY for in-memory tests |
| Trusted metadata input | READY for in-memory tests |
| Version and field registries | READY |
| Bounds and path policy | READY |
| Root/parent/target inspection | PARTIALLY_READY |
| File identity and hard links | PARTIALLY_READY |
| Containment | PARTIALLY_READY |
| Resource policy | READY |
| Parser boundary | PARTIALLY_READY |
| Metadata/classification | READY |
| Response schema | READY |
| Blocked reasons/order/errors | READY with stop-on-ambiguity rule |
| Test fixture and standard tests | READY |
| Windows tests | PARTIALLY_READY |
| Reparse proof | PARTIALLY_READY |
| Static authority | READY as a test requirement |
| Determinism | READY as a test requirement |
| Producer independence | READY for core in-memory slice |
| Exact two-file scope | READY with injected parser boundary |

## 20. Remaining core implementation blockers

The two-file core slice is permitted for separate authorization, but implementation remains blocked until its authorisation explicitly supplies a test-local private capability fixture and an injected parser-result boundary. The exact Windows API must be selected during implementation without changing the public contract. Any inability to obtain stable identity or safely abstract reparse inspection is a blocker. Real platform proof, parser isolation proof, and production producers remain later blockers.

## 21. Smallest safe next slice and future files

Recommend exactly: **Button 2 governed internal PDF read-only archive destination-inspection adapter implementation**.

Future files, and only these files:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

## 22. Recommended sequencing

A. implementation-readiness reassessment; B. separately authorised read-only destination-inspection adapter and focused tests; C. direct read-only adapter proof; D. capability/source-identity/metadata producer readiness; E. archive-planning endpoint readiness; F. endpoint and route test; G. live route proof; H. dashboard planning-control readiness; I. dashboard implementation and proof; J. archive-mutation readiness; K. separately authorised copy-and-retain archive implementation. Insert a separate parser-worker readiness/implementation slice before claiming parser isolation proof.

## 23. Explicit non-authorization

This reassessment does not authorize adapter implementation, tests, parser worker, process creation, private capability producer, source-identity producer, metadata producer, root configuration, real junction/symlink/mount/reparse/hard-link creation, endpoint, route, dashboard, directory/file/temp creation outside future pytest-owned scope, PDF generation, copy, archive, finalization, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit/lifecycle persistence, customer classification/release, queue/ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 24. Endpoint, dashboard, and mutation status

Endpoint: `NOT_READY_FOR_ENDPOINT` because no inspector, direct proof, producer, endpoint contract, or live route proof exists.

Dashboard: `NOT_READY_FOR_DASHBOARD`.

Archive mutation: `NOT_READY_FOR_ARCHIVE_MUTATION`.

## 25. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_IMPLEMENTATION_READINESS=READY_WITH_IMPLEMENTATION_BLOCKERS`
