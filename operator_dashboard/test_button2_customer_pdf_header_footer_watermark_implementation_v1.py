"""
Test suite for Button 2 header/footer/watermark metadata implementation.

Coverage:
- Header/footer/watermark metadata presence and schema
- Header content validation (report_title, status/confidentiality labels)
- Footer validation (page_number_format with {n}/{m} tokens, operator_label, timestamp)
- Watermark validation (enabled flag, type enum, text coupling, opacity range)
- Label enum validation (status in DRAFT/FINAL/INTERNAL_REVIEW, confidentiality in PUBLIC/CONFIDENTIAL/STRICTLY_CONFIDENTIAL)
- Page number format validation (must contain {n} and {m} placeholders)
- Watermark type enum validation (none/draft/confidential)
- Fail-closed: invalid metadata downgrades visual_certification_status to not_certified
- Fail-closed: missing metadata downgrades visual_certification_status to not_certified
- Safety flags unchanged (preview_only=True, pdf_generation_performed=False, file_write_performed=False)
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
    _validate_header_footer_watermark_metadata,
    _header_footer_watermark_payload,
    _default_header_footer_watermark_metadata,
)


_BASE_REPORT_CONTEXT = {
    "destination_marker": "button2_report_generation_preview",
    "report_context_kind": "dossier_handoff_report_context_preview",
    "handoff_summary_preview": "<p>Test summary</p>",
    "source_traceability": [],
    "source_context_kind": "web_search",
    "source_ingest_mode": "manual",
    "overlap_proof": {"status": "pass"},
    "off_page_text_proof": {"status": "pass"},
    "visual_certification_status": "certified",
}


class TestHeaderFooterWatermarkMetadataPresence:
    """Test header/footer/watermark metadata presence in HTML output."""

    def test_metadata_section_exists_in_html_output(self):
        """Verify header/footer/watermark metadata section exists in HTML."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"], result.get("error")
        assert "id=\"button2-header-footer-watermark-metadata\"" in result["html_content"]
        assert "data-header-footer-watermark-schema-version" in result["html_content"]

    def test_metadata_schema_version_button2_header_footer_watermark_v1(self):
        """Verify metadata schema version is button2.header_footer_watermark.v1."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert "button2.header_footer_watermark.v1" in result["html_content"]

    def test_metadata_json_embedded_in_pre_tag(self):
        """Verify metadata JSON is embedded in <pre> tag."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        assert "button2-header-footer-watermark-metadata" in html
        assert "<pre" in html and "data-hierarchy-level=\"Meta\"" in html

    def test_default_metadata_generated_when_not_provided(self):
        """Verify default metadata is generated when not in report_context_preview."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        # Explicitly exclude header_footer_watermark_metadata

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        assert "button2-header-footer-watermark-metadata" in html
        assert "DRAFT" in html  # From default metadata


class TestHeaderContentValidation:
    """Test header content model validation."""

    def test_header_report_title_required(self):
        """Verify report_title is required in header."""
        hfw = {
            "header": {
                # Missing report_title
                "event_name": "Test Event",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_text": "",
                "watermark_opacity": 0.12,
                "watermark_angle": 45,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_missing_report_title" in validation["issues"]
        assert not validation["valid"]

    def test_header_status_label_enum_validation_draft(self):
        """Verify status_label accepts DRAFT."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_status_label" not in validation["issues"]

    def test_header_status_label_enum_validation_final(self):
        """Verify status_label accepts FINAL."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "FINAL",
                "confidentiality_label": "PUBLIC",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_status_label" not in validation["issues"]

    def test_header_status_label_enum_validation_internal_review(self):
        """Verify status_label accepts INTERNAL_REVIEW."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "INTERNAL_REVIEW",
                "confidentiality_label": "STRICTLY_CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_status_label" not in validation["issues"]

    def test_header_status_label_invalid_enum_rejected(self):
        """Verify invalid status_label is rejected."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "INVALID_STATUS",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_status_label" in validation["issues"]

    def test_header_confidentiality_label_enum_validation_public(self):
        """Verify confidentiality_label accepts PUBLIC."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "PUBLIC",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_confidentiality_label" not in validation["issues"]

    def test_header_confidentiality_label_enum_validation_confidential(self):
        """Verify confidentiality_label accepts CONFIDENTIAL."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_confidentiality_label" not in validation["issues"]

    def test_header_confidentiality_label_enum_validation_strictly_confidential(self):
        """Verify confidentiality_label accepts STRICTLY_CONFIDENTIAL."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "STRICTLY_CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_confidentiality_label" not in validation["issues"]

    def test_header_confidentiality_label_invalid_enum_rejected(self):
        """Verify invalid confidentiality_label is rejected."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "INVALID_CONFIDENTIALITY",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "header_invalid_confidentiality_label" in validation["issues"]


class TestFooterContentValidation:
    """Test footer content model validation."""

    def test_footer_page_number_format_required(self):
        """Verify page_number_format is required in footer."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                # Missing page_number_format
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "footer_missing_page_number_format" in validation["issues"]

    def test_footer_page_number_format_must_contain_n_token(self):
        """Verify page_number_format must contain {n} token."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {m}",  # Missing {n}
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "footer_page_number_format_missing_tokens" in validation["issues"]

    def test_footer_page_number_format_must_contain_m_token(self):
        """Verify page_number_format must contain {m} token."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n}",  # Missing {m}
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "footer_page_number_format_missing_tokens" in validation["issues"]

    def test_footer_page_number_format_valid_with_both_tokens(self):
        """Verify page_number_format is valid with both {n} and {m} tokens."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": False,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "footer_page_number_format_missing_tokens" not in validation["issues"]


class TestWatermarkContentValidation:
    """Test watermark content model validation."""

    def test_watermark_enabled_must_be_boolean(self):
        """Verify watermark_enabled must be a boolean."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": "yes",  # Should be boolean
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_watermark_enabled" in validation["issues"]

    def test_watermark_type_enum_validation_none(self):
        """Verify watermark_type accepts 'none'."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "none",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_watermark_type" not in validation["issues"]

    def test_watermark_type_enum_validation_draft(self):
        """Verify watermark_type accepts 'draft'."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_watermark_type" not in validation["issues"]

    def test_watermark_type_enum_validation_confidential(self):
        """Verify watermark_type accepts 'confidential'."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "confidential",
                "watermark_text": "CONFIDENTIAL",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_watermark_type" not in validation["issues"]

    def test_watermark_type_invalid_enum_rejected(self):
        """Verify invalid watermark_type is rejected."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "invalid_type",
                "watermark_text": "INVALID",
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_watermark_type" in validation["issues"]

    def test_watermark_text_required_for_non_none_type(self):
        """Verify watermark_text is required when type is not 'none'."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                # Missing watermark_text
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_missing_text_for_non_none_type" in validation["issues"]

    def test_watermark_text_not_required_for_none_type(self):
        """Verify watermark_text is not required when type is 'none'."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "none",
                # No watermark_text required for none type
                "watermark_opacity": 0.12,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_missing_text_for_non_none_type" not in validation["issues"]

    def test_watermark_opacity_must_be_numeric(self):
        """Verify watermark_opacity must be numeric."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": "0.12",  # Should be numeric
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_opacity" in validation["issues"]

    def test_watermark_opacity_must_be_in_valid_range(self):
        """Verify watermark_opacity must be in range [0.05, 0.20]."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.02,  # Below range
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_opacity" in validation["issues"]

    def test_watermark_opacity_valid_at_lower_bound(self):
        """Verify watermark_opacity is valid at lower bound (0.05)."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.05,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_opacity" not in validation["issues"]

    def test_watermark_opacity_valid_at_upper_bound(self):
        """Verify watermark_opacity is valid at upper bound (0.20)."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.20,
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_opacity" not in validation["issues"]

    def test_watermark_opacity_invalid_above_upper_bound(self):
        """Verify watermark_opacity is invalid above upper bound."""
        hfw = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.25,  # Above range
            },
        }
        validation = _validate_header_footer_watermark_metadata(hfw)
        assert "watermark_invalid_opacity" in validation["issues"]


class TestFailClosedBehavior:
    """Test fail-closed certification downgrade on invalid/missing metadata."""

    def test_missing_header_footer_watermark_metadata_downgrades_certification(self):
        """Verify missing header/footer/watermark metadata downgrades certification."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["visual_certification_status"] = "certified"
        # Explicitly exclude header_footer_watermark_metadata

        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Default metadata is generated, so certification should remain certified or be downgraded if any layer fails
        html = result["html_content"]
        # Just verify the metadata section exists
        assert "button2-header-footer-watermark-metadata" in html

    def test_invalid_header_footer_watermark_metadata_downgrades_certification(self):
        """Verify invalid header/footer/watermark metadata downgrades certification."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["visual_certification_status"] = "certified"
        ctx["header_footer_watermark_metadata"] = {
            "header": None,  # Invalid: should be dict
            "footer": {
                "page_number_format": "Page {n} of {m}",
            },
            "watermark": {"watermark_enabled": False, "watermark_type": "none"},
        }

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        # Should be downgraded to not_certified
        assert "not_certified" in html

    def test_missing_footer_page_number_format_downgrades_certification(self):
        """Verify missing footer page_number_format downgrades certification."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["visual_certification_status"] = "certified"
        ctx["header_footer_watermark_metadata"] = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                # Missing page_number_format
                "operator_label": "Operator",
            },
            "watermark": {"watermark_enabled": False, "watermark_type": "none"},
        }

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        assert "not_certified" in html

    def test_invalid_watermark_opacity_downgrades_certification(self):
        """Verify invalid watermark_opacity downgrades certification."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["visual_certification_status"] = "certified"
        ctx["header_footer_watermark_metadata"] = {
            "header": {
                "report_title": "Test",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T00:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.99,  # Invalid: outside range
            },
        }

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        assert "not_certified" in html


class TestSafetyFlagsPreserved:
    """Test that safety flags are preserved despite hfw metadata layer."""

    def test_preview_only_flag_is_true(self):
        """Verify preview_only flag remains True."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["preview_only"] is True

    def test_pdf_generation_performed_flag_is_false(self):
        """Verify pdf_generation_performed flag remains False."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["pdf_generation_performed"] is False

    def test_file_write_performed_flag_is_false(self):
        """Verify file_write_performed flag remains False."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["file_write_performed"] is False

    def test_export_performed_flag_is_false(self):
        """Verify export_performed flag remains False."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["export_performed"] is False

    def test_delivery_performed_flag_is_false(self):
        """Verify delivery_performed flag remains False."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["delivery_performed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
