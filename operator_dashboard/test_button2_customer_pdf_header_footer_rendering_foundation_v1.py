"""
Button 2 Customer PDF - Phase 2 Slice 5 - Header/Footer/Watermark Rendering Foundation Tests

Purpose:
- Validate that locked header/footer/watermark metadata remains render-facing in composed HTML
- Verify header metadata, footer metadata, and watermark metadata remain represented
- Verify status/confidentiality labels, page-number rules, and QA footer placement remain represented
- Verify invalid header/footer/watermark metadata fails closed to not_certified
- Verify typography, hierarchy, page-break, and chart rendering foundation slices remain green

Governance:
- Header/footer/watermark rendering foundation ONLY
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
    _CONFIDENTIALITY_LABELS,
    _STATUS_LABELS,
    _WATERMARK_TYPES,
    _header_footer_watermark_payload,
    _validate_header_footer_watermark_metadata,
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_header_footer_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Header/Footer Rendering Foundation: Fighter A vs Fighter B",
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


def _valid_hfw_metadata():
    return {
        "header": {
            "report_title": "AI-RISA Premium Fight Report",
            "event_name": "Sample Event",
            "event_date": "2026-05-18",
            "status_label": "DRAFT",
            "confidentiality_label": "CONFIDENTIAL",
        },
        "footer": {
            "page_number_format": "Page {n} of {m}",
            "operator_label": "Operator",
            "generated_timestamp": "2026-05-18T12:00:00Z",
        },
        "watermark": {
            "watermark_enabled": True,
            "watermark_type": "draft",
            "watermark_text": "DRAFT",
            "watermark_opacity": 0.12,
            "watermark_angle": 45,
        },
    }


def _extract_metadata_json(html_text, section_id):
    match = re.search(
        rf'<section\s+id="{section_id}".*?<pre[^>]*>(.*?)</pre>',
        html_text,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(_html.unescape(match.group(1)))


class TestHeaderMetadataRenderFacing:
    def test_hfw_metadata_section_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-header-footer-watermark-metadata"' in html

    def test_hfw_schema_version_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-header-footer-watermark-schema-version="button2.header_footer_watermark.v1"' in html

    def test_hfw_validation_status_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-header-footer-watermark-validation-status="valid"' in html

    def test_header_metadata_json_parseable(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["schema_version"] == "button2.header_footer_watermark.v1"
        assert metadata["validation_status"] == "valid"

    def test_header_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert "header" in metadata["header_footer_watermark"]

    def test_header_report_title_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["header"]["report_title"] == "AI-RISA Premium Fight Report"

    def test_header_event_name_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["header"]["event_name"] == "Sample Event"


class TestFooterMetadataRenderFacing:
    def test_footer_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert "footer" in metadata["header_footer_watermark"]

    def test_footer_page_number_format_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["footer"]["page_number_format"] == "Page {n} of {m}"

    def test_footer_operator_label_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["footer"]["operator_label"] == "Operator"

    def test_footer_generated_timestamp_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["footer"]["generated_timestamp"] == "2026-05-17T12:00:00Z"

    def test_footer_metadata_validation_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Header/footer/watermark metadata validation: valid" in html


class TestWatermarkMetadataRenderFacing:
    def test_watermark_key_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert "watermark" in metadata["header_footer_watermark"]

    def test_watermark_enabled_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["watermark"]["watermark_enabled"] is True

    def test_watermark_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["watermark"]["watermark_type"] == "draft"

    def test_watermark_text_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["watermark"]["watermark_text"] == "DRAFT"

    def test_watermark_opacity_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["watermark"]["watermark_opacity"] == 0.12

    def test_watermark_angle_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["watermark"]["watermark_angle"] == 45


class TestLabelsAndPageNumberRules:
    def test_status_labels_represented(self):
        payload = _header_footer_watermark_payload(_valid_ctx())
        assert sorted(payload["allowed_status_labels"]) == sorted(_STATUS_LABELS)

    def test_confidentiality_labels_represented(self):
        payload = _header_footer_watermark_payload(_valid_ctx())
        assert sorted(payload["allowed_confidentiality_labels"]) == sorted(_CONFIDENTIALITY_LABELS)

    def test_watermark_types_represented(self):
        payload = _header_footer_watermark_payload(_valid_ctx())
        assert sorted(payload["allowed_watermark_types"]) == sorted(_WATERMARK_TYPES)

    def test_status_label_present_in_metadata(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["header"]["status_label"] == "DRAFT"

    def test_confidentiality_label_present_in_metadata(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["header"]["confidentiality_label"] == "CONFIDENTIAL"

    def test_page_number_rule_tokens_represented(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-header-footer-watermark-metadata",
        )
        page_number_format = metadata["header_footer_watermark"]["footer"]["page_number_format"]
        assert "{n}" in page_number_format
        assert "{m}" in page_number_format

    def test_page_number_rule_validation_present(self):
        validation = _validate_header_footer_watermark_metadata(_valid_hfw_metadata())
        assert validation["valid"] is True
        assert validation["status"] == "valid"


class TestSourceAndQaFooterPlacement:
    def test_footer_block_role_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-page-block-role="footer_metadata_block"' in html

    def test_footer_break_policy_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-break-policy="keep_together"' in html

    def test_footer_can_split_false_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-can-split="false"' in html

    def test_source_context_qa_footer_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Source context: button1_dossier_handoff" in html

    def test_source_ingest_mode_qa_footer_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Ingest mode: preview_only" in html

    def test_visual_qa_footer_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Visual QA rollup status:" in html

    def test_meta_footer_class_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="meta-footer typography-page-metadata"' in html


class TestHeaderFooterValidationFailClosed:
    def test_missing_hfw_metadata_fails_validation(self):
        validation = _validate_header_footer_watermark_metadata(None)
        assert validation["valid"] is False
        assert validation["status"] == "missing"
        assert "missing_header_footer_watermark_metadata" in validation["issues"]

    def test_invalid_status_label_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["header"]["status_label"] = "BAD"
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "header_invalid_status_label" in validation["issues"]

    def test_invalid_confidentiality_label_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["header"]["confidentiality_label"] = "SECRET"
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "header_invalid_confidentiality_label" in validation["issues"]

    def test_invalid_page_number_format_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["footer"]["page_number_format"] = "Page number only"
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "footer_page_number_format_missing_tokens" in validation["issues"]

    def test_invalid_watermark_type_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["watermark"]["watermark_type"] = "glow"
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "watermark_invalid_watermark_type" in validation["issues"]

    def test_invalid_watermark_opacity_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["watermark"]["watermark_opacity"] = 0.5
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "watermark_invalid_opacity" in validation["issues"]

    def test_missing_watermark_text_for_non_none_type_fails_validation(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["watermark"]["watermark_text"] = ""
        validation = _validate_header_footer_watermark_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "watermark_missing_text_for_non_none_type" in validation["issues"]

    def test_invalid_hfw_metadata_downgrades_certification(self):
        invalid_metadata = _valid_hfw_metadata()
        invalid_metadata["footer"]["page_number_format"] = "Page only"
        html = build_button2_report_html(
            _valid_ctx(
                header_footer_watermark_metadata=invalid_metadata,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Header/footer/watermark metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_missing_hfw_metadata_downgrades_certification(self):
        html = build_button2_report_html(
            _valid_ctx(
                header_footer_watermark_metadata=None,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Header/footer/watermark metadata validation: missing" in html
        assert "Visual certification: not_certified" in html


class TestNoRendererBehaviorChanges:
    def test_hfw_rendering_idempotent(self):
        ctx = _valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata())
        html_one = build_button2_report_html(ctx)["html_content"]
        html_two = build_button2_report_html(ctx)["html_content"]
        assert html_one == html_two

    def test_hfw_rendering_deterministic(self):
        ctx = _valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata())
        result_one = build_button2_report_html(ctx)
        result_two = build_button2_report_html(ctx)
        assert result_one["html_content"] == result_two["html_content"]
        assert result_one["ok"] is True
        assert result_two["ok"] is True

    def test_no_real_paged_media_surface_added(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ].lower()
        assert "@page" not in html
        assert "position: running(" not in html
        assert "element(header)" not in html


class TestNoTypographyHierarchyPageBreakOrChartChanges:
    def test_typography_tokens_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert "typography-page-metadata" in html

    def test_hierarchy_markers_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_page_break_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'data-page-breaks-validation-status="valid"' in html

    def test_chart_metadata_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'data-chart-scenario-validation-status="valid"' in html

    def test_all_metadata_sections_present(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html


class TestSafetyInvariantsPhase2Slice5:
    def test_preview_only_flag_preserved(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["preview_only"] is True

    def test_pdf_generation_flag_false(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["pdf_generation_performed"] is False

    def test_file_write_flag_false(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["file_write_performed"] is False

    def test_export_flag_false(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["export_performed"] is False

    def test_delivery_flag_false(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["delivery_performed"] is False

    def test_html_composition_performed_true(self):
        result = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))
        assert result["html_composition_performed"] is True

    def test_no_interactive_surface_added(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ].lower()
        assert "<button" not in html
        assert "<form" not in html


class TestPhase1BackwardCompatibility:
    def test_phase1_html_structure_unchanged(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert "AI-RISA Premium Fight Report" in html
        assert "fight_header_footer_001" in html

    def test_no_scripts_injected(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ].lower()
        assert "<script" not in html
        assert "http://" not in html
        assert "https://" not in html

    def test_source_traceability_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'id="button2-source-traceability-metadata"' in html

    def test_visual_qa_rollup_section_preserved(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert 'id="button2-visual-qa-rollup-metadata"' in html


class TestHeaderFooterIntegration:
    def test_hfw_schema_matches_allowed_surfaces(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
                "html_content"
            ],
            "button2-header-footer-watermark-metadata",
        )
        assert sorted(metadata["allowed_status_labels"]) == sorted(_STATUS_LABELS)
        assert sorted(metadata["allowed_confidentiality_labels"]) == sorted(_CONFIDENTIALITY_LABELS)
        assert sorted(metadata["allowed_watermark_types"]) == sorted(_WATERMARK_TYPES)

    def test_hfw_metadata_render_facing(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
                "html_content"
            ],
            "button2-header-footer-watermark-metadata",
        )
        assert metadata["header_footer_watermark"]["header"]["status_label"] == "DRAFT"
        assert metadata["header_footer_watermark"]["footer"]["page_number_format"] == "Page {n} of {m}"
        assert metadata["header_footer_watermark"]["watermark"]["watermark_type"] == "draft"

    def test_hfw_layer_does_not_break_page_break_layer(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert "Page-break metadata validation: valid" in html

    def test_hfw_layer_does_not_break_chart_layer(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert "Chart/scenario metadata validation: valid" in html

    def test_all_visual_qa_layers_accounted_for(self):
        html = build_button2_report_html(_valid_ctx(header_footer_watermark_metadata=_valid_hfw_metadata()))[
            "html_content"
        ]
        assert "Hierarchy validation: valid" in html
        assert "Page-break metadata validation: valid" in html
        assert "Chart/scenario metadata validation: valid" in html
        assert "Header/footer/watermark metadata validation: valid" in html
        assert "Source traceability metadata validation:" in html