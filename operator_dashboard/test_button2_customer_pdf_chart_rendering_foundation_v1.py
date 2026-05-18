"""
Button 2 Customer PDF - Phase 2 Slice 4 - Chart Rendering Foundation Implementation Tests

Purpose:
- Validate that locked chart/scenario metadata remains render-facing in composed HTML
- Verify scenario-tree, method-pathway, round-control, and risk/collapse markers remain present
- Verify chart placement roles remain represented
- Verify invalid chart/scenario metadata fails closed to not_certified
- Verify typography, hierarchy, and page-break rendering foundation slices remain compatible
- Verify no renderer behavior, approval, output, file-write, dashboard, or delivery changes

Governance:
- Chart rendering foundation ONLY
- No real chart drawing
- No renderer behavior changes
- No approval changes
- No output-path changes
- No file-write behavior changes
- No dashboard changes
- No delivery workflow changes
"""

import html as _html
import json
import re

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    _ALLOWED_CHART_PLACEMENT_BLOCK_ROLES,
    _CHART_TYPES,
    _DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES,
    _validate_chart_and_scenario_metadata,
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_chart_foundation_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Chart Rendering Foundation: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "section_block_metadata": [
            {
                "block_id": "report_identity",
                "role": "report_identity_block",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_h1_sections"],
            },
            {
                "block_id": "report_summary",
                "role": "analysis_block",
                "break_policy": "allow_internal_break",
                "can_split": True,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_h2_subsections"],
            },
            {
                "block_id": "source_traceability",
                "role": "sources_calibration_block",
                "break_policy": "split_by_chunk",
                "can_split": True,
                "continuation_header_required": True,
                "chunk_size": 10,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_source_chunks"],
            },
            {
                "block_id": "meta_footer",
                "role": "footer_metadata_block",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["never_split"],
            },
        ],
        "page_break_metadata": [
            {
                "break_id": "pb_001",
                "trigger_block_id": "source_traceability",
                "trigger_section": "Source Traceability",
                "overflow_reason": "source_chunking",
                "previous_page_content_height_in": 8.0,
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-18"}
        ],
        "overlap_proof": {"proof_kind": "overlap_proof", "proof_status": "missing"},
        "off_page_text_proof": {
            "proof_kind": "off_page_text_proof",
            "proof_status": "missing",
        },
        "visual_certification_status": "certified",
    }
    base.update(overrides)
    return base


def _extract_metadata_json(html_text, section_id):
    match = re.search(
        rf'<section\s+id="{section_id}".*?<pre[^>]*>(.*?)</pre>',
        html_text,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(_html.unescape(match.group(1)))


def _valid_chart_metadata():
    return {
        "charts": [
            {
                "chart_id": "chart_scenario_tree_001",
                "chart_type": "scenario_tree",
                "title": "Primary Scenario Pathways",
                "intent": "Explain major tactical branches",
                "placement_block_id": "matchup_signal",
                "placement_block_role": "matchup_signal_block",
                "size_contract": {"max_width_in": 6.5, "max_height_in": 3.5},
                "print_readability_contract": {
                    "min_label_pt": 9,
                    "min_stroke_pt": 1,
                    "min_contrast_ratio": 4.5,
                },
                "source_citations": ["SRC-001"],
            },
            {
                "chart_id": "chart_method_pathway_001",
                "chart_type": "method_pathway",
                "title": "Method Pathway",
                "intent": "Show likely finish or decision paths",
                "placement_block_id": "analysis_method",
                "placement_block_role": "analysis_block",
                "size_contract": {"max_width_in": 6.0, "max_height_in": 3.0},
                "print_readability_contract": {
                    "min_label_pt": 9,
                    "min_stroke_pt": 1,
                    "min_contrast_ratio": 4.5,
                },
                "source_citations": ["SRC-001"],
            },
            {
                "chart_id": "chart_round_control_001",
                "chart_type": "round_control",
                "title": "Round Control Outlook",
                "intent": "Show expected control swings",
                "placement_block_id": "analysis_rounds",
                "placement_block_role": "analysis_block",
                "size_contract": {"max_width_in": 6.0, "max_height_in": 3.0},
                "print_readability_contract": {
                    "min_label_pt": 9,
                    "min_stroke_pt": 1,
                    "min_contrast_ratio": 4.5,
                },
                "source_citations": ["SRC-001"],
            },
            {
                "chart_id": "chart_risk_collapse_001",
                "chart_type": "risk_collapse_markers",
                "title": "Risk Collapse Markers",
                "intent": "Highlight late-fight failure points",
                "placement_block_id": "analysis_risk",
                "placement_block_role": "analysis_block",
                "size_contract": {"max_width_in": 6.0, "max_height_in": 3.0},
                "print_readability_contract": {
                    "min_label_pt": 9,
                    "min_stroke_pt": 1,
                    "min_contrast_ratio": 4.5,
                },
                "source_citations": ["SRC-001"],
            },
        ],
        "scenario_tree": {
            "root_node": "baseline",
            "branches": ["pace_advantage", "distance_control"],
            "terminal_nodes": ["late_finish", "decision_path"],
            "confidence_band": "58-66%",
        },
        "method_pathways": [
            {
                "pathway_id": "method_001",
                "method_type": "decision",
                "trigger_factors": ["jab_volume", "distance_management"],
                "counter_factors": ["pressure_pocket_entries"],
                "evidence_links": ["SRC-001"],
                "confidence_band": "52-60%",
            }
        ],
        "round_control": [
            {
                "window_id": "round_window_001",
                "round_range": "R1-R2",
                "control_expectation": "fighter_a",
                "dominance_signal": "medium",
                "evidence_links": ["SRC-001"],
            }
        ],
        "risk_collapse_markers": [
            {
                "marker_id": "risk_001",
                "risk_type": "damage_accumulation",
                "trigger_window": "R3-R5",
                "severity": "elevated",
                "mitigation_note": "Prioritize distance reset and clinch exits.",
                "evidence_links": ["SRC-001"],
            }
        ],
    }


class TestChartScenarioMetadataPresence:
    def test_chart_metadata_section_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-chart-scenario-metadata"' in html

    def test_chart_schema_version_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-chart-scenario-schema-version="button2.chart_and_scenario.v1"' in html

    def test_chart_validation_status_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-chart-scenario-validation-status="valid"' in html

    def test_chart_metadata_json_parseable(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert metadata["schema_version"] == "button2.chart_and_scenario.v1"
        assert metadata["validation_status"] == "valid"

    def test_chart_metadata_validation_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Chart/scenario metadata validation: valid" in html


class TestScenarioTreeRenderMarkers:
    def test_scenario_tree_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-chart-scenario-metadata",
        )
        assert "scenario_tree" in metadata["chart_and_scenario"]

    def test_scenario_tree_root_node_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-chart-scenario-metadata",
        )
        scenario_tree = metadata["chart_and_scenario"]["scenario_tree"]
        assert scenario_tree["root_node"] == "baseline"

    def test_scenario_tree_branches_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["scenario_tree"]["branches"]

    def test_scenario_tree_terminal_nodes_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["scenario_tree"]["terminal_nodes"]

    def test_scenario_tree_confidence_band_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["scenario_tree"]["confidence_band"]


class TestMethodPathwayRenderMarkers:
    def test_method_pathways_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert "method_pathways" in metadata["chart_and_scenario"]

    def test_method_pathway_chart_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        chart_types = [chart["chart_type"] for chart in metadata["chart_and_scenario"]["charts"]]
        assert "method_pathway" in chart_types

    def test_method_pathway_metadata_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        method_pathway = metadata["chart_and_scenario"]["method_pathways"][0]
        assert method_pathway["method_type"] == "decision"

    def test_method_pathway_trigger_factors_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["method_pathways"][0]["trigger_factors"]

    def test_method_pathway_counter_factors_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["method_pathways"][0]["counter_factors"]


class TestRoundControlRenderMarkers:
    def test_round_control_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert "round_control" in metadata["chart_and_scenario"]

    def test_round_control_chart_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        chart_types = [chart["chart_type"] for chart in metadata["chart_and_scenario"]["charts"]]
        assert "round_control" in chart_types

    def test_round_control_round_range_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["round_control"][0]["round_range"] == "R1-R2"

    def test_round_control_expectation_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert (
            metadata["chart_and_scenario"]["round_control"][0]["control_expectation"]
            == "fighter_a"
        )

    def test_round_control_dominance_signal_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["round_control"][0]["dominance_signal"] == "medium"


class TestRiskCollapseRenderMarkers:
    def test_risk_collapse_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert "risk_collapse_markers" in metadata["chart_and_scenario"]

    def test_risk_collapse_chart_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        chart_types = [chart["chart_type"] for chart in metadata["chart_and_scenario"]["charts"]]
        assert "risk_collapse_markers" in chart_types

    def test_risk_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert (
            metadata["chart_and_scenario"]["risk_collapse_markers"][0]["risk_type"]
            == "damage_accumulation"
        )

    def test_risk_trigger_window_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["risk_collapse_markers"][0]["trigger_window"] == "R3-R5"

    def test_risk_severity_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["risk_collapse_markers"][0]["severity"] == "elevated"


class TestChartPlacementRoles:
    def test_allowed_placement_roles_defined(self):
        assert _ALLOWED_CHART_PLACEMENT_BLOCK_ROLES == {
            "analysis_block",
            "matchup_signal_block",
        }

    def test_disallowed_placement_roles_defined(self):
        assert _DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES == {
            "footer_metadata_block",
            "report_identity_block",
        }

    def test_allowed_placement_roles_present_in_metadata(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert sorted(metadata["allowed_placement_block_roles"]) == sorted(
            _ALLOWED_CHART_PLACEMENT_BLOCK_ROLES
        )

    def test_disallowed_placement_roles_present_in_metadata(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert sorted(metadata["disallowed_placement_block_roles"]) == sorted(
            _DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES
        )

    def test_chart_placement_block_roles_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        placement_roles = {
            chart["placement_block_role"]
            for chart in metadata["chart_and_scenario"]["charts"]
        }
        assert "matchup_signal_block" in placement_roles
        assert "analysis_block" in placement_roles


class TestChartMetadataIntegrity:
    def test_allowed_chart_types_defined(self):
        assert _CHART_TYPES == {
            "comparison_chart",
            "method_pathway",
            "risk_collapse_markers",
            "round_control",
            "scenario_tree",
        }

    def test_chart_list_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert len(metadata["chart_and_scenario"]["charts"]) == 4

    def test_chart_ids_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        chart_ids = [chart["chart_id"] for chart in metadata["chart_and_scenario"]["charts"]]
        assert "chart_scenario_tree_001" in chart_ids
        assert "chart_method_pathway_001" in chart_ids

    def test_size_contracts_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        for chart in metadata["chart_and_scenario"]["charts"]:
            assert chart["size_contract"]["max_width_in"] <= 6.5
            assert chart["size_contract"]["max_height_in"] <= 4.0

    def test_readability_contracts_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        for chart in metadata["chart_and_scenario"]["charts"]:
            assert chart["print_readability_contract"]["min_label_pt"] >= 9


class TestChartValidationFailClosed:
    def test_valid_chart_metadata_passes_validation(self):
        validation = _validate_chart_and_scenario_metadata(_valid_chart_metadata())
        assert validation["valid"] is True
        assert validation["status"] == "valid"
        assert validation["issues"] == []

    def test_missing_chart_metadata_fails_validation(self):
        validation = _validate_chart_and_scenario_metadata(None)
        assert validation["valid"] is False
        assert validation["status"] == "missing"
        assert "missing_chart_metadata" in validation["issues"]

    def test_invalid_chart_type_fails_validation(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["charts"][0]["chart_type"] = "invalid_chart"
        validation = _validate_chart_and_scenario_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "chart_0_invalid_chart_type" in validation["issues"]

    def test_invalid_placement_role_fails_validation(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["charts"][0]["placement_block_role"] = "fighter_context_block"
        validation = _validate_chart_and_scenario_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "chart_0_invalid_placement_role" in validation["issues"]

    def test_invalid_method_pathway_fails_validation(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["method_pathways"][0]["method_type"] = "bad_method"
        validation = _validate_chart_and_scenario_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "method_pathway_0_invalid_method_type" in validation["issues"]

    def test_invalid_round_control_fails_validation(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["round_control"][0]["control_expectation"] = "nobody"
        validation = _validate_chart_and_scenario_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "round_control_0_invalid_control_expectation" in validation["issues"]

    def test_invalid_risk_marker_fails_validation(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["risk_collapse_markers"][0]["severity"] = "bad"
        validation = _validate_chart_and_scenario_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "risk_marker_0_invalid_severity" in validation["issues"]

    def test_invalid_chart_metadata_downgrades_certification(self):
        invalid_metadata = _valid_chart_metadata()
        invalid_metadata["charts"][0]["chart_type"] = "invalid_chart"
        html = build_button2_report_html(
            _valid_ctx(
                chart_and_scenario_metadata=invalid_metadata,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Chart/scenario metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_missing_chart_metadata_downgrades_certification(self):
        html = build_button2_report_html(
            _valid_ctx(chart_and_scenario_metadata=None, visual_certification_status="certified")
        )["html_content"]
        assert "Chart/scenario metadata validation: missing" in html
        assert "Visual certification: not_certified" in html


class TestChartNoRendererBehaviorChanges:
    def test_chart_rendering_idempotent(self):
        ctx = _valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata())
        html_one = build_button2_report_html(ctx)["html_content"]
        html_two = build_button2_report_html(ctx)["html_content"]
        assert html_one == html_two

    def test_chart_rendering_deterministic(self):
        ctx = _valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata())
        result_one = build_button2_report_html(ctx)
        result_two = build_button2_report_html(ctx)
        assert result_one["html_content"] == result_two["html_content"]
        assert result_one["ok"] is True
        assert result_two["ok"] is True

    def test_no_real_chart_drawing_added(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ].lower()
        assert "<canvas" not in html
        assert "chart.js" not in html
        assert "plotly" not in html


class TestChartNoTypographyHierarchyOrPageBreakChanges:
    def test_typography_tokens_preserved(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert 'class="typography-body-secondary"' in html

    def test_hierarchy_markers_preserved(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_page_break_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'data-page-breaks-validation-status="valid"' in html

    def test_all_metadata_sections_present(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html


class TestSafetyInvariantsPhase2Slice4:
    def test_preview_only_flag_preserved(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["preview_only"] is True

    def test_pdf_generation_flag_false(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["pdf_generation_performed"] is False

    def test_file_write_flag_false(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["file_write_performed"] is False

    def test_export_flag_false(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["export_performed"] is False

    def test_delivery_flag_false(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["delivery_performed"] is False

    def test_html_composition_performed_true(self):
        result = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))
        assert result["html_composition_performed"] is True

    def test_no_dashboard_or_approval_surface_added(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ].lower()
        assert "<button" not in html
        assert "<form" not in html


class TestPhase1BackwardCompatibility:
    def test_phase1_html_structure_unchanged(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert "AI-RISA Premium Fight Report" in html
        assert "fight_chart_foundation_001" in html

    def test_no_scripts_injected(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ].lower()
        assert "<script" not in html
        assert "http://" not in html
        assert "https://" not in html

    def test_source_traceability_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert 'id="button2-source-traceability-metadata"' in html

    def test_visual_qa_rollup_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert 'id="button2-visual-qa-rollup-metadata"' in html


class TestChartIntegration:
    def test_chart_schema_matches_constant_surface(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert sorted(metadata["allowed_chart_types"]) == sorted(_CHART_TYPES)

    def test_chart_metadata_render_facing(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
                "html_content"
            ],
            "button2-chart-scenario-metadata",
        )
        assert metadata["chart_and_scenario"]["charts"][0]["chart_id"] == "chart_scenario_tree_001"
        assert any(
            chart["placement_block_role"] == "analysis_block"
            for chart in metadata["chart_and_scenario"]["charts"]
        )

    def test_chart_layer_does_not_break_page_break_layer(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert "Page-break metadata validation: valid" in html

    def test_chart_layer_does_not_break_hierarchy_layer(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert "Hierarchy validation: valid" in html

    def test_all_visual_qa_layers_accounted_for(self):
        html = build_button2_report_html(_valid_ctx(chart_and_scenario_metadata=_valid_chart_metadata()))[
            "html_content"
        ]
        assert "Hierarchy validation: valid" in html
        assert "Page-break metadata validation: valid" in html
        assert "Chart/scenario metadata validation: valid" in html
        assert "Header/footer/watermark metadata validation:" in html
        assert "Source traceability metadata validation:" in html