# Button 2 Premium Report Update Versioning Fixture Schema Test Design v1

## 1. Purpose
This document designs the fixture, schema, and targeted test boundary for future Button 2 premium report update versioning implementation readiness.

## 2. Design Boundary
This is docs-only design.

It does not authorize:

- runtime changes
- test creation
- fixture creation
- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes
- database writes

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Source Design Chain
Reference:

- docs/button2_premium_report_update_versioning_template_design_v1.md
- docs/button2_premium_report_update_versioning_template_contract_v1.md
- docs/button2_premium_report_update_versioning_template_contract_review_v1.md
- docs/pre_fight_report_update_watch_and_delivery_gate_design_v1.md

Confirm:

Button 2 report update versioning is approved for design lock only, not customer release.

## 5. Future Fixture Objective
Define a future fixture that models one internal premium report update cycle.

The fixture must represent:

- original internal draft
- update event
- changed section map
- refreshed source map
- confidence and uncertainty status
- delivery status
- operator review state
- final PDF integrity placeholder
- fail-closed customer delivery status

## 6. Proposed Future Fixture File
Design only. Do not create it.

Proposed future file:

operator_dashboard/fixtures/button2_premium_report_update_versioning_fixture_v1.json

This slice does not create that fixture file.

## 7. Required Fixture Fields
Required top-level fields:

- schema_version
- fixture_id
- report_id
- fight_id
- event_name
- fighter_a
- fighter_b
- report_version_before
- report_version_after
- update_event
- changed_section_map
- source_map_refresh
- confidence_uncertainty
- delivery_status
- operator_review
- final_pdf_integrity
- release_boundary
- prohibited_states

## 8. Update Event Required Fields
Required update_event fields:

- update_id
- update_timestamp
- update_source_type
- update_source_tier
- update_classification
- materiality
- affected_report_sections
- requires_report_regeneration
- requires_operator_review
- customer_delivery_hold_reason

## 9. Changed Section Map Required Fields
Required changed_section_map entries:

- section_id
- section_name
- prior_status
- updated_status
- change_reason
- evidence_reference
- uncertainty_note
- delivery_impact

## 10. Source Map Refresh Required Fields
Required source_map_refresh fields:

- source_map_status
- sources_added
- sources_removed
- sources_changed
- source_traceability_preserved
- stale_source_detected
- unresolved_source_conflict
- source_review_required

## 11. Confidence and Uncertainty Required Fields
Required confidence_uncertainty fields:

- confidence_before
- confidence_after
- confidence_delta
- uncertainty_flags
- uncertainty_summary
- report_hold_required

## 12. Delivery Status Required Fields
Required delivery_status fields:

- internal_draft_status
- delivery_ready_status
- customer_delivery_authorized
- automated_delivery_authorized
- public_publishing_authorized
- production_launch_authorized
- delivery_blockers

Must require:

customer_delivery_authorized=false

automated_delivery_authorized=false

public_publishing_authorized=false

production_launch_authorized=false

## 13. Operator Review Required Fields
Required operator_review fields:

- operator_review_required
- operator_review_status
- operator_id
- operator_decision
- operator_decision_timestamp
- approval_scope
- rejection_reason

Default safe state:

operator_review_required=true

operator_review_status=PENDING

operator_decision=NONE

## 14. Final PDF Integrity Required Fields
Required final_pdf_integrity fields:

- pdf_render_required
- pdf_render_status
- pdf_visual_qa_required
- pdf_visual_qa_status
- final_pdf_sha256
- final_pdf_page_count
- final_pdf_delivery_ready

Default safe state:

final_pdf_delivery_ready=false

## 15. Prohibited Fixture States
Prohibit:

- customer_delivery_authorized=true
- automated_delivery_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- learning_activation_authorized=true
- operator_review_status=APPROVED without operator_id
- final_pdf_delivery_ready=true without pdf_visual_qa_status=PASS
- delivery_ready_status=READY without source_traceability_preserved=true

## 16. Proposed Future Test File
Design only. Do not create it.

Proposed future test file:

operator_dashboard/test_button2_premium_report_update_versioning_fixture_contract_v1.py

This slice does not create that test file.

## 17. Targeted Test Objectives
Future targeted test must verify:

- fixture loads
- all required top-level fields exist
- update_event required fields exist
- changed_section_map entries are complete
- source_map_refresh preserves traceability
- confidence/uncertainty fields exist
- delivery status remains internal-only
- prohibited states are rejected
- operator review defaults to pending
- final PDF delivery-ready remains false unless all integrity gates pass

## 18. Future Test Command
Design only.

Future targeted test command:

python -m pytest operator_dashboard/test_button2_premium_report_update_versioning_fixture_contract_v1.py -q

Do not run this command in the current slice because the test file does not exist yet.

## 19. Implementation Readiness Decision
FIXTURE_SCHEMA_TEST_DESIGN_READY_FOR_NEXT_INTERNAL_SLICE

## 20. Recommended Next Slice
Recommend:

button2_premium_report_update_versioning_fixture_creation_v1

The next slice may create the fixture only, not runtime implementation.

## 21. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
FIXTURE_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY