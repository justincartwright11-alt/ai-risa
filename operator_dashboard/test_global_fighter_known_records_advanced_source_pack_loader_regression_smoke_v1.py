"""Evidence-only regression smoke for advanced source-pack preview normalization (v1)."""

import json

import pytest

from operator_dashboard.app import app
from operator_dashboard.global_fighter_known_records_readonly_loader import (
    load_known_records_readonly_preview,
)


ADVANCED_CASES = [
    (
        "approved_historical_records",
        "approved_historical",
        {
            "projection": {
                "known_record": {
                    "fighter_id": "ah-1",
                    "fighter_name": "Sean Strickland",
                    "aliases": ["Tarzan"],
                    "country": "US",
                    "organization": "UFC",
                    "ruleset": "MMA",
                    "weight_class": "Middleweight",
                    "confidence": "A",
                }
            },
            "source_name": "approved_history_projection",
            "database_pointer": "hidden",
            "write_authorized": True,
        },
    ),
    (
        "report_history_records",
        "report_history",
        {
            "projection_name": "report_history_projection",
            "projection": {
                "fighter_uuid": "rh-1",
                "display_name": "Alex Pereira",
                "nicknames": ["Poatan"],
                "nation": "BR",
                "promotion_name": "UFC",
                "sport": "MMA",
                "division": "Light Heavyweight",
                "confidence": "B",
            },
            "merge_instruction": "forbidden",
        },
    ),
    (
        "result_ledger_records",
        "result_ledger",
        {
            "known_record": {
                "global_fighter_id": "rl-1",
                "name": "Merab Dvalishvili",
                "aliases": ["The Machine"],
                "country": "GE",
                "organization": "UFC",
                "ruleset": "MMA",
                "weight_class": "Bantamweight",
                "identity_confidence_grade": "A",
            },
            "write_authorized": True,
        },
    ),
    (
        "global_read_projection_records",
        "global_read_projection",
        {
            "projection": {
                "known_record": {
                    "fighter_global_id": "gdb-1",
                    "full_name": "Tom Aspinall",
                    "known_aliases": ["Honey Badger"],
                    "nationality": "UK",
                    "promotion": "UFC",
                    "sport_ruleset": "MMA",
                    "division": "Heavyweight",
                    "confidence_grade": "A",
                }
            },
            "loader_source_name": "global_db_projection",
            "database_pointer": "should_not_leak",
        },
    ),
]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("field_name,expected_source,projection_row", ADVANCED_CASES)
def test_loader_advanced_projection_sources_normalize_to_resolver_known_records(
    field_name,
    expected_source,
    projection_row,
):
    kwargs = {field_name: [projection_row]}

    result = load_known_records_readonly_preview(**kwargs)

    assert result.preview_only is True
    assert result.source_type == "source_pack"
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert result.malformed_records_count == 0

    rec = result.known_records[0]
    assert rec["fighter_global_id"]
    assert rec["full_name"]
    assert rec["loader_source_type"] == expected_source
    assert isinstance(rec.get("known_aliases", []), list)
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec

    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False


@pytest.mark.parametrize("field_name,expected_source,projection_row", ADVANCED_CASES)
def test_loader_api_preview_advanced_projection_sources_are_safe(
    client,
    field_name,
    expected_source,
    projection_row,
):
    payload = {field_name: [projection_row]}

    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )

    data = resp.get_json()
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["source_type"] == "source_pack"
    assert data["records_received_count"] == 1
    assert data["records_accepted_count"] == 1

    rec = data["known_records"][0]
    assert rec["fighter_global_id"]
    assert rec["full_name"]
    assert rec["loader_source_type"] == expected_source
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec

    for flag in [
        "profile_create_performed",
        "profile_update_performed",
        "merge_performed",
        "database_write_performed",
        "ranking_write_performed",
        "learning_apply_performed",
        "calibration_write_performed",
    ]:
        assert data[flag] is False


def test_button1_ui_wire_and_dashboard_shape_remain_stable(client):
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)

    assert 'id="b1-btn"' in html
    assert 'id="b2-btn"' in html
    assert 'id="b3-btn"' in html
    assert html.count('class="btn-card"') == 3
    assert html.count("Operator Gate") >= 3
