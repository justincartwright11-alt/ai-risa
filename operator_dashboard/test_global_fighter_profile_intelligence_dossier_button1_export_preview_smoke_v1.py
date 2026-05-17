import pytest
from operator_dashboard.global_fighter_profile_dossier_export_preview import build_dossier_preview

def test_realistic_dossier_data():
    """Ensure realistic Button 1 dossier data produces copy-safe summary text."""
    dossier_data = {
        "fighter_name": "Jon Jones",
        "promotion": "UFC",
        "division": "Light Heavyweight",
        "record": "27W-1L-0D",
        "confidence": "A+",
        "source": "trusted_historical",
    }

    result = build_dossier_preview(dossier_data)

    expected_preview = (
        "Fighter Intelligence Dossier Preview\n"
        "Fighter: Jon Jones\n"
        "Promotion: UFC\n"
        "Division: Light Heavyweight\n"
        "Record: 27W-1L-0D\n"
        "Confidence: A+\n"
        "Source: trusted_historical\n\n"
        "Read-only preview. No profile create, update, merge, ranking, database, learning, or calibration action was performed."
    )

    assert result["preview"] == expected_preview
    assert result["preview_only"] is True
    assert result["export_performed"] is False
    assert result["file_write_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False

def test_missing_fields_fail_safe():
    """Ensure missing fields fail safe."""
    dossier_data = {}
    result = build_dossier_preview(dossier_data)
    expected_preview = (
        "Fighter Intelligence Dossier Preview\n"
        "Fighter: Unknown Fighter\n"
        "Promotion: Unknown Promotion\n"
        "Division: Unknown Division\n"
        "Record: 0W-0L-0D\n"
        "Confidence: Unknown\n"
        "Source: Unknown Source\n\n"
        "Read-only preview. No profile create, update, merge, ranking, database, learning, or calibration action was performed."
    )
    assert result["preview"] == expected_preview

def test_html_xss_payloads_escaped():
    """Ensure HTML/XSS payloads are escaped or excluded."""
    dossier_data = {
        "fighter_name": "<script>alert('XSS')</script>",
        "promotion": "<b>UFC</b>",
        "division": "<i>Light Heavyweight</i>",
        "record": "27W-1L-0D",
        "confidence": "A+",
        "source": "trusted_historical",
    }

    result = build_dossier_preview(dossier_data)

    assert "<script>" not in result["preview"]
    assert "<b>" not in result["preview"]
    assert "<i>" not in result["preview"]
    assert "alert('XSS')" not in result["preview"]

def test_no_raw_internal_fields_leaked():
    """Ensure raw/internal/write fields are not leaked."""
    dossier_data = {
        "fighter_name": "Jon Jones",
        "internal_notes": "Sensitive data",
        "write_flag": True,
    }

    result = build_dossier_preview(dossier_data)

    assert "internal_notes" not in result["preview"]
    assert "Sensitive data" not in result["preview"]
    assert "write_flag" not in result["preview"]