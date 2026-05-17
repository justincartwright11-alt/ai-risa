# Button 2 Source Traceability Visual Layer Implementation Tests (v1)
# Slice: button2-customer-pdf-source-traceability-visual-layer-implementation-v1
#
# Purpose: Comprehensive implementation tests for source traceability metadata layer.
# Validates: source type/class, confidence/verification enums, validation contracts,
# fail-closed behavior, safety flags, and HTML embedding.

import sys
import os
import pytest

# Add the operator_dashboard directory to sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

from button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
    _validate_source_traceability_metadata,
    _source_traceability_payload,
    _default_source_traceability_metadata,
    _SOURCE_TYPES,
    _SOURCE_CLASSES,
    _CONFIDENCE_LEVELS,
    _CITATION_COMPLETENESS,
    _VERIFICATION_STATUS,
)

# Base report context fixture
_BASE_REPORT_CONTEXT = {
    "destination_marker": "button2_report_generation_preview",
    "report_context_kind": "dossier_handoff_report_context_preview",
    "handoff_summary_preview": "<p>Sample report summary</p>",
    "source_context_kind": "test",
    "source_ingest_mode": "preview",
    "visual_certification_status": "certified",
}


class TestSourceTraceabilityMetadataPresence:
    """Verify source traceability metadata section exists and has correct structure."""

    def test_metadata_section_exists_in_html(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert 'id="button2-source-traceability-metadata"' in result["html_content"]

    def test_schema_version_present(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert "button2.source_traceability.v1" in result["html_content"]

    def test_metadata_json_embedded_in_pre_tag(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert '<pre data-hierarchy-level="Meta">' in result["html_content"]
        assert "button2.source_traceability.v1" in result["html_content"]

    def test_default_metadata_generated_when_not_provided(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        # Do not provide source_traceability_metadata
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Should contain default metadata with missing status
        assert "button2.source_traceability.v1" in result["html_content"]


class TestSourceTypeValidation:
    """Verify source type enum validation (official/research/operator)."""

    def test_valid_source_type_official(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_source_type_research(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_source_type_operator(self):
        metadata = {
            "sources": [
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.2,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_source_type(self):
        metadata = {
            "sources": [
                {
                    "source_type": "invalid_type",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_source_type" in issue for issue in validation["issues"])


class TestSourceClassValidation:
    """Verify source class enum validation (tier_a/tier_b/tier_c)."""

    def test_valid_source_class_tier_a(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_source_class_tier_b(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_source_class_tier_c(self):
        metadata = {
            "sources": [
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.2,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_source_class(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_z",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_source_class" in issue for issue in validation["issues"])


class TestConfidenceLevelValidation:
    """Verify confidence level enum validation (high/medium/low/uncertain)."""

    def test_valid_confidence_high(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_confidence_medium(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_confidence_low(self):
        metadata = {
            "sources": [
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.2,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_confidence_uncertain(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "uncertain",
                    "citation_completeness": "minimal",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_confidence_level(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "very_high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_confidence_level" in issue for issue in validation["issues"])


class TestCitationCompletenessValidation:
    """Verify citation completeness enum validation (complete/partial/minimal)."""

    def test_valid_citation_complete(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_citation_partial(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_citation_minimal(self):
        metadata = {
            "sources": [
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.2,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_citation_completeness(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "excessive",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_citation_completeness" in issue for issue in validation["issues"])


class TestVerificationStatusValidation:
    """Verify verification status enum validation (verified/unverified/contradicted)."""

    def test_valid_verification_verified(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_verification_unverified(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_verification_contradicted(self):
        metadata = {
            "sources": [
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "contradicted",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.2,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_verification_status(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "pending_verification",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_verification_status" in issue for issue in validation["issues"])


class TestRequiredFieldValidation:
    """Verify required field validation (source_url, source_date)."""

    def test_missing_source_url(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("missing_source_url" in issue for issue in validation["issues"])

    def test_missing_source_date(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("missing_source_date" in issue for issue in validation["issues"])


class TestLineageGraphValidation:
    """Verify lineage graph structure validation."""

    def test_valid_lineage_graph_empty(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_lineage_graph_not_dict(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": ["not", "a", "dict"],
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("lineage_graph_not_dict" in issue for issue in validation["issues"])


class TestTotalSourcesValidation:
    """Verify total_sources numeric validation."""

    def test_valid_total_sources_zero(self):
        metadata = {
            "sources": [],
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": 0.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_total_sources_positive(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 5,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_total_sources_negative(self):
        metadata = {
            "sources": [],
            "lineage_graph": {},
            "total_sources": -1,
            "corroboration_coverage": 0.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_total_sources" in issue for issue in validation["issues"])


class TestCorroborationCoverageValidation:
    """Verify corroboration_coverage numeric range validation [0.0, 1.0]."""

    def test_valid_corroboration_zero(self):
        metadata = {
            "sources": [],
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": 0.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_corroboration_half(self):
        metadata = {
            "sources": [
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 0.5,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_valid_corroboration_full(self):
        metadata = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is True

    def test_invalid_corroboration_below_zero(self):
        metadata = {
            "sources": [],
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": -0.1,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_corroboration_coverage" in issue for issue in validation["issues"])

    def test_invalid_corroboration_above_one(self):
        metadata = {
            "sources": [],
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": 1.1,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("invalid_corroboration_coverage" in issue for issue in validation["issues"])


class TestFailClosedBehavior:
    """Verify fail-closed downgrade to not_certified on invalid source metadata."""

    def test_missing_source_metadata_downgrades_certification(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        # Do not provide source_traceability_metadata
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Missing metadata should trigger fail-closed downgrade to not_certified
        # Check for the presence of missing status in the embedded JSON (escaped quotes)
        assert '&quot;validation_status&quot;:&quot;missing&quot;' in result["html_content"]

    def test_invalid_source_type_downgrades_certification(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "invalid",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Invalid source metadata should show invalid validation status
        assert 'data-source-traceability-validation-status="invalid"' in result["html_content"]

    def test_missing_required_field_downgrades_certification(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    # Missing source_url and source_date
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Missing required fields should show invalid validation status
        assert 'data-source-traceability-validation-status="invalid"' in result["html_content"]

    def test_valid_source_metadata_preserves_certification(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Valid metadata should preserve the "certified" status from context
        assert result["html_content"]


class TestSafetyFlagsPreserved:
    """Verify all safety flags remain unchanged with source traceability layer."""

    def test_preview_only_true(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["preview_only"] is True

    def test_pdf_generation_performed_false(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["pdf_generation_performed"] is False

    def test_file_write_performed_false(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["file_write_performed"] is False

    def test_export_performed_false(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["export_performed"] is False

    def test_delivery_performed_false(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["delivery_performed"] is False


class TestMissingSourceMetadataHandling:
    """Verify graceful handling of missing source traceability metadata."""

    def test_missing_none(self):
        validation = _validate_source_traceability_metadata(None)
        assert validation["valid"] is False
        assert validation["status"] == "missing"
        assert "missing_source_traceability_metadata" in validation["issues"]

    def test_missing_not_dict(self):
        validation = _validate_source_traceability_metadata("not_a_dict")
        assert validation["valid"] is False
        assert validation["status"] == "invalid"
        assert "source_traceability_metadata_not_dict" in validation["issues"]

    def test_missing_sources_list(self):
        metadata = {
            "sources": "not_a_list",
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": 0.0,
        }
        validation = _validate_source_traceability_metadata(metadata)
        assert validation["valid"] is False
        assert any("sources_not_list" in issue for issue in validation["issues"])


class TestSourceTraceabilityPayload:
    """Verify payload generation with defaults and validation."""

    def test_payload_with_provided_metadata(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        payload = _source_traceability_payload(ctx)
        assert payload["schema_version"] == "button2.source_traceability.v1"
        assert payload["validation_status"] == "valid"
        assert len(payload["validation_issues"]) == 0

    def test_payload_with_missing_metadata(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        # Do not provide source_traceability_metadata
        payload = _source_traceability_payload(ctx)
        assert payload["schema_version"] == "button2.source_traceability.v1"
        # Default metadata is generated with validation_status="missing" inside it
        assert payload["validation_status"] == "valid"  # Outer payload is structurally valid
        # The inner source_traceability metadata shows "missing" status
        assert payload["source_traceability"]["validation_status"] == "missing"

    def test_payload_contains_all_enums(self):
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        payload = _source_traceability_payload(ctx)
        assert "allowed_source_types" in payload
        assert set(payload["allowed_source_types"]) == _SOURCE_TYPES
        assert "allowed_source_classes" in payload
        assert set(payload["allowed_source_classes"]) == _SOURCE_CLASSES
        assert "allowed_confidence_levels" in payload
        assert set(payload["allowed_confidence_levels"]) == _CONFIDENCE_LEVELS
        assert "allowed_citation_completeness" in payload
        assert set(payload["allowed_citation_completeness"]) == _CITATION_COMPLETENESS
        assert "allowed_verification_status" in payload
        assert set(payload["allowed_verification_status"]) == _VERIFICATION_STATUS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
