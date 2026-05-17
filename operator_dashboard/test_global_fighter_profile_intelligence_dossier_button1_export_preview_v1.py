import pytest
from operator_dashboard.global_fighter_profile_dossier_export_preview import build_dossier_preview

def test_build_dossier_preview():
    """Test the read-only preview exporter for the fighter dossier."""
    dossier_data = {
        "known_records": "sanitized_data",
        "projection_ledger": "sanitized_data",
    }

    result = build_dossier_preview(dossier_data)

    assert result["preview"] == "Copy-safe summary text"
    assert result["preview_only"] is True
    assert result["export_performed"] is False
    assert result["file_write_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False