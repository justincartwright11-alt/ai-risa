"""
Button 2 Customer PDF - Phase 6 Controlled Export Preview v1

Purpose:
- Validate controlled export/download preview is read-only and safety-gated.

Governance:
- No customer delivery automation
- No certification automation
- No approval bypass
- No new unsafe write path
"""

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_phase6_controlled_export_preview_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Phase 6 controlled export preview status surface.",
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


def test_controlled_export_eligible_only_when_customer_ready_recommended():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert "Customer-ready status preview: customer_ready_recommended" in html
    assert "Controlled export preview: controlled_export_eligible_pending_operator_approval" in html


def test_controlled_export_not_eligible_when_not_customer_ready():
    html = build_button2_report_html(
        _valid_ctx(source_traceability_metadata=None, visual_certification_status="certified")
    )["html_content"]
    assert "Customer-ready status preview: customer_ready_not_ready" in html
    assert "Controlled export preview: controlled_export_not_eligible" in html


def test_operator_gate_and_server_derived_path_policy_present():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert "Gate: operator_approval_required" in html
    assert "Output path policy: server_derived_output_path_required" in html


def test_no_delivery_automation_certification_or_bypass_controls_added():
    html = build_button2_report_html(_valid_ctx())["html_content"].lower()
    assert "deliver now" not in html
    assert "auto certify" not in html
    assert "certification automation" not in html
    assert "bypass approval" not in html
    assert "/api/" not in html


def test_no_new_write_or_dashboard_behavior_changes():
    result = build_button2_report_html(_valid_ctx())
    html = result["html_content"].lower()
    assert result["preview_only"] is True
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert "<button" not in html
    assert "<form" not in html
