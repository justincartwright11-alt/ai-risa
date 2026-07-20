# Button 2 Premium Report Update Versioning Template Design v1

## 1. Purpose
Define how Button 2 should manage premium report drafts, pre-fight update versions, changed sections, source-map refresh, internal holds, and delivery-ready status without automatically sending reports to customers.

## 2. Release Boundary
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY
- CUSTOMER_RELEASE_AUTHORIZED=NO
- PUBLIC_PUBLISHING_AUTHORIZED=NO
- PRODUCTION_LAUNCH_AUTHORIZED=NO
- AUTOMATED_DELIVERY_AUTHORIZED=NO
- LEARNING_ACTIVATION_AUTHORIZED=NO

## 3. Source Design Dependency
This design depends on the pre-fight update-watch governance defined in `docs/pre_fight_report_update_watch_and_delivery_gate_design_v1.md`.

Button 2 may only refresh, version, hold, or promote a premium report draft when the upstream source-watch design has provided a current update record, impact classification, and trust-aware freshness state.

## 4. Button 2 Placement
Button 2 remains the premium report generation and refresh layer inside the three-button model.

It does not replace Button 1 source verification, and it does not replace Button 3 official result comparison.

Its role in this design is to:

- generate the first internal premium report draft
- preserve historical draft versions
- refresh content when verified pre-fight updates arrive
- expose changed and unchanged sections
- hold or promote delivery readiness based on source and operator state

## 5. Report Version Labels
Button 2 must support the following report version labels:

- DRAFT_INTERNAL_v1
- DRAFT_INTERNAL_UPDATED_v2
- DRAFT_INTERNAL_UPDATED_v3
- DELIVERY_READY_PENDING_OPERATOR_APPROVAL
- CUSTOMER_DELIVERY_APPROVED
- DELIVERED_TO_CUSTOMER
- DELIVERY_REVOKED_OR_SUPERSEDED

These labels are stateful workflow markers, not marketing labels, and they must reflect the current internal governance state of the report rather than only the latest file name.

## 6. Report Metadata Fields
Every Button 2 premium report draft or refreshed version must carry the following template output fields:

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

These fields must travel with the draft record so that a reviewer can determine which version existed, what changed, whether the source map is current, and whether delivery is allowed.

## 7. Update Event Record
Each refresh cycle must produce a Button 2 update event record that captures the trigger and the effect of the refresh.

The update event record should include:

- update_event_id
- report_id
- triggering_source
- triggering_update_classification
- triggering_impact_level
- source_watch_timestamp
- latest_update_timestamp
- prior_report_version
- resulting_report_version
- operator_review_required
- delivery_hold_applied
- notes

The record exists to preserve an auditable chain from incoming evidence change to resulting draft state.

## 8. Changed Section Map
Button 2 must maintain a changed section map that identifies which premium report sections were refreshed and which remained stable after each update.

The changed section map should show:

- section name
- changed or unchanged state
- reason for change
- upstream source or event trigger
- recalculation required or not required
- operator attention flag

This map is required so that the operator does not need to diff the full report blindly after each update.

## 9. Source Map Refresh
When Button 2 refreshes a report, it must refresh the report source map for any section affected by new evidence, a corrected identity field, a ruleset change, a market-supporting note, or a fight-week observation.

The source map refresh must:

- retain prior source lineage where sections are unchanged
- replace stale section-level sourcing where updates are material
- mark unresolved source conflicts explicitly
- downgrade sections to pending or blocked when upstream evidence is incomplete

## 10. Uncertainty and Confidence Refresh
Button 2 must refresh uncertainty and confidence notes whenever pre-fight updates materially change the evidence base.

This refresh should:

- increase uncertainty when verified conflicts, incomplete weigh-in data, opponent ambiguity, or event-status instability appear
- reduce uncertainty only when new trusted evidence closes a known gap
- prevent stale confidence language from carrying forward after a material update
- keep confidence_status and uncertainty_status aligned with the current source map and changed section map

## 11. Report Hold Conditions
Button 2 must hold a report internally when any of the following is true:

- source-watch review is incomplete
- a material update is pending operator review
- the source map is stale or conflicted
- a section recalculation or projection recalibration is still pending
- fighter identity is unresolved
- event status is unresolved
- ruleset is unresolved
- opponent identity is unresolved or changed
- delivery approval has not been granted

## 12. Delivery-Ready Conditions
Button 2 may mark a report as `DELIVERY_READY_PENDING_OPERATOR_APPROVAL` only when all of the following are true:

- the latest source watch has completed
- no unresolved material update remains
- changed sections have been refreshed
- unchanged sections have been preserved intentionally
- source_map_status is current and not conflicted
- confidence_status and uncertainty_status have been refreshed
- operator review is complete
- the report is current enough for the intended delivery window

## 13. Final Customer Delivery Gate
No report may be sent automatically.

No report may be delivered without operator approval.

No stale report may be delivered.

No report with unresolved material update may be delivered.

No report with unresolved fighter identity, event status, ruleset, opponent, or source conflict may be delivered.

Final customer delivery requires:

1. a valid customer request or active order
2. a current Button 1 verified matchup state
3. a completed source watch and freshness pass
4. a Button 2 report version marked `DELIVERY_READY_PENDING_OPERATOR_APPROVAL`
5. explicit operator delivery approval
6. a recorded final PDF hash in `final_pdf_sha256`
7. a delivery status transition to `CUSTOMER_DELIVERY_APPROVED` and then `DELIVERED_TO_CUSTOMER`

## 14. Button 1 Input Dependency
Button 2 depends on Button 1 to provide trusted matchup identity, event status, participant status, and ruleset context.

Button 2 must not treat its own report text as a source of truth when Button 1 indicates unresolved identity, event, or ruleset issues.

If Button 1 marks the fight as unresolved or source trust degraded, Button 2 must hold refresh promotion and delivery readiness.

## 15. Button 3 Result-Comparison Dependency
Button 3 depends on Button 2 preserving the final active pre-fight report version so that later result comparison can identify exactly which projection and evidence state existed at fight start.

Button 2 therefore must:

- preserve previous_report_version
- preserve the changed section map per refresh event
- preserve the source and uncertainty state of the final active report version
- prevent obsolete drafts from being treated as the governing pre-fight report once superseded

## 16. Fail-Closed Rules
Button 2 must fail closed and block customer-ready promotion when:

- report_version metadata is missing or inconsistent
- previous_report_version lineage is broken
- changed_sections cannot be explained
- source_map_status is stale, incomplete, or conflicted
- confidence_status or uncertainty_status has not been refreshed after a material update
- operator_review_status is incomplete
- operator_delivery_approval is missing
- final_pdf_sha256 is missing at the point of approved delivery

## 17. Acceptance Criteria
This design is accepted when:

- it defines the report version labels
- it defines the metadata fields
- it defines the update event record
- it defines the changed section map
- it defines source-map refresh behavior
- it defines report hold conditions
- it defines delivery-ready conditions
- it defines the final customer delivery gate
- it defines Button 1 input dependency
- it defines Button 3 result-comparison dependency
- it preserves internal-only governance and fail-closed delivery behavior

## 18. Slice Integrity
- DOCS_CHANGED=YES
- CODE_CHANGED=NO
- PDF_CHANGED=NO
- DATA_CHANGED=NO
- CUSTOMER_RELEASE_AUTHORIZED=NO
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY