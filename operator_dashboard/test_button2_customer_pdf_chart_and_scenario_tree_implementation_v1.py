"""
Button 2: Customer PDF Chart and Scenario Tree Implementation Tests v1

Purpose:
- Validate chart/scenario metadata emission and validation in HTML composition
- Validate scenario tree, method pathway, round-control, and risk marker metadata
- Validate fail-closed downgrade behavior for invalid/missing chart metadata
"""

import html as _html
import json
import re

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_chart_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Chart metadata test summary",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
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


class TestChartScenarioMetadataPresence:
    def test_chart_scenario_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert metadata["schema_version"] == "button2.chart_and_scenario.v1"
        assert metadata["validation_status"] == "valid"

    def test_scenario_tree_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        scenario_tree = metadata["chart_and_scenario"]["scenario_tree"]
        assert scenario_tree["root_node"]
        assert scenario_tree["branches"]
        assert scenario_tree["terminal_nodes"]
        assert scenario_tree["confidence_band"]

    def test_method_pathway_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        method_pathways = metadata["chart_and_scenario"]["method_pathways"]
        assert isinstance(method_pathways, list)
        assert len(method_pathways) > 0
        assert method_pathways[0]["method_type"]

    def test_round_control_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        round_control = metadata["chart_and_scenario"]["round_control"]
        assert isinstance(round_control, list)
        assert len(round_control) > 0
        assert round_control[0]["round_range"]

    def test_risk_collapse_marker_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        risk_markers = metadata["chart_and_scenario"]["risk_collapse_markers"]
        assert isinstance(risk_markers, list)
        assert len(risk_markers) > 0
        assert risk_markers[0]["risk_type"]

    def test_chart_placement_rules_are_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert "analysis_block" in metadata["allowed_placement_block_roles"]
        assert "matchup_signal_block" in metadata["allowed_placement_block_roles"]
        assert "report_identity_block" in metadata["disallowed_placement_block_roles"]


class TestChartScenarioFailClosed:
    def test_missing_chart_metadata_fails_closed(self):
        html = build_button2_report_html(
            _valid_ctx(chart_and_scenario_metadata=None, visual_certification_status="certified")
        )["html_content"]
        assert "Chart/scenario metadata validation: missing" in html
        assert "Visual certification: not_certified" in html

    def test_invalid_chart_type_fails_closed(self):
        invalid_metadata = {
            "charts": [
                {
                    "chart_id": "chart_1",
                    "chart_type": "unknown_type",
                    "title": "Bad chart",
                    "placement_block_id": "matchup_signal",
                    "placement_block_role": "analysis_block",
                    "size_contract": {"max_width_in": 6.5, "max_height_in": 3.0},
                    "print_readability_contract": {"min_label_pt": 9},
                    "source_citations": ["SRC-001"],
                }
            ],
            "scenario_tree": {
                "root_node": "baseline",
                "branches": ["a", "b"],
                "terminal_nodes": ["x", "y"],
                "confidence_band": "50-60%",
            },
            "method_pathways": [
                {
                    "pathway_id": "p1",
                    "method_type": "decision",
                    "trigger_factors": ["x"],
                    "counter_factors": ["y"],
                    "evidence_links": ["SRC-001"],
                    "confidence_band": "50-60%",
                }
            ],
            "round_control": [
                {
                    "window_id": "w1",
                    "round_range": "R1-R2",
                    "control_expectation": "fighter_a",
                    "dominance_signal": "medium",
                    "evidence_links": ["SRC-001"],
                }
            ],
            "risk_collapse_markers": [
                {
                    "marker_id": "m1",
                    "risk_type": "damage_accumulation",
                    "trigger_window": "R3-R5",
                    "severity": "elevated",
                    "mitigation_note": "Mitigate",
                    "evidence_links": ["SRC-001"],
                }
            ],
        }
        html = build_button2_report_html(
            _valid_ctx(chart_and_scenario_metadata=invalid_metadata, visual_certification_status="certified")
        )["html_content"]
        assert "Chart/scenario metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_disallowed_placement_role_fails_closed(self):
        invalid_metadata = {
            "charts": [
                {
                    "chart_id": "chart_1",
                    "chart_type": "scenario_tree",
                    "title": "Bad placement",
                    "placement_block_id": "report_identity",
                    "placement_block_role": "report_identity_block",
                    "size_contract": {"max_width_in": 6.5, "max_height_in": 3.0},
                    "print_readability_contract": {"min_label_pt": 9},
                    "source_citations": ["SRC-001"],
                }
            ],
            "scenario_tree": {
                "root_node": "baseline",
                "branches": ["a", "b"],
                "terminal_nodes": ["x", "y"],
                "confidence_band": "50-60%",
            },
            "method_pathways": [
                {
                    "pathway_id": "p1",
                    "method_type": "decision",
                    "trigger_factors": ["x"],
                    "counter_factors": ["y"],
                    "evidence_links": ["SRC-001"],
                    "confidence_band": "50-60%",
                }
            ],
            "round_control": [
                {
                    "window_id": "w1",
                    "round_range": "R1-R2",
                    "control_expectation": "fighter_a",
                    "dominance_signal": "medium",
                    "evidence_links": ["SRC-001"],
                }
            ],
            "risk_collapse_markers": [
                {
                    "marker_id": "m1",
                    "risk_type": "damage_accumulation",
                    "trigger_window": "R3-R5",
                    "severity": "elevated",
                    "mitigation_note": "Mitigate",
                    "evidence_links": ["SRC-001"],
                }
            ],
        }
        html = build_button2_report_html(
            _valid_ctx(chart_and_scenario_metadata=invalid_metadata, visual_certification_status="certified")
        )["html_content"]
        assert "Chart/scenario metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html


class TestSafetyRegressionSignals:
    def test_safety_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False

    def test_no_external_css_or_scripts(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
        assert "<link rel=\"stylesheet\"" not in html
