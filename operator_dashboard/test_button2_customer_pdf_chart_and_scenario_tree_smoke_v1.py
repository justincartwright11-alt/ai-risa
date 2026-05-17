"""
Button 2: Customer PDF Chart and Scenario Tree Smoke v1

Evidence-only smoke proof that typography, hierarchy, page-break/section-block,
and chart/scenario metadata coexist safely in composed Button 2 HTML.
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
        "fight_id": "smoke_chart_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Smoke summary for chart/scenario metadata chain",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-SMOKE-CHART", "type": "official", "date": "2026-05-17"}
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


class TestButton2ChartScenarioSmokeV1:
    def test_chart_scenario_metadata_exists_and_valid(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert metadata["schema_version"] == "button2.chart_and_scenario.v1"
        assert metadata["validation_status"] == "valid"

    def test_scenario_tree_method_round_risk_metadata_remain_valid(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        payload = metadata["chart_and_scenario"]

        scenario_tree = payload["scenario_tree"]
        assert scenario_tree["root_node"]
        assert scenario_tree["branches"]
        assert scenario_tree["terminal_nodes"]
        assert scenario_tree["confidence_band"]

        method_pathways = payload["method_pathways"]
        assert isinstance(method_pathways, list) and method_pathways
        assert method_pathways[0]["method_type"]

        round_control = payload["round_control"]
        assert isinstance(round_control, list) and round_control
        assert round_control[0]["round_range"]

        risk_markers = payload["risk_collapse_markers"]
        assert isinstance(risk_markers, list) and risk_markers
        assert risk_markers[0]["risk_type"]

    def test_chart_placement_rules_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert "analysis_block" in metadata["allowed_placement_block_roles"]
        assert "matchup_signal_block" in metadata["allowed_placement_block_roles"]
        assert "report_identity_block" in metadata["disallowed_placement_block_roles"]

    def test_typography_hierarchy_and_page_break_metadata_remain_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert 'class="typography-body-secondary"' in html
        assert 'class="typography-list-item"' in html

        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-hierarchy-metadata"' in html

    def test_invalid_chart_metadata_fails_closed_to_not_certified(self):
        invalid_metadata = {
            "charts": [
                {
                    "chart_id": "chart_bad_1",
                    "chart_type": "unknown_type",
                    "title": "Invalid",
                    "placement_block_id": "matchup_signal",
                    "placement_block_role": "analysis_block",
                    "size_contract": {"max_width_in": 6.5, "max_height_in": 3.0},
                    "print_readability_contract": {"min_label_pt": 9},
                    "source_citations": ["SRC-SMOKE-CHART"],
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
                    "evidence_links": ["SRC-SMOKE-CHART"],
                    "confidence_band": "50-60%",
                }
            ],
            "round_control": [
                {
                    "window_id": "w1",
                    "round_range": "R1-R2",
                    "control_expectation": "fighter_a",
                    "dominance_signal": "medium",
                    "evidence_links": ["SRC-SMOKE-CHART"],
                }
            ],
            "risk_collapse_markers": [
                {
                    "marker_id": "m1",
                    "risk_type": "damage_accumulation",
                    "trigger_window": "R3-R5",
                    "severity": "elevated",
                    "mitigation_note": "Mitigate",
                    "evidence_links": ["SRC-SMOKE-CHART"],
                }
            ],
        }
        html = build_button2_report_html(
            _valid_ctx(
                chart_and_scenario_metadata=invalid_metadata,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Chart/scenario metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_missing_chart_metadata_fails_closed_to_not_certified(self):
        html = build_button2_report_html(
            _valid_ctx(
                chart_and_scenario_metadata=None,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Chart/scenario metadata validation: missing" in html
        assert "Visual certification: not_certified" in html

    def test_no_external_css_scripts_and_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
        assert "<link rel=\"stylesheet\"" not in html

        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
