"""
Button 2 Customer PDF - Phase 5 Customer-Ready Status Preview v1

Purpose:
- Validate customer-ready status preview is read-only and uses existing proof outputs.

Governance:
- No delivery workflow changes
- No certification automation
- No approval bypass
- No output-path/file-write/dashboard behavior changes
"""

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_phase5_customer_ready_preview_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Phase 5 customer-ready preview status surface.",
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
        "source_traceability_metadata": {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.org/official",
                    "source_date": "2026-05-18",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        },
        "overlap_proof": {"status": "present"},
        "off_page_text_proof": {"status": "present"},
        "visual_certification_status": "certified",
    }
    base.update(overrides)
    return base


def test_customer_ready_preview_row_present():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert "Customer-ready status preview:" in html
    assert "Gate: operator_approval_required" in html


def test_customer_ready_recommended_when_ready_and_certified():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert "Customer-ready status preview: customer_ready_recommended" in html


def test_customer_ready_not_ready_when_fail_closed_or_not_certified():
    html = build_button2_report_html(
        _valid_ctx(
            source_traceability_metadata=None,
            visual_certification_status="certified",
        )
    )["html_content"]
    assert "Customer-ready status preview: customer_ready_not_ready" in html
    assert "Visual certification: not_certified" in html


def test_no_delivery_certification_controls_or_mutation_endpoints_added():
    html = build_button2_report_html(_valid_ctx())["html_content"].lower()
    assert "deliver now" not in html
    assert "auto certify" not in html
    assert "certification automation" not in html
    assert "/api/" not in html


def test_no_approval_output_file_write_dashboard_changes():
    result = build_button2_report_html(_valid_ctx())
    html = result["html_content"].lower()
    assert result["preview_only"] is True
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert "<button" not in html
    assert "<form" not in html
