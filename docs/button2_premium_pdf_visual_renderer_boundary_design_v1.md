# Button 2 Premium PDF Visual Renderer Boundary Design v1

## 1. Purpose
This document defines the future Button 2 Premium PDF Visual Intelligence renderer boundary.

## 2. Design Boundary
This is docs-only design.

It does not authorize:

- runtime implementation
- PDF renderer implementation
- PDF rendering
- image generation
- visual reference folder ingestion
- fixture creation
- test creation
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

## 4. Source Lock Reviewed
Reference:

docs/button2_premium_pdf_visual_style_registry_contract_test_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_BUTTON2_VISUAL_STYLE_REGISTRY_TEST_LOCK_INTERNAL_ONLY

TARGETED_TEST_RESULT=PASS

REFERENCE_VISUAL_FOLDER_NOT_USED=YES

IMAGE_DEPENDENCY_FOUND=NO

## 5. Renderer Objective
The renderer must produce AI-RISA premium PDF visual components from structured internal data and the locked style registry while enforcing visual-family contracts, release boundaries, evidence panels, disclaimers, page-density rules, accessibility rules, and visual QA prerequisites.

## 6. Proposed Future Renderer Module
Design only. Do not create it.

Proposed future module:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_renderer_v1.py

This slice does not create that module.

## 7. Proposed Future Renderer Contract Test
Design only. Do not create it.

Proposed future test:

operator_dashboard/test_button2_premium_pdf_visual_renderer_boundary_contract_v1.py

Future targeted command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_renderer_boundary_contract_v1.py -q

Do not create or run this test in the current slice.

## 8. Renderer Input Contract
Required future input fields:

- visual_family_id
- report_id
- analysis_id
- report_version
- fighter_a_label
- fighter_b_label
- visual_title
- visual_subtitle
- data_basis
- sample_size
- source_quality
- observed_vs_modelled
- confidence_score
- uncertainty_flags
- limitation_note
- operator_review_status
- release_boundary
- visual_data
- page_density_level
- disclaimer_variant
- visual_qa_required

## 9. Renderer Output Contract
Future output object fields:

- render_status
- visual_family_id
- output_type
- output_path
- page_component_id
- style_registry_id
- evidence_panel_rendered
- disclaimer_footer_rendered
- severity_scale_rendered
- accessibility_checks_passed
- page_density_checks_passed
- visual_qa_required
- visual_qa_status
- delivery_ready
- release_boundary

Required safe default:

delivery_ready=false

## 10. Visual Family Routing Contract
Renderer must route only approved visual family IDs:

- anatomical_target_exposure_heat_map
- fatigue_structural_decay_heat_map
- tactical_vulnerability_map
- fighter_architecture_radar
- tactical_edge_bar_chart
- round_control_projection_line_graph
- scenario_method_pathway_tree
- ring_geography_pressure_map
- decision_structure_map
- pace_energy_fatigue_curve
- training_priority_heat_map
- scorecard_probability_table
- button3_result_comparison_visual

Unknown visual_family_id must fail closed.

## 11. Style Registry Consumption Rules
Renderer must consume:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_style_registry_v1.json

Rules:

- no hard-coded visual-family IDs outside the registry unless contract tested
- no hard-coded customer release approvals
- no hard-coded production launch approvals
- no hard-coded learning activation approvals
- no hard-coded delivery-ready true
- red primary meaning rule must be preserved
- page density rules must be enforced
- evidence panel rules must be enforced
- disclaimer footer rules must be enforced

## 12. Reference Visual Folder Policy
Record:

C:\Users\jusin\OneDrive\Pictures\New Visuals

Policy:

- reference-only
- not a runtime dependency
- not a test dependency
- not copied into repo without a separate asset-ingestion authorization
- not used for customer delivery
- may guide future visual QA or prototype comparison only in separately authorized internal slices

## 13. Anatomical Visual Boundary
Anatomical treatment may be used only for:

- anatomical_target_exposure_heat_map
- fatigue_structural_decay_heat_map
- tactical_vulnerability_map
- training_priority_heat_map

Each anatomical visual must require:

- non-medical disclaimer
- severity scale
- evidence panel
- confidence score
- observed vs modelled classification
- no injury diagnosis language

## 14. Non-Anatomical Visual Boundary
These visuals must not require anatomical body graphics:

- fighter_architecture_radar
- tactical_edge_bar_chart
- round_control_projection_line_graph
- scenario_method_pathway_tree
- ring_geography_pressure_map
- decision_structure_map
- pace_energy_fatigue_curve
- scorecard_probability_table
- button3_result_comparison_visual

They must still use:

- AI-RISA black/gold visual identity
- evidence panel where required
- accessible labels
- page-density controls
- disclaimer footer where required

## 15. Fail-Closed Conditions
Renderer must fail closed if:

- registry fixture is missing
- registry contract is invalid
- unknown visual_family_id is requested
- release boundary is not INTERNAL_ONLY
- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- required evidence panel fields are missing
- required disclaimer footer is missing
- heat map lacks severity scale
- anatomical visual lacks non-medical disclaimer
- page density limit is exceeded
- visual QA gate is required but absent
- delivery_ready would become true without visual QA PASS

## 16. Visual QA Gate Boundary
Future renderer outputs must not become delivery-ready until a later visual QA gate confirms:

- no clipping
- no overflow
- no unreadable small text
- no missing labels
- no unlabeled severity colours
- no ambiguous Fighter A / Fighter B colours
- no missing source/evidence panel
- no missing disclaimer
- no broken table layout
- no glowing background behind critical table numbers

This slice does not create the visual QA gate.

## 17. Minimum Future Renderer Test Objectives
Future targeted test must verify:

- registry loads
- approved visual families route correctly
- unknown visual family fails closed
- internal-only release boundary enforced
- customer release true rejected
- learning activation true rejected
- anatomical visual without disclaimer rejected
- heat map without severity scale rejected
- delivery_ready remains false by default
- visual QA missing prevents delivery_ready true
- reference visual folder is not required
- no PDF is generated by boundary contract test

## 18. Implementation Direction
Implementation should proceed in narrow slices:

1. renderer boundary contract test design or creation
2. minimal renderer scaffold returning contract objects only
3. renderer scaffold targeted test
4. one non-customer internal visual prototype
5. visual QA gate design
6. visual QA gate test
7. internal-only sample PDF page generation
8. review lock

Do not authorize implementation in this slice.

## 19. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_renderer_boundary_contract_test_design_v1

The next slice should define or create the renderer boundary contract test before renderer implementation.

## 20. Design Decision
BUTTON2_PREMIUM_PDF_VISUAL_RENDERER_BOUNDARY_READY_FOR_CONTRACT_TEST_DESIGN

Do not use:

- IMPLEMENTATION_APPROVED
- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- LEARNING_APPROVED

## 21. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
FIXTURE_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
IMAGE_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY