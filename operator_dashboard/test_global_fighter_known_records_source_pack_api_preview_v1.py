"""API tests: source-pack mode in known-records loader API (v1)."""

import json
import pytest
from operator_dashboard.app import app

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

def test_01_api_accepts_all_six_source_pack_fields(client):
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
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["source_type"] == "source_pack"
    assert data["records_received_count"] == 6
    assert data["records_accepted_count"] == 6
    assert all("database_pointer" not in r for r in data["known_records"])
    assert all("merge_instruction" not in r for r in data["known_records"])
    assert all("write_authorized" not in r for r in data["known_records"])
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["database_write_performed"] is False

def test_02_api_legacy_in_memory_and_local_seed_paths(client):
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
    payload2 = {"local_seed_records": [_rec("f2", "B", "local_seed")]}
    resp2 = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload2),
        content_type="application/json",
    )
    data2 = resp2.get_json()
    assert resp2.status_code == 200
    assert data2["ok"] is True
    assert data2["source_type"] == "local_seed"
    assert data2["records_received_count"] == 1
    assert data2["records_accepted_count"] == 1

def test_03_api_precedence_and_dedupe(client):
    high = _rec("f1", "Anderson Silva", "manual_operator", promotion="UFC")
    low = _rec("f1", "Anderson Silva", "global_read_projection", promotion="Bellator")
    payload = {
        "manual_operator_records": [high],
        "global_read_projection_records": [low],
    }
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["records_accepted_count"] == 1
    rec = data["known_records"][0]
    assert rec["promotion"] == "UFC"
    assert rec["loader_source_type"] == "manual_operator"

def test_04_api_malformed_rows_fail_closed(client):
    payload = {"manual_operator_records": [{"full_name": "Missing ID"}, "not-a-dict", None]}
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["records_received_count"] == 3
    assert data["records_accepted_count"] == 0
    assert data["malformed_records_count"] == 3

def test_05_api_all_write_flags_remain_false(client):
    payload = {"manual_operator_records": [_rec("f1", "A", "manual_operator")]}
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
