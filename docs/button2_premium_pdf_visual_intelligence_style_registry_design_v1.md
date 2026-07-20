# Button 2 Premium PDF Visual Intelligence Style Registry Design v1

## 1. Purpose
This document designs the future style registry for AI-RISA Button 2 Premium PDF visuals.

## 2. Design Boundary
This is docs-only design.

It does not authorize:

- runtime changes
- PDF renderer changes
- style registry implementation
- fixture creation
- test creation
- image generation
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

## 4. Source Visual Standard
Reference:

docs/button2_premium_pdf_visual_intelligence_standard_design_v1.md

Confirm:

DESIGN_DECISION=BUTTON2_PREMIUM_PDF_VISUAL_INTELLIGENCE_STANDARD_READY_FOR_STYLE_REGISTRY_DESIGN

## 5. Registry Objective
The registry must centralize Button 2 visual tokens, visual-family identifiers, severity scales, evidence-panel rules, disclaimer footer rules, and page-density controls so future PDF visuals use one consistent AI-RISA premium intelligence-dashboard style.

## 6. Proposed Future Registry File
Design only. Do not create it.

Proposed future file:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_style_registry_v1.json

This slice does not create that file.

## 7. Required Registry Top-Level Fields
Required top-level fields:

- schema_version
- registry_id
- registry_scope
- release_boundary
- color_tokens
- typography_tokens
- border_tokens
- spacing_tokens
- severity_scales
- fighter_identity_tokens
- visual_family_ids
- evidence_panel_tokens
- disclaimer_footer_tokens
- page_density_rules
- overload_prohibitions
- accessibility_rules
- prohibited_states

## 8. Release Boundary Tokens
Require:

release_scope_decision=INTERNAL_ONLY
customer_release_authorized=false
public_publishing_authorized=false
production_launch_authorized=false
automated_delivery_authorized=false
learning_activation_authorized=false

## 9. Color Token Contract
Define color token groups.

### 9.1 Core Interface Colors

- midnight_black
- near_black_panel
- combat_gold
- muted_gold
- steel_grey
- grid_grey
- text_primary
- text_secondary

### 9.2 Fighter Identity Colors

- fighter_a_identity_blue
- fighter_b_identity_red
- neutral_identity_grey
- shared_information_gold

### 9.3 Severity Colors

- severity_very_low
- severity_low
- severity_moderate
- severity_high
- severity_very_high
- severity_critical

Red is a severity/risk colour first. Fighter B red must be restrained and never confuse identity with danger.

## 10. Typography Token Contract
Define typography roles:

- report_title
- section_title
- panel_title
- chart_axis_label
- table_header
- table_body
- score_number_large
- score_number_medium
- evidence_label
- disclaimer_text
- footnote_text

Typography must prioritize readability over decorative density.

## 11. Border and Panel Token Contract
Define:

- outer_report_frame
- hero_visual_frame
- chart_panel_frame
- evidence_panel_frame
- insight_panel_frame
- score_table_frame
- callout_box_frame
- warning_box_frame

## 12. Spacing and Layout Token Contract
Define:

- page_margin
- panel_gap
- title_to_content_gap
- chart_padding
- table_cell_padding
- callout_line_clearance
- footer_clearance
- minimum_mobile_text_size
- minimum_print_text_size

## 13. Severity Scale Contract
Use one consistent 0-100 severity scale.

- 0-20 very low
- 21-40 low
- 41-60 moderate
- 61-80 high
- 81-100 very high

Allow critical label only when a domain-specific threshold says critical.

Every heat map and risk visual must show:

- scale name
- score range
- interpretation
- evidence confidence
- non-medical status where anatomical

## 14. Visual Family ID Contract
Required visual family IDs:

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

## 15. Evidence Panel Contract
Evidence panels must include:

- analysis_id
- report_version
- data_basis
- sample_size
- source_quality
- observed_vs_modelled
- confidence_score
- uncertainty_flags
- limitation_note
- operator_review_status

## 16. Disclaimer Footer Contract
Footer variants:

- tactical_non_medical
- projected_modelled_estimate
- internal_draft_only
- result_comparison_verified

For anatomical visuals, require wording equivalent to:

TACTICAL ANALYSIS -- NOT A MEDICAL DIAGNOSIS

## 17. Page Density Rule Contract
Require:

- maximum one Level 1 hero visual per page
- maximum one Level 2 analytical visual supporting the hero
- maximum three Level 3 evidence panels per page
- no dense master dashboard unless it is a deliberate summary page
- mobile readability must remain acceptable
- printed-page readability must remain acceptable

## 18. Accessibility and Readability Contract
Require:

- no colour-only meaning
- severity must use labels plus colour
- important scores must be numeric
- fighter identity must be named, not only coloured
- callout text must stay readable
- charts must avoid overflow and clipping
- table numbers must not sit on glowing backgrounds

## 19. Prohibited Registry States
Prohibit:

- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- visual_family_id without evidence panel rules
- heat map without severity scale
- anatomical heat map without non-medical disclaimer
- red used as Fighter B identity where it conflicts with risk meaning
- unlabeled heat colours
- PDF visual marked delivery-ready without visual QA gate

## 20. Future Contract Test Objective
Design only.

Future targeted test file:

operator_dashboard/test_button2_premium_pdf_visual_style_registry_contract_v1.py

Future targeted test command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_style_registry_contract_v1.py -q

Do not create or run this test in the current slice.

## 21. Implementation Direction
Implementation should proceed in narrow slices:

1. style registry fixture creation
2. style registry contract test creation
3. style registry review lock
4. one renderer prototype for a non-customer internal chart
5. visual QA gate design
6. internal-only sample page generation
7. internal review lock

This slice does not authorize implementation.

## 22. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_intelligence_style_registry_fixture_creation_v1

The next slice may create only the style registry JSON fixture.

## 23. Design Decision
BUTTON2_PREMIUM_PDF_VISUAL_INTELLIGENCE_STYLE_REGISTRY_DESIGN_READY_FOR_FIXTURE_CREATION

Do not use:

- IMPLEMENTATION_APPROVED
- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- LEARNING_APPROVED

## 24. Slice Integrity
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