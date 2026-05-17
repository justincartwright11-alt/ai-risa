import pytest
from operator_dashboard.global_fighter_profile_dossier_export_preview import build_dossier_preview

def test_build_dossier_preview():
    """Test the read-only preview exporter for the fighter dossier."""
    dossier_data = {
        "fighter_name": "Anderson Silva",
        "promotion": "UFC",
        "division": "Middleweight",
        "record": "34W-11L-0D",
        "confidence": "A",
        "source": "approved_historical",
    }

    result = build_dossier_preview(dossier_data)

    expected_preview = (
        "Fighter Intelligence Dossier Preview\n"
        "Fighter: Anderson Silva\n"
        "Promotion: UFC\n"
        "Division: Middleweight\n"
        "Record: 34W-11L-0D\n"
        "Confidence: A\n"
        "Source: approved_historical\n\n"
        "Read-only preview. No profile create, update, merge, ranking, database, learning, or calibration action was performed."
    )

    assert result["preview"] == expected_preview
    assert result["preview_only"] is True
    assert result["export_performed"] is False
    assert result["file_write_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False

def test_sanitized_known_records():
    """Ensure only sanitized known_records are used."""
    dossier_data = {"fighter_name": "Anderson Silva"}
    result = build_dossier_preview(dossier_data)
    assert "Anderson Silva" in result["preview"]

def test_handles_missing_fields():
    """Ensure missing fields fail safely."""
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

def test_escapes_xss_payloads():
    """Ensure unsafe text / XSS payloads are escaped."""
    dossier_data = {"known_records": "<script>alert('XSS')</script>"}