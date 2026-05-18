"""
Button 2 Customer PDF - Phase 2 Slice 6 - Source-Link Rendering Foundation Tests

Purpose:
- Validate source traceability/citation metadata remains render-facing
- Verify official/research/operator source types and AI-RISA source classes remain represented
- Verify citation/source labels and source footer placement remain represented
- Verify traceability QA metadata remains represented
- Verify invalid source metadata fails closed to not_certified

Governance:
- Source-link rendering foundation ONLY
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
    _CITATION_COMPLETENESS,
    _SOURCE_CLASSES,
    _SOURCE_TYPES,
    _VERIFICATION_STATUS,
    _source_traceability_payload,
    _validate_source_traceability_metadata,
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_source_link_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Source Link Rendering Foundation: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-18"},
            {"id": "SRC-002", "type": "research", "date": "2026-05-18"},
            {"id": "SRC-003", "type": "operator", "date": "2026-05-18"},
        ],
        "source_traceability_metadata": {
            "sources": [
                {
                    "source_id": "SRC-001",
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com/official",
                    "source_date": "2026-05-18",
                },
                {
                    "source_id": "SRC-002",
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com/research",
                    "source_date": "2026-05-18",
                },
                {
                    "source_id": "SRC-003",
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com/operator",
                    "source_date": "2026-05-18",
                },
            ],
            "lineage_graph": {
                "nodes": ["SRC-001", "SRC-002", "SRC-003"],
                "edges": [["SRC-001", "SRC-002"], ["SRC-002", "SRC-003"]],
            },
            "total_sources": 3,
            "corroboration_coverage": 0.66,
        },
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


class TestSourceTraceabilityRenderFacing:
    def test_source_metadata_section_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-source-traceability-metadata"' in html

    def test_source_schema_version_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-source-traceability-schema-version="button2.source_traceability.v1"' in html

    def test_source_validation_status_render_facing(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-source-traceability-validation-status="valid"' in html

    def test_source_metadata_json_parseable(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        assert metadata["schema_version"] == "button2.source_traceability.v1"
        assert metadata["validation_status"] == "valid"

    def test_traceability_validation_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Source traceability metadata validation: valid" in html


class TestSourceTypesAndClassesRepresentation:
    def test_allowed_source_types_represented(self):
        payload = _source_traceability_payload(_valid_ctx())
        assert sorted(payload["allowed_source_types"]) == sorted(_SOURCE_TYPES)

    def test_allowed_source_classes_represented(self):
        payload = _source_traceability_payload(_valid_ctx())
        assert sorted(payload["allowed_source_classes"]) == sorted(_SOURCE_CLASSES)

    def test_official_source_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_types = [s["source_type"] for s in metadata["source_traceability"]["sources"]]
        assert "official" in src_types

    def test_research_source_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_types = [s["source_type"] for s in metadata["source_traceability"]["sources"]]
        assert "research" in src_types

    def test_operator_source_type_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_types = [s["source_type"] for s in metadata["source_traceability"]["sources"]]
        assert "operator" in src_types

    def test_ai_risa_source_classes_tier_a_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_classes = [s["source_class"] for s in metadata["source_traceability"]["sources"]]
        assert "tier_a" in src_classes

    def test_ai_risa_source_classes_tier_b_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_classes = [s["source_class"] for s in metadata["source_traceability"]["sources"]]
        assert "tier_b" in src_classes

    def test_ai_risa_source_classes_tier_c_present(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        src_classes = [s["source_class"] for s in metadata["source_traceability"]["sources"]]
        assert "tier_c" in src_classes


class TestCitationAndSourceLabelsRepresentation:
    def test_source_citations_label_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-hierarchy-title="Source Citations"' in html

    def test_source_traceability_section_role_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="page-block-sources"' in html
        assert 'data-page-block-role="sources_calibration_block"' in html

    def test_source_traceability_list_contains_official_label(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "SRC-001" in html
        assert "official" in html

    def test_source_traceability_list_contains_research_label(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "SRC-002" in html
        assert "research" in html

    def test_source_traceability_list_contains_operator_label(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "SRC-003" in html
        assert "operator" in html

    def test_citation_completeness_values_represented(self):
        payload = _source_traceability_payload(_valid_ctx())
        assert sorted(payload["allowed_citation_completeness"]) == sorted(_CITATION_COMPLETENESS)

    def test_verification_status_values_represented(self):
        payload = _source_traceability_payload(_valid_ctx())
        assert sorted(payload["allowed_verification_status"]) == sorted(_VERIFICATION_STATUS)


class TestSourceFooterPlacementAndQa:
    def test_source_footer_meta_block_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="meta-footer typography-page-metadata"' in html
        assert 'data-page-block-role="footer_metadata_block"' in html

    def test_source_context_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Source context: button1_dossier_handoff" in html

    def test_source_ingest_mode_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Ingest mode: preview_only" in html

    def test_source_traceability_qa_row_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Source traceability metadata validation: valid" in html

    def test_source_section_break_policy_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-break-policy="split_by_chunk"' in html

    def test_source_section_can_split_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-can-split="true"' in html

    def test_source_section_chunk_size_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-chunk-size="10"' in html


class TestSourceValidationFailClosed:
    def test_valid_source_metadata_passes_validation(self):
        validation = _validate_source_traceability_metadata(
            _valid_ctx()["source_traceability_metadata"]
        )
        assert validation["valid"] is True
        assert validation["status"] == "valid"

    def test_missing_source_metadata_fails_validation(self):
        validation = _validate_source_traceability_metadata(None)
        assert validation["valid"] is False
        assert validation["status"] == "missing"
        assert "missing_source_traceability_metadata" in validation["issues"]

    def test_invalid_source_type_fails_validation(self):
        invalid_metadata = _valid_ctx()["source_traceability_metadata"]
        invalid_metadata["sources"][0]["source_type"] = "newswire"
        validation = _validate_source_traceability_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "source_0_invalid_source_type" in validation["issues"]

    def test_invalid_source_class_fails_validation(self):
        invalid_metadata = _valid_ctx()["source_traceability_metadata"]
        invalid_metadata["sources"][0]["source_class"] = "tier_z"
        validation = _validate_source_traceability_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "source_0_invalid_source_class" in validation["issues"]

    def test_missing_source_url_fails_validation(self):
        invalid_metadata = _valid_ctx()["source_traceability_metadata"]
        invalid_metadata["sources"][0]["source_url"] = ""
        validation = _validate_source_traceability_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "source_0_missing_source_url" in validation["issues"]

    def test_invalid_lineage_graph_fails_validation(self):
        invalid_metadata = _valid_ctx()["source_traceability_metadata"]
        invalid_metadata["lineage_graph"] = []
        validation = _validate_source_traceability_metadata(invalid_metadata)
        assert validation["valid"] is False
        assert "lineage_graph_not_dict" in validation["issues"]

    def test_invalid_source_metadata_downgrades_certification(self):
        invalid_metadata = _valid_ctx()["source_traceability_metadata"]
        invalid_metadata["sources"][0]["source_type"] = "newswire"
        html = build_button2_report_html(
            _valid_ctx(
                source_traceability_metadata=invalid_metadata,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Source traceability metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_missing_source_metadata_downgrades_certification(self):
        html = build_button2_report_html(
            _valid_ctx(
                source_traceability_metadata=None,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Source traceability metadata validation: missing" in html
        assert "Visual certification: not_certified" in html


class TestNoRendererBehaviorChanges:
    def test_source_rendering_idempotent(self):
        ctx = _valid_ctx()
        html_one = build_button2_report_html(ctx)["html_content"]
        html_two = build_button2_report_html(ctx)["html_content"]
        assert html_one == html_two

    def test_source_rendering_deterministic(self):
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


class TestNoTypographyHierarchyPageBreakChartOrHfwChanges:
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


class TestSafetyInvariantsPhase2Slice6:
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


class TestPhase1BackwardCompatibility:
    def test_phase1_html_structure_unchanged(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "AI-RISA Premium Fight Report" in html
        assert "fight_source_link_001" in html

    def test_no_scripts_injected(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "<script" not in html
        assert '<link rel="stylesheet"' not in html

    def test_visual_qa_rollup_section_preserved(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-visual-qa-rollup-metadata"' in html


class TestSourceLayerIntegration:
    def test_source_schema_matches_allowed_surfaces(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        assert sorted(metadata["allowed_source_types"]) == sorted(_SOURCE_TYPES)
        assert sorted(metadata["allowed_source_classes"]) == sorted(_SOURCE_CLASSES)

    def test_source_metadata_render_facing(self):
        metadata = _extract_metadata_json(
            build_button2_report_html(_valid_ctx())["html_content"],
            "button2-source-traceability-metadata",
        )
        assert metadata["source_traceability"]["total_sources"] == 3
        assert metadata["source_traceability"]["corroboration_coverage"] == 0.66

    def test_source_layer_does_not_break_other_layers(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Hierarchy validation: valid" in html
        assert "Page-break metadata validation: valid" in html
        assert "Chart/scenario metadata validation: valid" in html
        assert "Header/footer/watermark metadata validation: valid" in html

    def test_all_visual_qa_layers_accounted_for(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Source traceability metadata validation: valid" in html
        assert "Visual QA rollup status:" in html
