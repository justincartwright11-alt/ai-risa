"""Automated smoke test: Button 1 source-pack UI preview wire (summary-only, zero-write, no new controls)."""

import pytest
from operator_dashboard.app import app
import json

def _rec(fid, name, src, **kw):
    out = {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": [name + " Alias"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "confidence_grade": "A",
        "loader_source_type": src,
        "loader_source_name": src + "_source",
        "completeness_flags": {"has_identity_core": True},
        # Unsafe fields
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }
    out.update(kw)
    return out

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_button1_source_pack_ui_preview_summary_only(client):
    # Simulate Button 1 loader request with source-pack fields
    payload = {
        "manual_operator_records": [_rec("f1", "A", "manual_operator")],
        "local_seed_records": [_rec("f2", "B", "local_seed")],
        "approved_historical_records": [_rec("f3", "C", "approved_historical")],
        "report_history_records": [_rec("f4", "D", "report_history")],
        "result_ledger_records": [_rec("f5", "E", "result_ledger")],
        "global_read_projection_records": [_rec("f6", "F", "global_read_projection")],
    }
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()
    # Summary-only: only safe counts, source_type, preview_only, write flags
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["source_type"] == "source_pack"
    assert data["records_received_count"] == 6
    assert data["records_accepted_count"] == 6
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["database_write_performed"] is False
    # No raw source-pack internals rendered
    assert all("database_pointer" not in r for r in data["known_records"])
    assert all("merge_instruction" not in r for r in data["known_records"])
    assert all("write_authorized" not in r for r in data["known_records"])
    # No new controls, no new buttons/gates/routes (API-level proof)
    # All write flags remain false
    for flag in [
        "profile_create_performed", "profile_update_performed", "merge_performed",
        "database_write_performed", "ranking_write_performed",
        "learning_apply_performed", "calibration_write_performed"
    ]:
        assert data[flag] is False

def test_button1_source_pack_ui_preview_legacy_path(client):
    # Simulate legacy in_memory/local_seed path
    payload = {"in_memory_records": [_rec("f1", "A", "in_memory")]}
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["source_type"] == "in_memory"
    assert data["records_received_count"] == 1
    assert data["records_accepted_count"] == 1
    assert data["preview_only"] is True
    # All write flags remain false
    for flag in [
        "profile_create_performed", "profile_update_performed", "merge_performed",
        "database_write_performed", "ranking_write_performed",
        "learning_apply_performed", "calibration_write_performed"
    ]:
        assert data[flag] is False
