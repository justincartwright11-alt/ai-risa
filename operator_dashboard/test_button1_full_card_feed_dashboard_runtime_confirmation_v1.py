"""Dashboard runtime confirmation for Button 1 full-card feed population (v1)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _run_button1_runtime_preview(client):
    response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={
            "source_button": "button1_find_fights",
            "use_runtime_context": True,
            "execute_preview": True,
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    return data


def _extract_candidate_rows(workflow_preview_response):
    workflow = workflow_preview_response["workflow"]
    first_job = workflow["jobs"][0]
    payload = first_job["input_ref"]["metadata"]["payload"]
    candidate_rows = payload["candidate_rows"]
    assert isinstance(candidate_rows, list)
    return candidate_rows


def _event_rows_by_name(candidate_rows):
    event_rows = {}
    for row in candidate_rows:
        event_name = str(row.get("event_name", "")).strip()
        if not event_name:
            continue
        if isinstance(row.get("matchups"), list):
            event_rows[event_name] = row
    return event_rows


def test_dashboard_root_exposes_button1_full_card_ui_surface(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Source-Backed Event Cards" in html
    assert "id=\"b1-event-cards-list\"" in html
    assert "handleButton1Click()" in html
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in html
    assert "<strong>Card Completeness:</strong>" in html
    assert "<strong>Matchup Count:</strong>" in html
    assert "Select for PDF" in html


def test_button1_runtime_preview_returns_four_full_card_confirmed_events(client):
    preview = _run_button1_runtime_preview(client)
    candidate_rows = _extract_candidate_rows(preview)
    events = _event_rows_by_name(candidate_rows)

    assert set(events.keys()) == {
        "Joshua vs Dubois",
        "UFC 300",
        "GLORY 100",
        "ONE SAMURAI 1",
    }

    for event in events.values():
        assert event["card_completeness_status"] == "full_card_confirmed"


def test_button1_runtime_preview_preserves_full_matchup_counts_per_event(client):
    preview = _run_button1_runtime_preview(client)
    candidate_rows = _extract_candidate_rows(preview)
    events = _event_rows_by_name(candidate_rows)

    expected_counts = {
        "Joshua vs Dubois": 5,
        "UFC 300": 5,
        "GLORY 100": 5,
        "ONE SAMURAI 1": 15,
    }

    for event_name, expected in expected_counts.items():
        row = events[event_name]
        matchups = row["matchups"]
        assert row["matchup_count"] == expected
        assert row["expected_matchup_count"] == expected
        assert len(matchups) == expected


def test_button1_runtime_preview_full_matchup_rows_remain_source_backed(client):
    preview = _run_button1_runtime_preview(client)
    candidate_rows = _extract_candidate_rows(preview)
    events = _event_rows_by_name(candidate_rows)

    for event_name, row in events.items():
        assert row["source_backed"] is True
        assert row["preview_only"] is True
        assert row["approval_required"] is True
        assert str(row["source_url"]).startswith("https://")

        for matchup in row["matchups"]:
            assert matchup["source_backed"] is True, f"source_backed=False in {event_name}"
            assert str(matchup["source_url"]).startswith("https://"), (
                f"missing source_url in {event_name}"
            )


def test_tier_a_queue_save_eligibility_and_muay_thai_review_governance_hold(client):
    preview = _run_button1_runtime_preview(client)
    candidate_rows = _extract_candidate_rows(preview)
    events = _event_rows_by_name(candidate_rows)

    for event_name in ("Joshua vs Dubois", "UFC 300", "GLORY 100"):
        row = events[event_name]
        assert row["queue_save_eligible"] is True
        assert row["source_tier"] == "A"
        for matchup in row["matchups"]:
            assert matchup["queue_save_eligible"] is True

    muay_thai = events["ONE SAMURAI 1"]
    assert muay_thai["queue_save_eligible"] is False
    assert muay_thai["requires_secondary_confirmation"] is True
    assert muay_thai["unsafe_queue_save_blocked"] is True
