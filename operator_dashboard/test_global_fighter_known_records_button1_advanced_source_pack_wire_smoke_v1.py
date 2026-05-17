"""Evidence smoke: Button 1 advanced source-pack wire through loader + identity preview (v1)."""

import json

import pytest

from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _projection_row(fid: str, fighter_name: str, source_label: str):
    return {
        "projection": {
            "known_record": {
                "fighter_id": fid,
                "fighter_name": fighter_name,
                "aliases": [fighter_name + " Alias"],
                "country": "US",
                "organization": "UFC",
                "ruleset": "MMA",
                "weight_class": "Middleweight",
                "confidence": "A",
            }
        },
        "projection_name": source_label,
        # Unsafe internals that must never appear in known_records output.
        "database_pointer": "internal-only",
        "merge_instruction": "internal-only",
        "write_authorized": True,
    }


def _candidate_payload(name: str):
    return {
        "candidate": {
            "name": name,
            "aliases": [],
            "nationality": "US",
            "promotion": "UFC",
            "sport_ruleset": "MMA",
            "division": "Middleweight",
            "source_refs": [
                {
                    "source_name": "button1_discovery",
                    "source_url": "https://example.com/fight",
                    "source_type": "button1_discovery",
                    "source_date": "2026-05-17",
                }
            ],
        }
    }


@pytest.mark.parametrize(
    "field_name,expected_source",
    [
        ("approved_historical_records", "approved_historical"),
        ("report_history_records", "report_history"),
        ("result_ledger_records", "result_ledger"),
        ("global_read_projection_records", "global_read_projection"),
    ],
)
def test_button1_advanced_source_pack_field_flows_loader_to_identity_preview_safely(
    client,
    field_name,
    expected_source,
):
    fighter_name = "Sean Strickland"
    loader_payload = {field_name: [_projection_row("adv-100", fighter_name, field_name)]}

    # 1) Loader API receives advanced source-pack field and returns sanitized known_records.
    loader_resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(loader_payload),
        content_type="application/json",
    )
    loader_data = loader_resp.get_json()

    assert loader_resp.status_code == 200
    assert loader_data["ok"] is True
    assert loader_data["source_type"] == "source_pack"
    assert loader_data["records_received_count"] == 1
    assert loader_data["records_accepted_count"] == 1

    loaded = loader_data["known_records"][0]
    assert loaded["fighter_global_id"] == "adv-100"
    assert loaded["full_name"] == fighter_name
    assert loaded["loader_source_type"] == expected_source

    # Source-pack output remains sanitized.
    assert "database_pointer" not in loaded
    assert "merge_instruction" not in loaded
    assert "write_authorized" not in loaded

    # 2) Identity resolver preview with no known records (baseline).
    baseline_payload = _candidate_payload(fighter_name)
    baseline_payload["known_records"] = []
    baseline_resp = client.post(
        "/api/global-fighters/identity-resolver/preview",
        data=json.dumps(baseline_payload),
        content_type="application/json",
    )
    baseline_data = baseline_resp.get_json()
    assert baseline_resp.status_code == 200
    assert baseline_data["ok"] is True

    # 3) Identity resolver preview with loaded known records (advanced context).
    enriched_payload = _candidate_payload(fighter_name)
    enriched_payload["known_records"] = loader_data["known_records"]
    enriched_resp = client.post(
        "/api/global-fighters/identity-resolver/preview",
        data=json.dumps(enriched_payload),
        content_type="application/json",
    )
    enriched_data = enriched_resp.get_json()

    assert enriched_resp.status_code == 200
    assert enriched_data["ok"] is True
    assert enriched_data["matched_record_id"] == "adv-100"
    assert enriched_data["confidence_tier"] is not None

    # Identity confidence can improve using advanced records.
    assert float(enriched_data.get("match_score", 0.0)) >= float(baseline_data.get("match_score", 0.0))

    # All write flags remain false across loader and resolver preview envelopes.
    for data in (loader_data, enriched_data):
        assert data["preview_only"] is True
        assert data["profile_create_performed"] is False
        assert data["profile_update_performed"] is False
        assert data["merge_performed"] is False
        assert data["database_write_performed"] is False
        assert data["ranking_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False


def test_button1_dashboard_remains_summary_only_three_buttons_three_gates(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Normal dashboard remains 3 buttons / 3 gates.
    assert html.count('class="btn-card"') == 3
    assert 'id="b1-btn"' in html
    assert 'id="b2-btn"' in html
    assert 'id="b3-btn"' in html
    assert html.count("Operator Gate") >= 3

    # No additional write-control surface appears on normal dashboard.
    assert 'id="b4-btn"' not in html
    assert 'id="profile-create-btn"' not in html
    assert 'id="profile-update-btn"' not in html
    assert 'id="profile-merge-btn"' not in html
    assert 'id="database-write-btn"' not in html
    assert 'id="ranking-write-btn"' not in html
