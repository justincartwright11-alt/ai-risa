# Button 2 Governed Internal PDF Artifact Archive-Plan Adapter
## Implementation-Readiness Reassessment v1

## 1. Executive verdict

`READY_FOR_PURE_ARCHIVE_PLAN_ADAPTER_IMPLEMENTATION`

The planner-specific contract is sufficiently exact for a separately authorised two-file implementation slice. The future adapter may be implemented as one pure, deterministic, non-mutating function over normalized bounded dictionaries and may be tested with small in-memory dictionaries. This positive readiness finding authorises nothing by itself: it does not authorise planner implementation, tests, evidence producers, an endpoint, a dashboard control, archive-root configuration, or mutation.

Endpoint, dashboard, and archive mutation remain blocked as recorded below.

## 2. Locked baseline

- Latest contract commit: `bf683f5fbf9b18df51ec9d0910286da35ae1e5cb`.
- Previous readiness commit: `0d4b20f04f90fdc1eba5eb63f7079122d1d5e0e4`.
- Contract readiness effect: `CONTRACT_READY_FOR_IMPLEMENTATION_REASSESSMENT`.
- The governed fixture is fictional only: `closed_loop_governed_local_fixture_v1`.
- Referenced artifacts are internal/test-only and not customer-ready or for customer release.
- The existing inspection chain is read-only.
- No planner, endpoint, dashboard control, archive-root configuration, archive mutation, or removal mutation is implemented.

The live proof establishes only inspection and governed internal test generation evidence. It does not establish lifecycle authority, archive evidence, or mutation authority.

## 3. Proposed implementation scope

The minimum safe future implementation slice is exactly these two files:

- `operator_dashboard/button2_governed_internal_pdf_archive_plan_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_plan_adapter_v1.py`

No other file belongs in that slice. In particular, it must not modify `app.py`, templates, the inspection adapter, the preflight adapter, the fixture, a generation route, Button 1, Button 3, or customer PDF code. The two-file scope is sufficient because the adapter consumes normalized dictionaries and tests can construct them in memory; no producer is required to implement the pure function.

## 4. Proposed public API

The exact public function is:

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

The argument order is stable. Each argument has one normalized purpose, and none grants filesystem authority: root capability contains bounded identity and booleans, never a path; destination evidence is supplied evidence, not an inspection handle; authorization and audit inputs are prior bounded evaluations/capabilities; concurrency is evidence, not a lock. No optional implicit dependency is required. The return is one bounded dictionary with a stable closed response schema. Expected blocked states return bounded responses rather than exceptions. Programmer faults may raise during development tests under the exception policy below.

## 5. Pure-function boundary

The implementation is ready to remain completely pure and filesystem-independent. It requires none of:

- `pathlib`, `os`, `shutil`, file opening, directory listing, or filesystem inspection;
- environment variables, Flask, requests, sockets, network access, or databases;
- current datetime lookup, randomness, mutable caches, mutable module state, or unrestricted logging.

Any such dependency is a slice blocker. Supplied timestamps are data only. No absolute path is accepted, constructed, inspected, or returned.

## 6. Contract-version constants

The module should define explicit exact-version constants for:

- planner contract;
- inspection evidence;
- archive-root capability;
- destination evidence;
- authorization;
- audit capability; and
- concurrency evidence.

Each normalized input version must equal its supported constant. Unsupported or missing versions produce deterministic `unsupported_contract_version` (or the canonical invalid-contract result where the version field itself is malformed), before later validation. No version fallback is permitted.

## 7. Closed field registries

The implementation should define closed registries for request fields, consumed governed-row fields, artifact-evidence fields, archive-root capability fields, destination-evidence fields, authorization-evidence fields, audit-capability fields, concurrency-evidence fields, response fields, safety flags, blocked reasons, and outcome statuses.

Unknown request fields are rejected with `unexpected_plan_fields`. For all normalized evidence objects, the safer policy is also to reject unexpected fields with the same bounded contract error rather than silently ignore them. This keeps producer drift visible and makes the pure boundary deterministic. The fixture's broader source shape must be normalized before reaching the planner.

## 8. Type-validation readiness

Every field has an implementable type rule. Booleans must be actual booleans, never integers or truthy values. File size is a non-negative integer no greater than `2^63 - 1`; page count is a positive integer no greater than `10,000`. SHA-256 is exactly 64 lowercase hexadecimal characters. Required identifiers and filenames are bounded non-empty ASCII strings; optional strings are either absent or bounded strings. Required mutation flags are false; required validation flags are true; enums must be one of their closed values. No implicit coercion or trimming into acceptance is allowed.

## 9. Exact length limits

The blocker-resolution contract fixes these limits:

| Field | Maximum |
|---|---:|
| `fixture_id` | 64 characters |
| `report_id` | 96 characters |
| `report_version` | 32 characters |
| `expected_filename` | 160 characters |
| `request_id` | 128 characters |
| `idempotency_key` | 128 characters |
| `approval_id` | 128 characters |
| `source_boundary_id` / `archive_boundary_id` | 96 characters |
| `destination_relative_id` | 512 characters |

The contract also fixes each logical destination component at 160 characters, while the more specific limits above govern fixture, report, and version fields. No listed limit remains unresolved and no number is invented here.

## 10. Path-component validation readiness

The ASCII-only v1 rejection policy is implementable as a pure validator. Accepted identity components use the closed ASCII alphabet selected by the contract: fixture and report IDs use letters, digits, underscore, and hyphen; report version additionally permits periods; filename uses ASCII letters, digits, underscore, hyphen, periods, and the required `.pdf` suffix.

The validator rejects separators, colon and ADS syntax, NUL and controls, non-ASCII characters, leading/trailing whitespace, leading/trailing periods where prohibited, `.` and `..`, traversal-like sequences, length overflow, and Windows reserved device names case-insensitively, including extension forms. It does not normalize unsafe input. It rejects case-insensitive identity collisions when supplied evidence indicates one. No filesystem knowledge is needed.

## 11. Filename validation readiness

The deterministic filename is validated as a basename only: no separator, drive form, UNC form, colon/ADS syntax, reserved Windows basename, control, non-ASCII character, prohibited leading/trailing period or whitespace, or length overflow. The required `.pdf` extension is enforced. The filename must exactly match the request and the artifact evidence. No filesystem access is required to validate syntax or identity.

## 12. Destination-relative identifier and identity matching

The adapter derives exactly:

`fixture_id/report_id/report_version/expected_filename`

The separator is the logical forward slash only. The result has exactly four non-empty components, no leading/trailing slash, no absolute-path interpretation, and a maximum length of 512. It is a bounded identifier, never an executable path. Repeated valid inputs produce the same value.

Before a ready plan, the adapter must compare request identity to governed row, artifact evidence, root capability, destination evidence, and authorization evidence as applicable: fixture, report, version, expected state, filename, SHA-256, size, page count, root ID/version, policy ID, destination-relative ID, action, request ID, idempotency key, and approval binding. Source and archive boundary identity must be present and distinct. No identity mismatch may be repaired by normalization.

## 13. Artifact eligibility readiness

The adapter can deterministically require all of the following: `ACTIVE_INTERNAL_TEST_ARTIFACT`; inspection completed; signature valid; parse valid; identity valid; classification valid; internal warning valid; expected and observed filename match; SHA-256 match; size match; page count match; and release and mutation flags false. Missing, absent, blocked, corrupt, stale, mismatched, or forbidden-release evidence is ineligible. Governed-row gates require fictional, internal-only, test-only identity, required provenance validity/binding, customer-ready false, customer-release false, and queue-write false.

## 14. Archive-root capability readiness

The pure adapter validates only bounded capability fields: exact root ID/version/policy identity, configured, enabled, absolute-valid, server-controlled, customer-isolated, source-isolated, link-safe, bounded platform, filesystem policy, sanitization policy, and archive boundary ID. It does not know or receive the actual root path. Missing, disabled, invalid, policy-mismatched, or identity-mismatched capability maps to the closed root reasons.

The capability producer remains external. Its absence prevents a ready result for that input, but does not prevent implementing or unit-testing the pure adapter with contract-conforming in-memory capability dictionaries.

## 15. Destination-evidence readiness

The adapter consumes, and never produces, destination evidence. Required outcome mappings are:

- `DESTINATION_EVIDENCE_NOT_EVALUATED`, missing, incomplete, or stale evidence -> `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION`;
- `DESTINATION_ABSENT`, with complete safe evidence -> potentially `ARCHIVE_PLAN_READY`;
- `IDENTICAL_ARCHIVE_PRESENT`, with exact identity and metadata match -> potentially `ARCHIVE_ALREADY_SATISFIED`;
- conflicting, unsafe, same-path, normalization-collision, reparse/link, non-regular, outside-root, directory-collision, or idempotency-conflict states -> `ARCHIVE_PLAN_BLOCKED` with the canonical specific reason.

No filesystem check occurs inside the planner. The destination producer is separately assessed later.

## 16. Authorization-evidence readiness

Authorization evidence must match action `plan_internal_pdf_archive`, fixture/report/version, request ID, and idempotency key; contain `planning_authorized=true`; contain completed evidence and a bounded non-expired evaluation represented as input; and include approval ID when the contract requires it. `execution_authorized` must never be true in planner output. An approval ID alone is insufficient. No session or actor authentication occurs inside the planner.

Missing or unsatisfied planning authorization maps to `ARCHIVE_PLAN_REQUIRES_AUTHORIZATION` or its canonical blocked reason according to the locked response precedence; mismatched identity is blocked deterministically.

## 17. Audit-capability readiness

Audit capability requires a bounded sink ID, availability, supported schema, supported planning event, persistence authorization as capability evidence, and `action_performed=false`. The planner creates no audit record and performs no persistence. An unavailable sink maps specifically to `ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY`, not to a generic blocked state; unsupported schema maps to `audit_schema_unsupported` within the bounded blocked response.

## 18. Concurrency-evidence readiness

Concurrency evidence requires completed evidence, no active artifact action, no conflicting action, a bounded artifact version token, current source evidence, current destination evidence, and supplied `evaluated_at`. The timestamp is data only. The planner never reads the current clock, calculates freshness, locks, reserves, or persists state. Missing, stale, conflicting, or incomplete evidence maps to `ARCHIVE_PLAN_REQUIRES_CURRENT_CONCURRENCY_EVIDENCE` or the canonical concurrency reason.

## 19. Idempotency readiness

The canonical binding fields are exact: requested action; fixture/report/version; expected artifact state; filename; SHA-256; size; page count; root ID/version; archive policy; derived destination-relative ID; and approval ID where applicable. The lowest-authority v1 design is to validate identity binding only, accept a server-produced fingerprint or bounded prior-result evidence when supplied, return the canonical bounded components, and avoid generating a cryptographic fingerprint in the planner. Conflicting reuse returns `idempotency_conflict`; the planner does not hash, persist, or invent an idempotency record.

## 20. Validation order and outcome precedence

The implementation can follow the exact fail-closed order:

1. contract versions;
2. unexpected fields;
3. types and bounds;
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

The first failure in this order determines the result. Invalid contract/version overrides all later states. Artifact ineligibility overrides missing destination evidence. Authorization is evaluated only after destination evidence. An identical archive is returned only after all earlier eligibility and identity checks pass. This removes ambiguous multi-failure precedence.

## 21. Response, blocked-reason, and exception readiness

Every success and blocked response uses the same bounded response keys: contract version, status, request/action identity, current and proposed state, filename and expected metadata, bounded boundary/root/policy IDs, destination identity/status/classification, authorization/audit/concurrency summaries, planning and safety flags, request/idempotency/approval IDs, and `blocked_reason`. No raw evidence objects, unrestricted paths, raw bytes, secrets, or arbitrary exception text are returned.

The closed blocked-reason registry from the blocker-resolution contract is sufficient and includes the specific artifact, root, component, destination, authorization, audit, concurrency, and idempotency reasons. No expected failure lacks a canonical mapping. Expected validation failures return bounded dictionaries. Programmer faults may raise internal exceptions in development tests; no broad exception swallowing is allowed, and caller-controlled exception text never enters a response.

All response safety flags are present and false, including `execution_authorized=false`, `action_performed=false`, `artifact_archived=false`, `artifact_removed=false`, `artifact_overwritten=false`, and `permanent_mutation_performed=false`.

## 22. Focused test and determinism-proof readiness

The two-file test scope can cover the complete contract using small in-memory normalized dictionaries only. It must include valid ready output; identical repeated output; already-satisfied output; missing destination evidence; every unsupported version; unexpected request field; invalid type; excessive length; non-ASCII, separator, traversal, colon/ADS, drive, UNC, reserved-name, and case-collision inputs; governed identity mismatch; absent/blocked artifact; signature, parse, hash, size, page, classification, warning, release, root, destination, authorization, audit, concurrency, idempotency, and mutation-flag failures; no absolute path in output; no prohibited import/call; unchanged inputs; and no filesystem changes.

Static authority tests should use AST or narrow source inspection to reject imports or calls involving `os`, `pathlib`, `shutil`, `tempfile`, `subprocess`, Flask, file opening, sockets/network, and database libraries. This is narrow source inspection, not broad security tooling. Determinism tests deep-compare repeated outputs, deep-compare inputs before and after calls, use key-order permutations, and assert no generated timestamps, random IDs, environment reads, or mutable state.

## 23. Concrete producer dependency analysis

| Producer | Pure adapter implementation | Direct proof | Endpoint | Mutation |
|---|---|---|---|---|
| Archive-root capability | Not required; use in-memory normalized input | Required for real integration proof | Required | Required |
| Destination inspection | Not required; use in-memory normalized input | Required for direct integration proof | Required | Required |
| Authorization evidence | Not required; use in-memory normalized input | Required for authorized-route proof | Required | Required |
| Audit capability | Not required; use in-memory normalized input | Required for direct proof | Required | Required |
| Concurrency evidence | Not required; use in-memory normalized input | Required for direct proof | Required | Required |

Thus the pure adapter may be implemented and tested before those producers exist. Their absence blocks direct runtime/integration proof and all later endpoint or mutation work, not the two-file pure implementation slice.

## 24. Proposed implementation authority

If separately authorised, implementation authority is restricted exactly to:

- `operator_dashboard/button2_governed_internal_pdf_archive_plan_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_plan_adapter_v1.py`

No app, template, adapter, fixture, route, generation, Button 1, Button 3, or customer PDF file may change.

## 25. Proposed test command

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_archive_plan_adapter_v1.py
```

This command belongs only to the separately authorised implementation slice and is not run by this docs-only reassessment.

## 26. Implementation stop conditions

Stop without commit if any normalized field remains ambiguous; any exact length limit is missing; any blocked-reason mapping is ambiguous; filesystem access becomes necessary; an external producer must be implemented in the same slice; an endpoint or dashboard edit becomes necessary; an unrelated file must change; or the focused test fails.

## 27. Endpoint, dashboard, and mutation readiness

`NOT_READY_FOR_ENDPOINT`

Endpoint work remains blocked until the adapter passes focused tests, direct non-mutating proof passes, the route request contract is separately assessed, environment and fixture gates are reviewed, and path disclosure is reviewed.

`NOT_READY_FOR_DASHBOARD`

Dashboard work remains blocked until the planner and endpoint exist, live route proof passes, and dashboard language and authority boundaries are separately assessed.

`NOT_READY_FOR_ARCHIVE_MUTATION`

Mutation remains outside this reassessment. No copy, archive, removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, or persistence is approved.

## 28. Readiness matrix

| Area | Finding |
|---|---|
| Public function | READY |
| Argument contracts | READY |
| Contract versions | READY |
| Field registries | READY |
| Type validation | READY |
| Length limits | READY |
| Component rules | READY |
| Filename rules | READY |
| Relative ID derivation | READY |
| Identity matching | READY |
| Artifact eligibility | READY |
| Root capability | READY |
| Destination classifications | READY |
| Authorization input | READY |
| Audit input | READY |
| Concurrency input | READY |
| Idempotency | READY |
| Validation order | READY |
| Blocked reasons | READY |
| Response schema | READY |
| Safety flags | READY |
| Testing feasibility | READY |
| Producer independence | READY |

## 29. Remaining blockers

No unresolved contract blocker prevents the two-file pure adapter implementation. The remaining concrete archive-root, destination, authorization, audit, and concurrency producers prevent direct runtime/integration proof and later endpoint or mutation work, but they are intentionally external to the pure adapter and therefore are not implementation blockers for this slice.

## 30. Smallest safe next slice

The smallest safe next slice is exactly:

**Button 2 governed internal PDF pure non-mutating archive-plan adapter implementation.**

It must remain separately authorised and restricted to the two files named above. No endpoint, dashboard, or mutation is recommended in that slice.

## 31. Recommended sequencing

A. Pure adapter implementation-readiness reassessment.
B. Separately authorised pure archive-plan adapter and focused tests.
C. Direct non-mutating adapter proof.
D. Destination-inspection capability readiness.
E. Supporting evidence producers.
F. Planning endpoint readiness.
G. Endpoint and route test.
H. Live planning route proof.
I. Dashboard planning readiness.
J. Dashboard control and proof.
K. Archive mutation readiness.
L. Separately authorised copy-and-retain archive implementation.

## 32. Explicit non-authorization

This reassessment does not authorise planner implementation; tests; external evidence producers; destination inspection; endpoint; dashboard; archive-root configuration; directory creation; temporary-file creation; copy; archive; finalization; source removal; quarantine; deactivation; restoration; deletion; secure deletion; rename; movement; overwrite; regeneration; audit persistence; lifecycle persistence; customer-ready classification; customer release; queue or ledger writes; learning; calibration; accuracy-ledger writes; GCID writes; deployment; or any other mutation.

## 33. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_ARCHIVE_PLAN_ADAPTER_IMPLEMENTATION_READINESS=READY_FOR_PURE_ARCHIVE_PLAN_ADAPTER_IMPLEMENTATION`
