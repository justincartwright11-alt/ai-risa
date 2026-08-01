# Button 2 Governed Internal PDF Artifact Archive Planning Adapter Readiness Assessment v1

## 1. Executive verdict

`READY_WITH_BLOCKERS`

The current evidence is sufficient to document and design a future pure, deterministic, non-mutating archive planning adapter. It is not sufficient to implement that adapter yet because the archive-root configuration, sanitization/rejection policy, planner-normalized evidence contract, platform matrix, destination evidence, authorization/audit inputs, and concurrency evidence remain unresolved. A positive design-readiness finding does not authorize implementation. Archive mutation remains blocked.

Readiness is separated as follows:

| Capability | Verdict |
|---|---|
| Document or design a planner | READY |
| Implement a pure non-mutating planner | READY_WITH_BLOCKERS |
| Expose a backend planning endpoint | NOT_READY_FOR_ENDPOINT |
| Expose a dashboard planning control | NOT_READY_FOR_DASHBOARD |
| Perform archive mutation | NOT_READY_FOR_ARCHIVE_MUTATION |

## 2. Locked baseline

- Threat-review commit: `656b95a`.
- Threat-review verdict: `THREAT_REVIEW_COMPLETE_READY_FOR_NON_MUTATING_ARCHIVE_PLANNING_READINESS`.
- Archive destination contract commit: `8302cb7afd78a56c1c78096fe36f909fd0dd1e7b`.
- Audit/authorization contract commit: `cbadefb9cf73236aa0786917f2c8ebb236be292a`.
- Removal/retention policy commit: `bc551a5709f8c7de0ba82df6a509f1e45c97d945`.
- The fixture is fictional and governed for internal/test use only.
- The artifact is internal/test-only, not customer-ready, and not for customer release.
- The inspection chain is proven read-only.
- No archive planner or mutation is currently implemented.

## 3. Proposed planner purpose

A future planner may only:

- validate a bounded request;
- accept a governed internal row or bounded identity inputs;
- invoke or consume read-only inspection evidence;
- verify current artifact state;
- verify deterministic filename and metadata;
- resolve a server-controlled archive-root identity;
- derive a deterministic bounded destination-relative identifier;
- validate path components without creating paths;
- classify destination and collision state from supplied or separately produced read-only evidence;
- evaluate documented eligibility gates; and
- return a bounded non-mutating plan with every mutation flag false.

The preferred architecture is the smallest-authority pure planning function over a validated artifact-inspection result, validated server configuration, and bounded destination-inspection result. It should not depend on HTTP, a dashboard, browser state, or filesystem write capability.

## 4. Strict non-mutating invariant

The planner must perform no directory creation, file creation, write-open, temporary-file creation, copy, move, rename, finalization, overwrite, deletion, removal, quarantine, deactivation, restoration, lifecycle persistence, audit persistence, queue write, or ledger write. Bounded read-only filesystem inspection is acceptable only where separately authorised. The planner must never create an archive root or destination parent.

## 5. Proposed adapter boundary

The current inspection adapter proves deterministic, read-only inspection of the server-derived active target and returns bounded states and metadata. It is evidence for a planner input, not an archive planner. The safest future boundary is:

1. a pure function over normalized inspection evidence and server-derived configuration;
2. an optional separately authorised read-only destination-inspection capability producing a bounded destination classification; and
3. no HTTP or dashboard dependency.

The planner should consume, rather than authenticate or persist, external authorization and audit-capability evaluations. A separate readiness assessment is required before implementing destination inspection.

## 6. Proposed inputs and prohibited inputs

Bounded inputs may include equivalents of: governed row; normalized artifact inspection result; `requested_action=archive_plan`; `archive_root_id`; `archive_root_version`; `archive_policy_id`; expected artifact state; expected filename; expected SHA-256; expected size; expected page count; request ID; idempotency key; bounded authorization evaluation; approval ID where required; audit-sink availability; and bounded destination-inspection result.

The archive-root identity, policy, current artifact evidence, and authorization result must be server-derived or independently verified. Caller input may request planning but may not select a root path or alter expected evidence.

Reject `source_path`, `archive_path`, `destination_path`, absolute paths, arbitrary filename, arbitrary directory, wildcard, glob, recursive flag, overwrite, force, skip validation, customer directory, arbitrary report content, raw PDF bytes, caller-selected audit sink, and caller-selected archive-root path.

## 7. Input schema readiness

The contracts sufficiently identify the required conceptual fields, identity binding, metadata binding, request identity, approval binding, and idempotency binding. They do not yet define one planner-specific normalized schema with exact types, bounds, optional fields, unexpected-field rejection, canonicalization rules, versioning, or error precedence. This is a blocker to implementation, not to documentation.

## 8. Governed-row eligibility

The fixture and proof sufficiently establish entry gates: fixture mode enabled; accepted fixture source; fixture ID; fixture-only; internal-only; test-fixture-only; report ID; report version; governed classification; internal warnings; customer-ready false; customer-release false; and queue-write false. The source fixture is `closed_loop_governed_local_fixture_v1`, with internal report `internal_fixture_report_closed_loop_v1` and version `DRAFT_INTERNAL_FIXTURE_v1`.

The planner must reject missing, false, contradictory, stale, or unexpected governance fields. Fixture evidence remains fictional and internal/test-only; it is not production or customer authority.

## 9. Current artifact-state readiness

Only `ACTIVE_INTERNAL_TEST_ARTIFACT` may be archive-eligible. `ABSENT`, `BLOCKED_ARTIFACT`, corrupt, mismatched, invalid-signature, parse-failure, identity-mismatch, and forbidden-release-claim results must block. The planner must not infer eligibility from file existence or UI state.

## 10. Inspection-evidence contract

Planning evidence must include deterministic filename; SHA-256; file size; page count; PDF signature result; parse result; fixture/report identity; classification; warnings; current artifact state; source boundary ID; `inspection_completed=true`; and all mutation flags false. The current inspection response supplies most artifact metadata and safety flags, but a planner-specific normalized input contract is still required for source boundary ID, explicit parse/signature fields in every state, warning completeness, current-state semantics, field bounds, and immutable evidence binding.

## 11. Archive-root identity readiness

A future bounded configuration object should contain `archive_root_id`, `archive_root_version`, `archive_root_classification`, `configured`, `enabled`, `absolute`, `server_controlled`, `customer_isolated`, `source_isolated`, `link_safe`, and `policy_id`. The absolute root is an internal validation attribute and must never be returned to callers.

Contract readiness is PARTIALLY_READY. Configuration readiness is NOT_READY: no actual root is approved or configured. Implementation readiness is NOT_READY until ownership, version, isolation, platform support, and server configuration are approved.

## 12. Destination derivation readiness

The deterministic design is:

`archive root identity -> sanitized fixture ID -> sanitized report ID -> sanitized report version -> deterministic original filename`

The structure is sufficiently specified at the identity level, but exact sanitization, normalization, allowed alphabet, maximum component and relative-path lengths, case behavior, and collision handling remain unresolved. Those decisions block planner implementation.

## 13. Sanitization readiness

`PARTIALLY_DEFINED`

The contracts require rejection or deterministic normalization of separators, traversal, drive prefixes, UNC, ADS/colon syntax, control characters, reserved Windows names, trailing spaces and periods, unsafe Unicode, excessive lengths, and target-filesystem-prohibited characters. Rejection is preferred where normalization could lose identity. Unresolved decisions are the Unicode normalization form, exact accepted alphabet, case policy, component limits, relative-path limit, normalization-versus-rejection matrix, and collision policy after normalization.

A future planner must produce `invalid_path_component`, `reserved_path_component`, `path_component_too_long`, or `identity_normalization_collision` without selecting an alternate destination.

## 14. Destination-relative identifier

A planner may return only a bounded relative identifier equivalent to:

`sanitized_fixture_id/sanitized_report_id/sanitized_report_version/deterministic_filename`

It must have no leading separator, drive, UNC prefix, `.` or `..`, unrestricted root path, or unbounded length. It must be deterministic and identity-bound. No absolute source, archive-root, destination, temporary, customer, or unrelated filesystem path may be returned.

## 15. Destination-state evaluation

The lowest-authority design is for a pure planner to consume a separately produced bounded destination-inspection classification. It should not scan directories or perform destination inspection itself. A read-only destination-inspection capability requires its own readiness assessment and proof. Missing destination evidence must produce `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION` or `destination_evidence_missing`, not a guessed absent state.

## 16. Collision-classification readiness

The design sufficiently defines `DESTINATION_ABSENT`, `IDENTICAL_ARCHIVE_PRESENT`, `CONFLICTING_ARCHIVE_PRESENT`, `DESTINATION_NON_REGULAR`, `DESTINATION_LINK_OR_REPARSE`, `DESTINATION_DIRECTORY_COLLISION`, `DESTINATION_OUTSIDE_APPROVED_ROOT`, `SOURCE_DESTINATION_SAME`, `IDENTITY_NORMALIZATION_COLLISION`, and `IDEMPOTENCY_CONFLICT`.

A pure planner can classify these from complete supplied evidence without mutation. It cannot conclusively establish real filesystem resolution, link/reparse state, root nesting, hard-link identity, or concurrent changes without a separate read-only capability. No overwrite, suffix, alternate destination, cleanup, or retry may be inferred.

## 17. Source/destination separation readiness

The required evidence is `source_boundary_id`, archive boundary ID, distinctness, root-nesting result, relative-identity result, and same-path result. Lexical, resolved, case, Unicode, link/reparse, mount, and filesystem-identity checks requiring actual resolution cannot be conclusively completed by a pure function alone. Ambiguous or missing evidence must block or require destination inspection.

## 18. Authorization and audit scope

The first planner should consume a bounded prior authorization evaluation result and should not authenticate actors, implement roles, sessions, approvals, or separation of duties. It should not claim authorization from a supplied approval ID alone. The planner may require `audit_sink_available` or an equivalent bounded capability result and may generate an audit-event plan without persistence. No audit event may be durably written by the planner.

`ARCHIVE_PLAN_REQUIRES_AUTHORIZATION` and `ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY` remain valid outcomes when those external gates are absent.

## 19. Request and idempotency readiness

Request ID and idempotency key are conceptually specified but require a planner-specific canonical binding. The binding must cover action; fixture/report/version; artifact state; filename; SHA-256; size; page count; archive root ID/version; archive policy; destination-relative identity; and authorization or approval result where applicable. Conflicting reuse must block. Concurrency evidence is also unresolved and cannot be silently assumed.

## 20. Proposed plan states

Design-only, non-persisted outcomes are:

- `ARCHIVE_PLAN_READY`;
- `ARCHIVE_PLAN_BLOCKED`;
- `ARCHIVE_ALREADY_SATISFIED`;
- `ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION`;
- `ARCHIVE_PLAN_REQUIRES_AUTHORIZATION`; and
- `ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY`.

These are response classifications, not lifecycle states, permissions, execution approvals, or persisted transitions.

## 21. Proposed plan response

A bounded response may contain `ok`, `status`, `requested_action`, fixture/report/version, current artifact state, proposed state, filename, expected SHA-256, expected size, expected page count, source boundary ID, archive root ID/version, archive policy ID, destination-relative ID, destination status, collision classification, source/destination distinctness, authorization status, audit availability, planning authorization, `execution_authorized=false`, `action_performed=false`, request ID, idempotency key, approval ID where applicable, blocked reason, and safety flags.

It must contain no unrestricted path, raw bytes, complete PDF text, customer directory, secret, credential, or unrelated filesystem entry.

## 22. Deterministic blocked reasons

The future normalized registry should include the requested reasons: `invalid_plan_contract`, `unexpected_plan_fields`, `fixture_governance_blocked`, `artifact_state_not_archive_eligible`, `artifact_identity_mismatch`, `filename_mismatch`, `sha256_mismatch`, `file_size_mismatch`, `page_count_mismatch`, `signature_validation_failed`, `parse_validation_failed`, `classification_mismatch`, `internal_warning_missing`, `forbidden_release_claim_present`, `archive_root_missing`, `archive_root_disabled`, `archive_root_invalid`, `archive_root_identity_mismatch`, `archive_policy_missing`, `sanitization_policy_unresolved`, `invalid_path_component`, `identity_normalization_collision`, `destination_evidence_missing`, `source_destination_same`, `archive_destination_collision`, `destination_link_or_reparse`, `destination_non_regular`, `authorization_not_satisfied`, `approval_not_satisfied`, `audit_capability_unavailable`, `idempotency_conflict`, `concurrency_evidence_missing`, and `planning_not_authorized`.

The registry is not yet normalized into one versioned implementation contract.

## 23. Safety flags and purity

Every future plan must preserve:

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

For identical validated inputs, output must be deterministic, side-effect free, independent of browser state, current working directory, wall-clock time except supplied timestamps, randomness, directory scans, newest-file behavior, and mutable global state.

## 24. Testing readiness

Focused tests are feasible after the normalized input contract is locked. They should prove valid plan; absent and blocked artifact rejection; identity and metadata mismatch; invalid archive-root identity; unsafe component; normalization collision; destination absent; identical archive; conflicting archive; authorization missing; audit capability missing; idempotency conflict; all mutation flags false; no filesystem creation or modification; no absolute-path disclosure; and deterministic repeated output. Direct proof must verify no writes and no path disclosure. Endpoint and browser tests are out of scope until their separate readiness gates pass.

## 25. Planner implementation blockers

Evidence-supported blockers are:

- no approved or configured archive-root identity;
- unresolved rejection, normalization, Unicode, case, reserved-name, ADS, platform, and length policy;
- planner-specific normalized inspection and destination-evidence schema not locked;
- source/archive boundary IDs and real-resolution evidence contract unresolved;
- authorization-result input and approval binding unresolved;
- audit-capability input unresolved;
- concurrency and stale-evidence input unresolved; and
- versioned blocked-reason registry and unexpected-field policy unresolved.

No unsupported blocker is asserted.

## 26. Endpoint readiness

`NOT_READY_FOR_ENDPOINT`

A backend planning endpoint remains blocked until a pure planner is implemented and proven, the route request contract is reviewed, fixture/environment gates are defined, path disclosure is reviewed, an endpoint test exists, and direct planner proof passes. No endpoint is implemented or authorized by this assessment.

## 27. Dashboard readiness

`NOT_READY_FOR_DASHBOARD`

A dashboard planning control remains blocked until planner and route proof exist, endpoint live proof passes, UI selection and state contracts are assessed, authority confusion is excluded, execution-looking language is absent, and stale-state clearing is designed and proven. No dashboard control is implemented or authorized.

## 28. Mutation readiness

`NOT_READY_FOR_ARCHIVE_MUTATION`

Mutation remains blocked by no approved archive root, no filesystem execution implementation, no approved audit sink, no approved authorization system, no concurrency mechanism, no partial-copy recovery, no finalized platform-safe copy strategy, no live planning proof, and no archive implementation-readiness assessment. Copy-and-retain is the conservative future position; coupled removal remains prohibited.

## 29. Residual-risk assessment

| Surface | Residual risk |
|---|---|
| Docs-only planner design | ACCEPTABLE |
| Pure planner implementation | ACCEPTABLE_WITH_BLOCKERS |
| Planning endpoint | UNACCEPTABLE |
| Dashboard planning control | UNACCEPTABLE |
| Archive mutation | UNACCEPTABLE |

## 30. Readiness matrix

| Area | Finding |
|---|---|
| Contract specificity | READY |
| Bounded input schema | PARTIALLY_READY |
| Deterministic output | PARTIALLY_READY |
| Source evidence | READY |
| Archive-root identity | PARTIALLY_READY |
| Sanitization policy | PARTIALLY_READY |
| Destination identity | PARTIALLY_READY |
| Collision evidence | PARTIALLY_READY |
| Authorization boundary | PARTIALLY_READY |
| Audit boundary | PARTIALLY_READY |
| Idempotency | PARTIALLY_READY |
| Concurrency evidence | NOT_READY |
| Path non-disclosure | READY |
| Safety flags | READY |
| Focused-test feasibility | PARTIALLY_READY |

## 31. Smallest safe next slice

Recommend exactly one next slice: a docs-only blocker-resolution assessment that locks the planner-specific normalized input/output schema, archive-root identity source, sanitization/platform policy, destination-inspection evidence, authorization/audit capability inputs, concurrency evidence, and blocked-reason registry. Do not recommend an endpoint, dashboard control, or mutation.

## 32. Recommended sequencing

A. Archive planning-adapter readiness assessment.
B. Resolve planner-specific blockers.
C. Pure non-mutating archive-plan adapter.
D. Focused planner tests.
E. Direct non-mutating proof.
F. Planning endpoint readiness assessment.
G. Planning endpoint and focused route test.
H. Live planning route proof.
I. Dashboard planning-control readiness assessment.
J. Dashboard control and focused test.
K. Live dashboard planning proof.
L. Archive mutation implementation-readiness assessment.
M. Separately authorised copy-and-retain archive implementation.

## 33. Explicit non-authorization

This assessment does not authorize planner, endpoint, dashboard, archive-root configuration, directory creation, destination-inspection implementation, temporary-file creation, copy, archive, finalization, source removal, quarantine, deactivation, restoration, deletion, secure deletion, rename, movement, overwrite, audit persistence, lifecycle persistence, customer-ready classification, customer release, production storage, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 34. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_ARCHIVE_PLANNING_ADAPTER_READINESS=READY_WITH_BLOCKERS`
