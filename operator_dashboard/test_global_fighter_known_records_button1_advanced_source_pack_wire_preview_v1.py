"""Focused tests for Button 1 advanced source-pack wire (preview-only, zero-write)."""

import json

import pytest

from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _advanced_projection_row(fid: str, name: str):
    return {
        "projection": {
            "known_record": {
                "fighter_id": fid,
                "fighter_name": name,
                "aliases": [name + " Alias"],
                "country": "US",
                "organization": "UFC",
                "ruleset": "MMA",
                "weight_class": "Middleweight",
                "confidence": "A",
                "source_refs": [
                    {
                        "source_name": "projection_source",
                        "source_type": "projection",
                        "source_url": "https://example.test/source",
                        "source_date": "2026-05-17",
                    }
                ],
            }
        },
        "source_name": "projection_source",
        # Unsafe internals that must not survive to known_records output.
        "database_pointer": "must_not_leak",
        "merge_instruction": "must_not_leak",
        "write_authorized": True,
    }


def test_button1_template_wires_advanced_source_pack_fields_without_new_controls(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "function buildButton1AdvancedSourcePackFields(workflowData)" in html
    assert "approved_historical_records" in html
    assert "report_history_records" in html
    assert "result_ledger_records" in html
    assert "global_read_projection_records" in html
    assert "buildButton1AdvancedSourcePackFields(result.workflowData)" in html
    assert "postGlobalFighterKnownRecordsLoaderPreview(sourcePackFields)" in html

    # Normal dashboard remains unchanged: exactly 3 buttons and operator gates.
    assert html.count('class="btn-card"') == 3
    assert 'id="b1-btn"' in html
    assert 'id="b2-btn"' in html
    assert 'id="b3-btn"' in html
    assert "Operator Gate" in html
    assert html.count("Operator Gate") >= 3
    assert 'id="b4-btn"' not in html


@pytest.mark.parametrize(
    "field_name,expected_source",
    [
        ("approved_historical_records", "approved_historical"),
        ("report_history_records", "report_history"),
        ("result_ledger_records", "result_ledger"),
        ("global_read_projection_records", "global_read_projection"),
    ],
)
def test_loader_preview_accepts_each_advanced_field_with_safe_summary(
    client,
    field_name,
    expected_source,
):
    payload = {
        field_name: [_advanced_projection_row("adv-1", "Sean Strickland")],
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
    assert data["records_received_count"] == 1
    assert data["records_accepted_count"] == 1

    rec = data["known_records"][0]
    assert rec["fighter_global_id"] == "adv-1"
    assert rec["full_name"] == "Sean Strickland"
    assert rec["loader_source_type"] == expected_source

    # Raw/internal/write fields are excluded from rendered known_records.
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec

    # Preview-only and zero-write invariants.
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
