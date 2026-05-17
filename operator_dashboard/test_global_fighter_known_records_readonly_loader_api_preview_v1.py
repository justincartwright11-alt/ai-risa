"""Tests for readonly known fighter records loader API preview (v1)."""

import json
import socket

import pytest

from operator_dashboard.app import app


def _test_record(fid: str = "fighter_001", name: str = "Anderson Silva"):
    return {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": ["The Spider"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "confidence_grade": "A",
        "loader_source_type": "test",
        "loader_source_name": "test_seed",
        "completeness_flags": {"has_identity_core": True},
        # Unsafe fields that must be excluded
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_01_route_exists(client):
    """POST /api/global-fighters/known-records/loader-preview route is accessible."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={},
    )
    assert response.status_code in (200, 400)


def test_02_in_memory_records_load_and_sanitize(client):
    """In-memory records load and are sanitized."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["records_received_count"] == 1
    assert data["records_accepted_count"] == 1
    assert len(data["known_records"]) == 1


def test_03_local_seed_records_load_and_sanitize(client):
    """Local seed records load and are sanitized."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"local_seed_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["source_type"] == "local_seed"
    assert data["records_accepted_count"] == 1


def test_04_in_memory_takes_priority_over_local_seed(client):
    """In-memory records take priority over local seed records."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={
            "in_memory_records": [_test_record("fighter_001", "Memory Fighter")],
            "local_seed_records": [_test_record("fighter_002", "Seed Fighter")],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["source_type"] == "in_memory"
    assert data["known_records"][0]["full_name"] == "Memory Fighter"


def test_05_empty_request_returns_empty_safe_context(client):
    """Empty request returns empty safe context."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["known_records"] == []
    assert data["records_received_count"] == 0
    assert data["source_type"] == "empty"


def test_06_raw_internal_write_fields_excluded(client):
    """Raw/internal/write fields are excluded from response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    rec = data["known_records"][0]

    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_07_provenance_fields_preserved(client):
    """Provenance fields are preserved in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    rec = data["known_records"][0]

    assert rec.get("loader_source_type") == "test"
    assert rec.get("loader_source_name") == "test_seed"


def test_08_completeness_hints_preserved(client):
    """Completeness hints are preserved in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    rec = data["known_records"][0]

    assert rec["completeness_flags"] == {"has_identity_core": True}


def test_09_malformed_records_skipped_fail_closed(client):
    """Malformed records are skipped and fail closed."""
    malformed = [
        {"full_name": "Missing ID"},
        {"fighter_global_id": "fighter_002"},
        "not-an-object",
    ]
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": malformed},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 3
    assert data["records_accepted_count"] == 0
    assert data["malformed_records_count"] == 3
    assert data["known_records"] == []


def test_10_mixed_valid_invalid_keep_only_valid(client):
    """Mixed valid/invalid records keeps only valid ones."""
    mixed = [
        _test_record("fighter_001", "Valid Fighter"),
        {"full_name": "Missing ID"},
        _test_record("fighter_003", "Another Valid"),
    ]
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": mixed},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 3
    assert data["records_accepted_count"] == 2
    assert data["malformed_records_count"] == 1


def test_11_response_serializes_to_json(client):
    """Response is valid JSON."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    payload = json.dumps(data)
    assert isinstance(payload, str)


def test_12_profile_create_performed_false(client):
    """profile_create_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_create_performed"] is False


def test_13_profile_update_performed_false(client):
    """profile_update_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_update_performed"] is False


def test_14_merge_performed_false(client):
    """merge_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["merge_performed"] is False


def test_15_database_write_performed_false(client):
    """database_write_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["database_write_performed"] is False


def test_16_ranking_write_performed_false(client):
    """ranking_write_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ranking_write_performed"] is False


def test_17_learning_apply_performed_false(client):
    """learning_apply_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["learning_apply_performed"] is False


def test_18_calibration_write_performed_false(client):
    """calibration_write_performed is false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["calibration_write_performed"] is False


def test_19_route_performs_no_filesystem_writes(client, monkeypatch):
    """Route performs no filesystem writes."""
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    assert opened_for_write == []


def test_20_route_performs_no_live_web_calls(client, monkeypatch):
    """Route performs no live web calls."""
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200


def test_21_invalid_in_memory_records_type_rejected(client):
    """Invalid in_memory_records type is rejected."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": "not-a-list"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False


def test_22_invalid_local_seed_records_type_rejected(client):
    """Invalid local_seed_records type is rejected."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"local_seed_records": "not-a-list"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False


def test_23_invalid_request_body_type_gracefully_handled(client):
    """Invalid request body type is gracefully handled as empty context."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data="not-json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["known_records"] == []


def test_24_preview_only_always_true(client):
    """preview_only is always true in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True
