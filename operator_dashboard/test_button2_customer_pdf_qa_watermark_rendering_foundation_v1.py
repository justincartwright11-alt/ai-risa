"""
Button 2 Customer PDF - Phase 2 Slice 7 - QA Watermark Rendering Foundation Tests

Purpose:
- Verify Visual QA rollup metadata remains render-facing
- Verify rollup status, completeness, confidence, readiness, attention layers, and review focus remain represented
- Verify invalid rollup metadata path fails closed to not_certified

Governance:
- QA watermark rendering foundation ONLY
- No certification automation changes
- No renderer, approval, output-path, file-write, dashboard, or delivery changes
"""

import html as _html
import json
import re

import operator_dashboard.button2_html_composition_entry_point_v1 as _entry
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    _CERTIFICATION_READINESS,
    _ROLLUP_STATUS,
    _VISUAL_CONFIDENCE_LEVELS,
    _validate_visual_qa_rollup_metadata,
    _visual_qa_rollup_payload,
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_qa_watermark_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "QA Watermark Rendering Foundation: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-18"}
        ],
        "overlap_proof": {"status": "present"},
        "off_page_text_proof": {"status": "present"},
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


def _valid_rollup_metadata():
    layer_summary = {
        "layer_1_typography": {
            "schema_version": "button2.page_typography_tokens.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_2_hierarchy": {
            "schema_version": "button2.page_hierarchy.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_3_page_breaks": {
            "schema_version": "button2.page_breaks_and_blocks.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_4_charts": {
            "schema_version": "button2.chart_and_scenario.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_5_header_footer_watermark": {
            "schema_version": "button2.header_footer_watermark.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_6_source_traceability": {
            "schema_version": "button2.source_traceability.v1",
            "validation_status": "valid",
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "proof_overlap": {
            "proof_kind": "overlap_proof",
            "proof_status": "present",
            "required_for_certification": True,
        },
        "proof_off_page_text": {
            "proof_kind": "off_page_text_proof",
            "proof_status": "present",
            "required_for_certification": True,
        },
    }
    return {
        "schema_version": "button2.visual_qa_rollup.v1",
        "rollup_generated_timestamp": "2026-05-18T12:00:00Z",
        "rollup_status": "all_valid",
        "layer_validation_summary": layer_summary,
        "visual_qa_indicators": {
            "overall_visual_completeness": 1.0,
            "overall_visual_confidence": "high",
            "certification_readiness": "ready",
            "valid_layers_count": 8,
            "invalid_layers_count": 0,
            "missing_layers_count": 0,
            "layers_requiring_attention": [],
        },
        "recommended_review_focus": [
            {
                "priority": 1,
                "category": "all_layers",
                "issue": "all_valid",
                "recommendation": "All visual QA metadata is valid and complete",
            }
        ],
    }


class TestVisualQaRollupRenderFacing:
    def test_rollup_metadata_section_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-visual-qa-rollup-metadata"' in html

    def test_rollup_schema_version_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-visual-qa-rollup-schema-version="button2.visual_qa_rollup.v1"' in html

    def test_rollup_metadata_json_parseable(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        assert metadata["schema_version"] == "button2.visual_qa_rollup.v1"
        assert metadata["validation_status"] == "valid"

    def test_rollup_status_data_attribute_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-visual-qa-rollup-status="all_valid"' in html

    def test_rollup_status_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Visual QA rollup status: all_valid" in html


class TestQaIndicatorsRepresentation:
    def test_completeness_score_data_attribute_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-visual-completeness="100%"' in html

    def test_completeness_score_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Completeness: 100%" in html

    def test_visual_confidence_data_attribute_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-visual-confidence="high"' in html

    def test_visual_confidence_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Overall visual confidence: high" in html

    def test_certification_readiness_data_attribute_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-certification-readiness="ready"' in html

    def test_certification_readiness_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Certification readiness: ready" in html

    def test_valid_invalid_missing_counts_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Valid layers: 8/8 | Invalid: 0 | Missing: 0" in html


class TestAttentionAndReviewFocusRepresentation:
    def test_layers_requiring_attention_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(overlap_proof={}, off_page_text_proof={}))["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        attention = metadata["visual_qa_rollup"]["visual_qa_indicators"]["layers_requiring_attention"]
        assert isinstance(attention, list)
        assert "proof_overlap" in attention
        assert "proof_off_page_text" in attention

    def test_recommended_review_focus_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(overlap_proof={}, off_page_text_proof={}))["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        focus = metadata["visual_qa_rollup"]["recommended_review_focus"]
        assert isinstance(focus, list)
        assert len(focus) > 0
        assert focus[0].get("issue")
        assert focus[0].get("recommendation")

    def test_missing_overlap_focus_issue_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(overlap_proof={}))["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        focus_issues = [item.get("issue") for item in metadata["visual_qa_rollup"]["recommended_review_focus"]]
        assert "missing_overlap_proof" in focus_issues

    def test_missing_off_page_focus_issue_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(off_page_text_proof={}))["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        focus_issues = [item.get("issue") for item in metadata["visual_qa_rollup"]["recommended_review_focus"]]
        assert "missing_off_page_text_proof" in focus_issues

    def test_all_valid_focus_message_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        focus_issues = [item.get("issue") for item in metadata["visual_qa_rollup"]["recommended_review_focus"]]
        assert "all_valid" in focus_issues


class TestRollupValidationFailClosed:
    def test_valid_rollup_metadata_passes_validation(self):
        validation = _validate_visual_qa_rollup_metadata(_valid_rollup_metadata())
        assert validation["valid"] is True
        assert validation["status"] == "valid"

    def test_missing_rollup_metadata_fails_validation(self):
        validation = _validate_visual_qa_rollup_metadata(None)
        assert validation["valid"] is False
        assert validation["status"] == "missing"
        assert "missing_visual_qa_rollup_metadata" in validation["issues"]

    def test_invalid_rollup_status_fails_validation(self):
        invalid_metadata = _valid_rollup_metadata()
        invalid_metadata["rollup_status"] = "unknown"
        validation = _validate_visual_qa_rollup_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "invalid_rollup_status" in validation["issues"]

    def test_invalid_completeness_fails_validation(self):
        invalid_metadata = _valid_rollup_metadata()
        invalid_metadata["visual_qa_indicators"]["overall_visual_completeness"] = 2.0
        validation = _validate_visual_qa_rollup_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "invalid_overall_visual_completeness" in validation["issues"]

    def test_invalid_confidence_fails_validation(self):
        invalid_metadata = _valid_rollup_metadata()
        invalid_metadata["visual_qa_indicators"]["overall_visual_confidence"] = "certain"
        validation = _validate_visual_qa_rollup_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "invalid_overall_visual_confidence" in validation["issues"]

    def test_invalid_readiness_fails_validation(self):
        invalid_metadata = _valid_rollup_metadata()
        invalid_metadata["visual_qa_indicators"]["certification_readiness"] = "auto_approved"
        validation = _validate_visual_qa_rollup_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "invalid_certification_readiness" in validation["issues"]

    def test_invalid_rollup_payload_downgrades_certification(self, monkeypatch):
        original = _entry._visual_qa_rollup_payload

        def _invalid_rollup_payload(_ctx, _layers):
            payload = original(_ctx, _layers)
            payload["validation_status"] = "invalid"
            payload["validation_issues"] = ["simulated_invalid_rollup"]
            return payload

        monkeypatch.setattr(_entry, "_visual_qa_rollup_payload", _invalid_rollup_payload)

        html = build_button2_report_html(_valid_ctx(visual_certification_status="certified"))["html_content"]
        assert "Visual certification: not_certified" in html


class TestNoRendererBehaviorChanges:
    def test_rollup_rendering_idempotent(self):
        ctx = _valid_ctx()
        html_one = build_button2_report_html(ctx)["html_content"]
        html_two = build_button2_report_html(ctx)["html_content"]
        assert html_one == html_two

    def test_rollup_rendering_deterministic(self):
        ctx = _valid_ctx()
        result_one = build_button2_report_html(ctx)
        result_two = build_button2_report_html(ctx)
        assert result_one["html_content"] == result_two["html_content"]
        assert result_one["ok"] is True
        assert result_two["ok"] is True

    def test_no_interactive_surface_added(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "<button" not in html
        assert "<form" not in html


class TestNoPriorFoundationChanges:
    def test_typography_tokens_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert "typography-page-metadata" in html

    def test_hierarchy_markers_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_page_break_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'data-page-breaks-validation-status="valid"' in html

    def test_chart_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'data-chart-scenario-validation-status="valid"' in html

    def test_hfw_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'data-header-footer-watermark-validation-status="valid"' in html

    def test_source_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-source-traceability-metadata"' in html
        assert 'data-source-traceability-validation-status="valid"' in html


class TestSafetyInvariantsPhase2Slice7:
    def test_preview_only_flag_preserved(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True

    def test_pdf_generation_flag_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["pdf_generation_performed"] is False

    def test_file_write_flag_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["file_write_performed"] is False

    def test_export_flag_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["export_performed"] is False

    def test_delivery_flag_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["delivery_performed"] is False

    def test_html_composition_performed_true(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["html_composition_performed"] is True


class TestQaWatermarkIntegration:
    def test_rollup_allowed_statuses_surface(self):
        payload = _visual_qa_rollup_payload(
            _valid_ctx(),
            {
                "hierarchy_payload": {"hierarchy_validation_status": "valid", "validation_issues": []},
                "page_breaks_payload": {"validation_status": "valid", "validation_issues": []},
                "chart_payload": {"validation_status": "valid", "validation_issues": []},
                "hfw_payload": {"validation_status": "valid", "validation_issues": []},
                "src_payload": {"validation_status": "valid", "validation_issues": []},
            },
        )
        assert sorted(payload["allowed_rollup_statuses"]) == sorted(_ROLLUP_STATUS)
        assert sorted(payload["allowed_confidence_levels"]) == sorted(_VISUAL_CONFIDENCE_LEVELS)
        assert sorted(payload["allowed_readiness_levels"]) == sorted(_CERTIFICATION_READINESS)

    def test_rollup_metadata_render_facing(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-visual-qa-rollup-metadata",
        )
        indicators = metadata["visual_qa_rollup"]["visual_qa_indicators"]
        assert metadata["visual_qa_rollup"]["rollup_status"] == "all_valid"
        assert indicators["overall_visual_completeness"] == 1.0
        assert indicators["overall_visual_confidence"] == "high"
        assert indicators["certification_readiness"] == "ready"

    def test_qa_watermark_layer_does_not_break_other_layers(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Hierarchy validation: valid" in html
        assert "Page-break metadata validation: valid" in html
        assert "Chart/scenario metadata validation: valid" in html
        assert "Header/footer/watermark metadata validation: valid" in html
        assert "Source traceability metadata validation: valid" in html

    def test_all_visual_qa_rows_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Visual QA rollup status:" in html
        assert "Overall visual confidence:" in html
        assert "Valid layers:" in html
