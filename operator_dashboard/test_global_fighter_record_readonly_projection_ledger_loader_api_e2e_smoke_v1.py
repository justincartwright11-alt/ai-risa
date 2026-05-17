"""E2E smoke: projection-ledger -> source-pack -> loader -> loader API -> Button 1 preview path (v1)."""

import json

import pytest

from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _source_ref(name, typ):
    return {
        "source_name": name,
        "source_type": typ,
        "source_url": "https://example.test/source",
        "source_date": "2026-05-17",
    }


def _projection_row(fid, name, typ, confidence="A", with_refs=True):
    known_record = {
        "fighter_id": fid,
        "fighter_name": name,
        "aliases": [name + " Alias"],
        "country": "US",
        "organization": "UFC",
        "ruleset": "MMA",
        "weight_class": "Middleweight",
        "win_loss_record": {"wins": 10, "losses": 2, "draws": 0},
        "career_years": [2015, 2026],
        "confidence": confidence,
    }
    if with_refs:
        known_record["source_refs"] = [_source_ref(typ + "_source", typ)]

    return {
        "projection": {"known_record": known_record},
        "projection_name": typ + "_projection",
        # Unsafe fields that must not surface in known_records output.
        "database_pointer": "secret",
        "merge_instruction": "secret",
        "write_authorized": True,
        "raw_ledger_internals": {"x": 1},
    }


def _candidate_payload(name, known_records):
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
                    "source_type": "button1_discovery",
                    "source_url": "https://example.test/fight",
                    "source_date": "2026-05-17",
                }
            ],
        },
        "known_records": known_records,
    }


@pytest.mark.parametrize(
    "field_name,source_type,fid,name",
    [
        ("approved_historical_records", "approved_historical", "ah-1", "Sean Strickland"),
        ("result_ledger_records", "result_ledger", "rl-1", "Alex Pereira"),
        ("report_history_records", "report_history", "rh-1", "Tom Aspinall"),
        ("global_read_projection_records", "global_read_projection", "gr-1", "Merab Dvalishvili"),
    ],
)
def test_01_projection_source_flows_end_to_end_via_loader_api(
    client,
    field_name,
    source_type,
    fid,
    name,
):
    payload = {
        field_name: [_projection_row(fid, name, source_type)],
    }

    loader_resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    loader_data = loader_resp.get_json()

    assert loader_resp.status_code == 200
    assert loader_data["ok"] is True
    assert loader_data["source_type"] == "source_pack"
    assert loader_data["records_received_count"] == 1
    assert loader_data["records_accepted_count"] == 1

    rec = loader_data["known_records"][0]
    assert rec["fighter_global_id"] == fid
    assert rec["full_name"] == name
    assert rec["loader_source_type"] == source_type

    # Sanitized known_records remain resolver-compatible and safe.
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec
    assert "raw_ledger_internals" not in rec

    # Smoke the identity resolver preview with loader output.
    resolver_resp = client.post(
        "/api/global-fighters/identity-resolver/preview",
        data=json.dumps(_candidate_payload(name, loader_data["known_records"])),
        content_type="application/json",
    )
    resolver_data = resolver_resp.get_json()

    assert resolver_resp.status_code == 200
    assert resolver_data["ok"] is True
    assert resolver_data["matched_record_id"] == fid

    # All write flags remain false in both envelopes.
    for data in (loader_data, resolver_data):
        assert data["preview_only"] is True
        assert data["profile_create_performed"] is False
        assert data["profile_update_performed"] is False
        assert data["merge_performed"] is False
        assert data["database_write_performed"] is False
        assert data["ranking_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False


def test_02_missing_provenance_or_confidence_fail_closed_through_loader_api(client):
    missing_refs = _projection_row("x1", "No Refs", "approved_historical", with_refs=False)
    missing_conf = _projection_row("x2", "No Confidence", "approved_historical")
    del missing_conf["projection"]["known_record"]["confidence"]

    payload = {
        "approved_historical_records": [missing_refs, missing_conf],
    }

    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["records_received_count"] == 2
    assert data["records_accepted_count"] == 0
    errors = data.get("errors", [])
    assert any("missing required source_refs provenance" in e for e in errors)
    assert any("missing required projection confidence" in e for e in errors)


def test_03_button1_preview_surface_and_dashboard_shape_unchanged(client):
    # Loader endpoint still exists for Button 1 known-records preview path.
    resp = client.post(
        "/api/global-fighters/known-records/loader-preview",
        data=json.dumps({"approved_historical_records": []}),
        content_type="application/json",
    )
    assert resp.status_code == 200

    # Normal dashboard remains 3 buttons / 3 gates.
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert html.count('class="btn-card"') == 3
    assert 'id="b1-btn"' in html
    assert 'id="b2-btn"' in html
    assert 'id="b3-btn"' in html
    assert html.count("Operator Gate") >= 3
