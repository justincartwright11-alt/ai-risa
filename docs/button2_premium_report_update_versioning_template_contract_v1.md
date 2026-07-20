# Button 2 Premium Report Update Versioning Template Contract v1

## 1. Purpose
Define the contract shape Button 2 must eventually use for premium report update/versioning records.

This is contract design only. It grants no implementation authority.

## 2. Release Boundary
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY
- CUSTOMER_RELEASE_AUTHORIZED=NO
- PUBLIC_PUBLISHING_AUTHORIZED=NO
- PRODUCTION_LAUNCH_AUTHORIZED=NO
- AUTOMATED_DELIVERY_AUTHORIZED=NO
- LEARNING_ACTIVATION_AUTHORIZED=NO

## 3. Source Design Dependency
This contract depends on the versioning-template design defined in `docs/button2_premium_report_update_versioning_template_design_v1.md`.

The contract must remain aligned with that design's rules for report version labels, update events, changed section tracking, source-map refresh, delivery holds, and fail-closed customer delivery boundaries.

## 4. Contract Authority
This document defines the required contract shape only.

It does not authorize runtime implementation, automatic delivery, PDF generation changes, customer release, learning activation, or production deployment.

Any future implementation must satisfy this contract and remain within internal-only governance until separately authorized.

## 5. Contract Envelope
Every Button 2 premium report update/versioning record must include the following contract envelope fields:

- contract_type
- contract_version
- schema_name
- schema_version
- created_at_utc
- report_id
- matchup_id
- event_id
- fighter_a
- fighter_b
- report_version
- previous_report_version
- source_watch_timestamp
- latest_update_timestamp
- changed_sections
- unchanged_sections
- source_map_status
- confidence_status
- uncertainty_status
- delivery_status
- operator_review_status
- operator_delivery_approval
- final_pdf_sha256
- release_scope_decision
- customer_release_authorized
- public_publishing_authorized
- production_launch_authorized
- automated_delivery_authorized
- learning_activation_authorized

The envelope exists so the record can describe both report state and release-governance state in the same object.

## 6. Required Metadata Fields
At minimum, the contract must carry identifying and timing metadata sufficient to trace the report through its pre-fight lifecycle.

Required metadata fields include:

- contract_type
- contract_version
- schema_name
- schema_version
- created_at_utc
- report_id
- matchup_id
- event_id
- fighter_a
- fighter_b

These fields must never be omitted because downstream review, comparison, and delivery logic depend on stable record identity.

## 7. Report Version Fields
The contract must include the following version-state fields:

- report_version
- previous_report_version

Supported version labels must include:

- DRAFT_INTERNAL_v1
- DRAFT_INTERNAL_UPDATED_v2
- DRAFT_INTERNAL_UPDATED_v3
- DELIVERY_READY_PENDING_OPERATOR_APPROVAL
- CUSTOMER_DELIVERY_APPROVED
- DELIVERED_TO_CUSTOMER
- DELIVERY_REVOKED_OR_SUPERSEDED

The contract must preserve prior version lineage so that Button 3 can later identify the active final pre-fight report version.

## 8. Update Event Fields
The contract must support update-event information tied to the report refresh process.

Required update-event fields include:

- source_watch_timestamp
- latest_update_timestamp
- report_version
- previous_report_version
- delivery_status

The implementation may later extend this with event-specific companion records, but the core contract must still expose enough data to show when the last upstream watch occurred and when the latest material update landed.

## 9. Changed Section Map Fields
The contract must represent section-level change state using:

- changed_sections
- unchanged_sections

These fields must support a future changed section map that identifies which premium report sections were refreshed, which remained stable, and which require reviewer attention after pre-fight updates.

## 10. Source Map Refresh Fields
The contract must represent source-map refresh state using:

- source_map_status
- source_watch_timestamp
- latest_update_timestamp

These fields must allow future implementations to record whether the source map is current, stale, conflicted, or blocked by unresolved upstream evidence.

## 11. Confidence and Uncertainty Fields
The contract must represent analytical state refresh using:

- confidence_status
- uncertainty_status

These fields must support future enforcement that confidence and uncertainty language are refreshed whenever a material evidence update affects the report.

## 12. Delivery Status Fields
The contract must represent delivery progression using:

- delivery_status
- release_scope_decision
- customer_release_authorized
- public_publishing_authorized
- production_launch_authorized
- automated_delivery_authorized

Delivery status values must include:

- NOT_FOR_CUSTOMER
- INTERNAL_DRAFT
- WATCH_ACTIVE
- UPDATE_PENDING_REVIEW
- REPORT_HOLD
- DELIVERY_READY_PENDING_OPERATOR_APPROVAL
- CUSTOMER_DELIVERY_APPROVED
- DELIVERED
- DELIVERY_REVOKED_OR_SUPERSEDED

## 13. Operator Review Fields
The contract must represent operator gate state using:

- operator_review_status
- operator_delivery_approval

These fields exist to ensure that internal draft refresh and customer delivery approval are not treated as the same control point.

## 14. Final PDF Integrity Fields
The contract must represent final delivery artifact integrity using:

- final_pdf_sha256

This field is required so any approved delivery can be tied to a specific immutable PDF artifact rather than a floating report state.

## 15. Fail-Closed Validation Rules
The contract must fail closed and block customer delivery when any of the following is true:

- operator approval is missing
- source watch is stale
- material update is pending review
- fighter identity is unresolved
- event status is uncertain
- opponent changes
- ruleset or scheduled rounds conflict exists
- source trust is below threshold
- final PDF hash is missing
- release scope is not approved for customer delivery

The contract must be interpreted so that missing or contradictory gate data blocks promotion instead of allowing inferred approval.

## 16. Prohibited Contract States
The contract must prohibit the following states:

- `customer_release_authorized=YES` while `RELEASE_SCOPE_DECISION=INTERNAL_ONLY`
- `automated_delivery_authorized=YES` while `operator_delivery_approval` is missing
- `DELIVERED` without `final_pdf_sha256`
- `DELIVERED` without `operator_delivery_approval`
- `CUSTOMER_DELIVERY_APPROVED` with unresolved material update
- `LEARNING_ACTIVATION_AUTHORIZED=YES` inside this Button 2 contract

These states are invalid even if other fields appear populated.

## 17. Future Implementation Test Requirements
Future implementations must add tests that verify all of the following. These tests are required later but are not implemented in this slice:

- required fields cannot be missing
- stale reports cannot be delivery-ready
- unresolved updates force `REPORT_HOLD`
- `INTERNAL_ONLY` blocks customer delivery
- final PDF hash is required before delivered status
- previous report version is preserved
- changed section map is generated
- source map refresh status is recorded
- Button 3 can identify the active final pre-fight report version

## 18. Acceptance Criteria
This contract is accepted when:

- it defines the contract envelope
- it defines the required metadata fields
- it defines the report version fields
- it defines the update event fields
- it defines the changed section map fields
- it defines the source map refresh fields
- it defines the confidence and uncertainty fields
- it defines the delivery status fields
- it defines the operator review fields
- it defines the final PDF integrity fields
- it defines fail-closed validation rules
- it defines prohibited contract states
- it defines future implementation test requirements

## 19. Slice Integrity
- DOCS_CHANGED=YES
- CODE_CHANGED=NO
- PDF_CHANGED=NO
- DATA_CHANGED=NO
- CUSTOMER_RELEASE_AUTHORIZED=NO
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY