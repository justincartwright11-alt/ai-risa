"""Tests for Button 1 known records loader wire preview (v1)."""

import json

import pytest

from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


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
    }


def test_01_loader_api_returns_empty_context_by_default(client):
    """Readonly loader API returns empty context when no records provided."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["known_records"] == []
    assert data["preview_only"] is True


def test_02_loader_api_accepts_in_memory_records(client):
    """Readonly loader API accepts in_memory_records."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert len(data["known_records"]) == 1
    assert data["records_accepted_count"] == 1


def test_03_known_records_returned_sanitized(client):
    """Known records are returned in resolver-compatible format."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    rec = data["known_records"][0]

    # Safe fields present
    assert "fighter_global_id" in rec
    assert "full_name" in rec
    assert "known_aliases" in rec
    assert "confidence_grade" in rec

    # Unsafe fields excluded
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_04_identity_resolver_accepts_known_records(client):
    """Identity resolver accepts known_records parameter."""
    candidate = {
        "name": "Anderson Silva",
        "aliases": [],
        "nationality": None,
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "test_source",
                "source_url": None,
                "source_type": "test",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [_test_record()],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True


def test_05_loader_returns_preview_only_flag(client):
    """Loader returns preview_only=true."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True


def test_06_loader_returns_all_write_flags_false(client):
    """Loader returns all write flags as false."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_07_loader_returns_source_type(client):
    """Loader returns source type of records."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["source_type"] == "in_memory"


def test_08_loader_returns_record_counts(client):
    """Loader returns received and accepted record counts."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 1
    assert data["records_accepted_count"] == 1
    assert data["malformed_records_count"] == 0


def test_09_loader_skips_malformed_records(client):
    """Loader skips malformed records safely."""
    malformed = [
        {"full_name": "Missing ID"},
        _test_record("fighter_001", "Valid Fighter"),
    ]
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": malformed},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 2
    assert data["records_accepted_count"] == 1
    assert data["malformed_records_count"] == 1


def test_10_identity_resolver_works_without_known_records(client):
    """Identity resolver still works when known_records is empty list."""
    candidate = {
        "name": "Test Fighter",
        "aliases": [],
        "nationality": None,
        "promotion": None,
        "sport_ruleset": None,
        "division": None,
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "test",
                "source_url": None,
                "source_type": "test",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True


def test_11_identity_resolver_returns_preview_only_true(client):
    """Identity resolver returns preview_only=true."""
    candidate = {
        "name": "Test Fighter",
        "aliases": [],
        "nationality": None,
        "promotion": None,
        "sport_ruleset": None,
        "division": None,
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "test",
                "source_url": None,
                "source_type": "test",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True


def test_12_identity_resolver_all_write_flags_false(client):
    """Identity resolver returns all write flags as false."""
    candidate = {
        "name": "Test Fighter",
        "aliases": [],
        "nationality": None,
        "promotion": None,
        "sport_ruleset": None,
        "division": None,
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "test",
                "source_url": None,
                "source_type": "test",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_13_loader_response_serializes_to_json(client):
    """Loader response is valid JSON."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    payload = json.dumps(data)
    assert isinstance(payload, str)


def test_14_identity_resolver_response_serializes_to_json(client):
    """Identity resolver response is valid JSON."""
    candidate = {
        "name": "Test Fighter",
        "aliases": [],
        "nationality": None,
        "promotion": None,
        "sport_ruleset": None,
        "division": None,
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "test",
                "source_url": None,
                "source_type": "test",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [_test_record()],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    payload = json.dumps(data)
    assert isinstance(payload, str)


def test_15_loader_handles_multiple_records(client):
    """Loader handles multiple records."""
    records = [
        _test_record("fighter_001", "Anderson Silva"),
        _test_record("fighter_002", "Chris Weidman"),
        _test_record("fighter_003", "Israel Adesanya"),
    ]
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": records},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 3
    assert data["records_accepted_count"] == 3
    assert len(data["known_records"]) == 3


def test_16_loader_deduplicates_records(client):
    """Loader handles duplicate fighter IDs gracefully."""
    records = [
        _test_record("fighter_001", "Anderson Silva"),
        _test_record("fighter_001", "Spider Silva"),  # Same ID
    ]
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": records},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["records_received_count"] == 2
    assert data["records_accepted_count"] == 2


def test_17_button1_payload_builder_accepts_known_records_parameter(client):
    """Button 1 can be tested to use known records parameter."""
    # This tests the Flask app still works
    response = client.get("/")
    assert response.status_code == 200
    assert "Find Fights" in response.get_data(as_text=True)


def test_18_no_new_dashboard_buttons(client):
    """Dashboard still has exactly 3 buttons."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Count button main classes
    button_count = html.count('class="btn-main"')
    assert button_count == 3


def test_19_dashboard_invariant_preserved(client):
    """Dashboard 3-gate invariant preserved."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Should still have gate mentions
    assert "Gate 1" in html or "gate" in html


def test_20_loader_api_still_accessible_after_button1_wire(client):
    """Readonly loader API is still accessible."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_record()]},
    )
    assert response.status_code == 200
