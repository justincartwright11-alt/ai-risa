# Button 2 Governed Internal PDF Artifact Lifecycle Audit and Authorization Contract v1

## 1. Executive status

`AUDIT_AUTHORIZATION_CONTRACT_COMPLETE`

This document defines governance evidence required before any governed internal PDF archive or removal action could be planned or executed. Contract completion does not authorise implementation, planning, mutation, persistence, deletion, quarantine, copying, movement, rename, overwrite, endpoint creation, UI creation, customer release, or production use.

## 2. Locked baseline

- Archive/removal contract commit: `bca19b763ef9af78c876f74db8157efd49404f5c`.
- Lifecycle reassessment commit: `90b8413ce28c0eec7d0deb2f3cee1667d755deee`.
- The fixture is fictional only.
- All referenced artifacts are internal/test-only.
- No lifecycle mutation is currently implemented.
- The current inspection chain is read-only and does not provide lifecycle authority.

## 3. Contract purpose

This design defines evidence needed to prove who requested an action, what action was requested, which artifact was targeted, why it was requested, who approved it, what evidence was expected, what evidence was observed, whether it was permitted, whether it occurred, what state resulted, and where durable audit evidence is stored. It defines governance evidence only and grants no implementation authority.

## 4. Separation of concepts

The following are independent concepts and none may substitute for another:

- **Actor identity:** the server-verified person or service identity associated with an action.
- **Authenticated session:** the bounded authenticated session under which a request is made.
- **Operator role:** a server-resolved role assigned to the actor.
- **Action permission:** an explicit permission for one requested action.
- **Approval:** an action- and artifact-bound authorization decision by an approver.
- **Acknowledgement:** action-specific confirmation that required risks and boundaries were understood.
- **Reason:** a bounded reason code, optionally accompanied by bounded text.
- **Request identity:** the server-validated request identifier and canonical request contents.
- **Idempotency:** replay handling bound to the exact request and prior result.
- **Audit event:** an immutable record of an observed governance or lifecycle event.
- **Audit persistence:** durable storage of that event in an approved lifecycle audit sink.
- **Execution result:** observed evidence of what happened and the resulting state.

A dashboard selection, generation acknowledgement, inspection success, prior proof, design document, or file existence is not any of these by implication.

## 5. Actor identity contract

A future implementation must require bounded, server-verified fields equivalent to:

- `operator_id`;
- `operator_display_name` where permitted;
- `operator_role`;
- `authentication_method`;
- `authenticated_at`;
- `session_id` or bounded session reference;
- `identity_source`; and
- `identity_verified`.

Lifecycle mutation must be anonymous-never. Free-form actor names cannot confer authority. Roles cannot be elevated by browser input. Client-supplied identity must be rejected unless independently verified by the server. Passwords, credentials, secrets, tokens, raw authentication assertions, and session secrets must never enter audit records.

## 6. Operator-role model

The following design-only role names are provisional unless separately established in repository governance:

- `internal_viewer`: inspect bounded internal fixture evidence only;
- `internal_artifact_operator`: submit bounded lifecycle requests and prepare evidence;
- `internal_archive_approver`: approve archive within assigned scope;
- `internal_removal_approver`: approve removal within assigned scope and stronger policy;
- `lifecycle_auditor`: review lifecycle audit evidence without mutation authority;
- `system_administrator`: administer approved identity, policy, or sink configuration, not automatically approve or execute actions.

Least privilege requires inspection, planning, approval, execution, and audit review to be separately mapped. A role must receive only the minimum permissions necessary. Role names, scope, inheritance, emergency access, and administrator restrictions remain open organizational decisions.

## 7. Permission contract

Future action permissions must remain distinct:

- `inspect_internal_pdf`;
- `plan_internal_pdf_archive`;
- `approve_internal_pdf_archive`;
- `execute_internal_pdf_archive`;
- `plan_internal_pdf_removal`;
- `approve_internal_pdf_removal`;
- `execute_internal_pdf_removal`;
- `review_lifecycle_audit`.

Archive and removal permissions must never be combined implicitly. Removal execution requires stronger authority than archive execution. Permanent deletion has no permission in this contract and remains blocked.

## 8. Separation of duties

Archive planning and approval should be separate permissions. Archive may use single-person approval only if an approved organizational policy explicitly permits it and the requester/approver relationship is recorded. Removal approval should require an actor separate from the requester. Removal should use two-person approval unless a separately approved policy proves an equivalent control. Permanent deletion remains blocked; any exceptional approval model is unresolved. The final organizational decision, conflict exceptions, and emergency procedure are open decisions.

## 9. Approval contract

A future approval must be bound to the exact requested action and artifact and contain fields equivalent to:

- `approval_id`;
- `approval_type`;
- `approved_action`;
- `approved_fixture_id`;
- `approved_report_id`;
- `approved_report_version`;
- `approved_expected_state`;
- `approved_expected_filename`;
- `approved_expected_sha256`;
- `approved_expected_file_size_bytes`;
- `approved_expected_page_count`;
- `approver_id`;
- `approver_role`;
- `approved_at`;
- `approval_expires_at`;
- `approval_status`;
- `approval_scope`; and
- `approval_signature` or other server-verifiable evidence where applicable.

Approval is invalid when missing, expired, revoked, action-mismatched, artifact-mismatched, state-mismatched, metadata-mismatched, role-insufficient, reused outside scope, created after execution, or sourced unverifiably.

## 10. Explicit acknowledgement

Acknowledgement must be action-specific and versioned. It may not be inherited from generation acknowledgement or dashboard selection.

Archive acknowledgement must confirm: the target is a governed internal fixture only; archive does not release anything to customers; the active source will be retained under the approved archive design; and overwrite is prohibited.

Removal acknowledgement must additionally confirm: the active artifact may become unavailable; evidence-preservation requirements; the exact removal semantics; restoration limitations; and that permanent deletion is not authorised unless separately approved.

## 11. Reason-code registry

Archive reason codes may include:

- `proof_preservation`;
- `retention_transfer`;
- `superseded_internal_draft`;
- `governed_lifecycle_closure`;
- `controlled_evidence_copy`.

Removal reason codes may include:

- `approved_retention_expiry`;
- `verified_duplicate_after_archive`;
- `approved_fixture_cleanup`;
- `governance_directed_deactivation`;
- `approved_quarantine`.

The registry must reject vague codes such as `cleanup`, `old`, `unwanted`, `bad`, or `fix`. Registry ownership and final values are unresolved.

## 12. Reason-text rules

Optional reason text must be length-bounded, retained in the audit record, and must not contain credentials, secrets, unrestricted filesystem paths, unnecessary personal information, or arbitrary report content. Text cannot replace the required reason code.

## 13. Request identity contract

A future request must require:

- `request_id`;
- `idempotency_key`;
- `requested_action`;
- `requested_at`;
- requester identity;
- fixture and report identity;
- expected lifecycle state;
- expected filename;
- expected SHA-256;
- expected size;
- expected page count;
- approval ID;
- reason code; and
- explicit action acknowledgement.

Request IDs and idempotency keys must be server-validated. The server must canonicalize the request before planning or execution. Canonical data must exclude absolute source paths, destination paths, credentials, raw PDF bytes, arbitrary report content, and unbounded user text. Caller-controlled paths, wildcards, overwrite flags, force flags, and validation bypasses are prohibited.

## 14. Authorization evaluation sequence

The required order is:

1. Validate fixture mode and governed fixture source.
2. Authenticate the actor.
3. Resolve the server-side role.
4. Validate the requested action.
5. Validate action permission.
6. Validate exact artifact identity.
7. Validate current artifact state.
8. Validate expected metadata.
9. Validate approval.
10. Validate acknowledgement.
11. Validate reason.
12. Validate request ID and idempotency key.
13. Validate audit sink availability.
14. Permit planning or execution only when every gate passes.

No later gate may compensate for an earlier failure. Design-only bounded outcomes are `AUTHORIZED_FOR_PLANNING`, `AUTHORIZED_FOR_ARCHIVE_EXECUTION`, `AUTHORIZED_FOR_REMOVAL_EXECUTION`, and `AUTHORIZATION_BLOCKED`. This document implements none of them.

## 15. Audit-event taxonomy

Design-only event types are:

- `lifecycle_request_received`;
- `lifecycle_authorization_evaluated`;
- `lifecycle_authorization_blocked`;
- `archive_plan_created`;
- `archive_execution_started`;
- `archive_execution_completed`;
- `archive_execution_blocked`;
- `removal_plan_created`;
- `removal_execution_started`;
- `removal_execution_completed`;
- `removal_execution_blocked`;
- `lifecycle_replay_detected`; and
- `lifecycle_audit_persistence_failed`.

## 16. Audit-event schema

A future event must contain fields equivalent to:

- `event_id`, `event_version`, `event_type`, and `event_timestamp`;
- `request_id`, `idempotency_key`, and `correlation_id`;
- `fixture_id`, `report_id`, and `report_version`;
- `requested_action`, requester ID/role, approver ID/role, and `approval_id`;
- `reason_code` and `acknowledgement_version`;
- `previous_state` and `resulting_state`;
- expected and observed filename;
- expected and observed SHA-256;
- expected and observed file size;
- expected and observed page count;
- source boundary ID and destination boundary ID where applicable;
- authorization result, action performed, and blocked reason;
- safety flags;
- runtime version or bounded build identifier; and
- `completed_at` where applicable.

Events must not contain passwords, API keys, session tokens, raw authentication assertions, unrestricted absolute paths, complete PDF text, raw PDF bytes, unrelated customer information, or unnecessary personal information.

## 17. Audit immutability and durability

Future audit persistence must support append-only records, immutable event IDs, event ordering or sequence, integrity validation, no silent overwrite, and no silent deletion. Corrections must use compensating events rather than editing prior events. No database technology is prescribed.

Intent must be durably persisted before irreversible execution where required. A completion event must be persisted after execution. Failures must remain visible and bounded, with recoverable correlation between intent and result. Lifecycle action must be blocked when mandatory audit intent cannot be durably stored.

## 18. Audit sink contract

An approved lifecycle audit sink must be a separate bounded system with server-configured sink identity, availability status, write authorization, schema/version validation, append-only behavior, durable event IDs, bounded failure reasons, and no caller-controlled sink selection. No approved sink is currently implemented.

The customer queue, PDF-generation result panel, application console logs, report ledger, accuracy ledger, GCID, learning store, calibration store, and browser local state must not be reused implicitly as the lifecycle audit sink.

## 19. Audit failure policy

Fail closed when the sink is unavailable, schema is unsupported, event write is rejected, a durable event ID is not returned, the intent event cannot be stored, the completion event cannot be correlated, or audit integrity validation fails.

Distinguish failure before mutation, failure during mutation, and failure after filesystem action but before completion audit. The last case is a critical partial-mutation incident requiring a separately designed recovery policy; it is not success and must not be silently retried.

## 20. Before-action audit intent

Before execution, the durable intent event must identify the exact canonical request, actor, role, approval, expected artifact evidence, expected transition, source and destination boundary IDs where applicable, idempotency key, and authorization result. No mutation may begin without this evidence.

After execution, the result must record observed metadata, resulting state, source and destination existence, action result, blocked reason where applicable, completion timestamp, linkage to the intent event, and safety flags. Authorization or validation failures should create a bounded blocked event where safe, without credentials or unrestricted paths.

## 21. Idempotency, replay, and expiry

Every replay evaluation must use request identity, action, artifact identity, expected metadata, approval, and prior audit result. Exact replay may return the prior bounded result. Conflicting reuse must be blocked and audited. Request expiry, approval expiry, acknowledgement-version compatibility, stale metadata rejection, replay conflict, and revoked approval behavior must be explicit. No expired or revoked approval may authorise execution.

## 22. Concurrency and TOCTOU controls

Authorization must be revalidated when an action begins. Prior authorization is insufficient if metadata or state changes, another lifecycle action starts, approval expires or is revoked, or the audit sink becomes unavailable.

Immediate pre-action revalidation must cover actor session, role and permission, approval, acknowledgement, artifact identity, lifecycle state, filename, SHA-256, size, page count, classification, warnings, and source/destination boundaries. Only one active lifecycle action may exist for the deterministic artifact. The locking mechanism is unresolved; stale authorization must fail closed.

## 23. Authorization response contract

A bounded future response may contain:

- `ok` and `authorization_status`;
- `requested_action` and `fixture_id`;
- `report_id` and `report_version`;
- `operator_id` and `operator_role`;
- `approval_id`, `request_id`, and `idempotency_key`;
- expected state;
- `authorization_expires_at`;
- `blocked_reason`;
- `planning_authorized` and `execution_authorized`;
- `audit_sink_available`;
- `action_performed`; and
- safety flags.

It must not return credentials, secrets, raw PDF content, or unrestricted paths.

## 24. Deterministic blocked reasons

Bounded reasons include:

`authentication_required`, `actor_identity_unverified`, `operator_role_invalid`, `action_permission_missing`, `separation_of_duties_violation`, `approval_missing`, `approval_invalid`, `approval_expired`, `approval_revoked`, `approval_scope_mismatch`, `acknowledgement_missing`, `acknowledgement_version_invalid`, `reason_code_missing`, `reason_code_invalid`, `request_id_invalid`, `request_expired`, `idempotency_key_invalid`, `idempotency_conflict`, `fixture_governance_blocked`, `artifact_identity_mismatch`, `lifecycle_state_mismatch`, `artifact_metadata_mismatch`, `audit_sink_unavailable`, `audit_schema_invalid`, `audit_intent_write_failed`, `concurrency_conflict`, `authorization_revalidation_failed`, and `permanent_deletion_not_authorized`.

## 25. HTTP design boundary

A future endpoint may classify responses deterministically as follows: `200` for authorization evaluation or an identical replay result; `400` for malformed request contract; `401` for unauthenticated actor; `403` for role, permission, approval, acknowledgement, or fixture-governance block; `409` for identity, state, concurrency, replay, or separation-of-duties conflict; `422` for metadata, reason, policy, or evidence validation failure; `503` for audit sink unavailability or persistence block; and `500` only for unexpected internal failure. No endpoint is implemented or authorised by this document.

## 26. Safety flags

Future planning and authorization responses must preserve:

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

## 27. Threat analysis and controls

- **Forged identity or client role elevation:** require server authentication and server-side role resolution; reject client authority fields.
- **Stolen, replayed, expired, or substituted approval:** bind approval to exact action, artifact, metadata, scope, expiry, and server-verifiable evidence; revalidate immediately.
- **Acknowledgement bypass:** require a versioned action-specific acknowledgement independent of generation or selection state.
- **Vague or malicious reason:** use an owned bounded registry and bounded text with secret, path, personal-data, and length controls.
- **Request replay or idempotency collision:** canonicalize and bind request identity, action, artifact evidence, approval, and prior result; block conflicts.
- **Audit tampering or bypass:** use a separate append-only sink, durable IDs, integrity validation, intent-before-action, and compensating events.
- **Sink substitution or sensitive-data leakage:** server-select the sink and prohibit credentials, raw bytes, full PDF text, unrestricted paths, and unrelated personal data.
- **Execution without durable intent:** fail closed before mutation when intent cannot be persisted.
- **Mutation followed by audit failure:** classify as a critical partial-mutation incident and require separately designed recovery.
- **Requester/approver collusion:** enforce separation of duties and stronger removal approval; retain both identities.
- **Stale authorization and TOCTOU:** revalidate actor, approval, state, metadata, boundaries, and sink immediately before action.

## 28. Open decisions

The following remain unresolved: authentication provider; canonical actor identifier; final operator roles; role-to-permission mapping; archive approval model; removal dual-approval model; approval expiry duration; acknowledgement wording and versioning; reason-code registry ownership; audit sink technology; audit-event retention duration; audit integrity mechanism; audit access policy; recovery after partial mutation; legal or governance hold authority; concurrency mechanism; removal semantics; retention policy; approved archive root; and planning-adapter readiness criteria.

## 29. Implementation-readiness blockers

Implementation remains blocked until at least the following are approved or completed: actor authentication source; role model; permission mapping; approval workflow; separation-of-duties policy; acknowledgement wording; reason-code registry; audit sink; audit schema/version; audit durability and failure behavior; retention and access policy; partial-mutation recovery; lifecycle threat review; and a separate planning-adapter readiness assessment.

## 30. Smallest safe next slice

Recommend exactly one docs-only next slice: **Button 2 governed internal PDF archive destination and collision contract design**.

Proposed file:

`docs/button2_governed_internal_pdf_artifact_archive_destination_collision_contract_v1.md`

Do not recommend implementation.

## 31. Recommended sequencing

A. Lifecycle audit and authorization contract.

B. Archive destination and collision contract.

C. Removal semantics and retention policy.

D. Lifecycle threat review.

E. Lifecycle planning-adapter readiness assessment.

F. Pure non-mutating lifecycle authorization/plan adapter.

G. Focused planning tests.

H. Live non-mutating planning proof.

I. Separate mutation implementation-readiness assessment.

J. Separately authorised archive implementation.

K. Removal implementation only after archive and stronger controls are proven.

## 32. Explicit non-authorization

This document does not authorise authentication implementation, role or permission implementation, approval implementation, audit sink implementation, audit persistence, archive planning implementation, archive implementation, removal planning implementation, removal implementation, deletion, quarantine, copy, movement, rename, overwrite, lifecycle endpoints, lifecycle UI, customer-ready classification, customer release, production storage, queue or ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 33. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_LIFECYCLE_AUDIT_AUTHORIZATION=CONTRACT_DESIGN_COMPLETE`
