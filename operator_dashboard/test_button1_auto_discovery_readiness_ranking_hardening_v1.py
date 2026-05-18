import copy

import pytest

from operator_dashboard.app import app as flask_app
from operator_dashboard.button1_auto_discovery_readiness_ranking_v1 import (
    build_button1_auto_discovery_readiness_ranking,
)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _base_row():
    return {
        "candidate_id": "base_1",
        "event_name": "Joshua vs Dubois",
        "event_date": "2026-09-21",
        "promotion": "Matchroom Boxing",
        "sport": "boxing",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "source_tier": "A",
        "source_backed": True,
        "provenance_status": "source_backed_ready",
        "card_completeness_status": "full_card_confirmed",
        "matchup_count": 5,
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "button2_readiness_status": "ready_for_button2_preview",
        "queue_save_eligible": True,
        "duplicate_or_conflict": False,
        "needs_review": False,
        "requires_secondary_confirmation": False,
    }


def test_full_card_source_backed_rows_rank_above_headline_only_rows():
    full_card = _base_row()
    headline = copy.deepcopy(full_card)
    headline["candidate_id"] = "headline"
    headline["card_completeness_status"] = "headline_only"
    headline["matchup_count"] = 1

    ranked = build_button1_auto_discovery_readiness_ranking([headline, full_card])
    by_id = {r["candidate_id"]: r for r in ranked}

    assert by_id["base_1"]["readiness_score"] > by_id["headline"]["readiness_score"]
    assert by_id["base_1"]["discovery_rank"] < by_id["headline"]["discovery_rank"]


def test_tier_a_official_source_ranks_above_lower_tier_source_when_equal():
    tier_a = _base_row()
    tier_c = copy.deepcopy(tier_a)
    tier_c["candidate_id"] = "tier_c"
    tier_c["source_tier"] = "C"
    tier_c["source_url"] = "https://www.tapology.com/fightcenter/events/12345"

    ranked = build_button1_auto_discovery_readiness_ranking([tier_c, tier_a])
    by_id = {r["candidate_id"]: r for r in ranked}

    assert by_id["base_1"]["source_quality_score"] > by_id["tier_c"]["source_quality_score"]
    assert by_id["base_1"]["discovery_rank"] < by_id["tier_c"]["discovery_rank"]


def test_missing_source_url_blocks_or_lowers_ranking():
    row = _base_row()
    row["candidate_id"] = "missing_source"
    row["source_url"] = ""
    row["source_backed"] = False

    ranked = build_button1_auto_discovery_readiness_ranking([row])[0]

    assert ranked["readiness_band"] == "blocked"
    assert "source_backed_provenance_required" in ranked["blocking_reasons"]


def test_review_only_muay_thai_secondary_confirmation_row_remains_needs_review():
    row = _base_row()
    row.update(
        {
            "candidate_id": "muay_thai_review",
            "sport": "muay_thai",
            "source_tier": "B",
            "source_url": "https://www.muaythairecords.com/events/one-samurai-1",
            "queue_save_eligible": False,
            "ready_state": "needs_review",
            "requires_secondary_confirmation": True,
        }
    )

    ranked = build_button1_auto_discovery_readiness_ranking([row])[0]

    assert ranked["ready_state"] == "needs_review"
    assert ranked["recommended_operator_action"] in {"review_source", "review_identity"}
    assert "requires_secondary_confirmation" in ranked["ranking_reasons"]


def test_non_source_backed_row_is_blocked():
    row = _base_row()
    row["candidate_id"] = "non_source_backed"
    row["source_backed"] = False
    row["source_url"] = ""

    ranked = build_button1_auto_discovery_readiness_ranking([row])[0]

    assert ranked["readiness_band"] == "blocked"
    assert ranked["recommended_operator_action"] == "review_source"


def test_duplicate_or_conflict_rows_are_downgraded_or_blocked():
    row = _base_row()
    row["candidate_id"] = "duplicate_row"
    row["duplicate_or_conflict"] = True

    ranked = build_button1_auto_discovery_readiness_ranking([row])[0]
    assert ranked["readiness_band"] in {"low", "blocked", "medium"}

    conflict_row = _base_row()
    conflict_row["candidate_id"] = "conflict_row"
    conflict_row["conflict"] = True
    ranked_conflict = build_button1_auto_discovery_readiness_ranking([conflict_row])[0]
    assert ranked_conflict["readiness_band"] == "blocked"


def test_button2_ready_rows_score_higher_than_not_ready_rows():
    ready_row = _base_row()
    not_ready_row = copy.deepcopy(ready_row)
    not_ready_row["candidate_id"] = "not_ready"
    not_ready_row["button2_readiness_status"] = "not_ready"

    ranked = build_button1_auto_discovery_readiness_ranking([ready_row, not_ready_row])
    by_id = {r["candidate_id"]: r for r in ranked}

    assert by_id["base_1"]["button2_report_readiness_score"] > by_id["not_ready"]["button2_report_readiness_score"]
    assert by_id["base_1"]["readiness_score"] > by_id["not_ready"]["readiness_score"]


def test_ranking_is_deterministic():
    rows = [_base_row() for _ in range(3)]
    rows[0]["candidate_id"] = "a"
    rows[1]["candidate_id"] = "b"
    rows[2]["candidate_id"] = "c"
    rows[2]["button2_readiness_status"] = "review_only"

    first = build_button1_auto_discovery_readiness_ranking(rows)
    second = build_button1_auto_discovery_readiness_ranking(rows)

    left = [(r["candidate_id"], r["discovery_rank"], r["readiness_score"]) for r in first]
    right = [(r["candidate_id"], r["discovery_rank"], r["readiness_score"]) for r in second]
    assert left == right


def test_dashboard_payload_includes_rank_and_readiness_fields(client):
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
    workflow = data["workflow"]
    first_job = workflow["jobs"][0]
    payload = first_job["input_ref"]["metadata"]["payload"]
    candidate_rows = payload["candidate_rows"]
    assert candidate_rows

    row = candidate_rows[0]
    for field in [
        "discovery_rank",
        "readiness_score",
        "readiness_band",
        "ranking_reasons",
        "blocking_reasons",
        "recommended_operator_action",
        "source_quality_score",
        "completeness_score",
        "button2_report_readiness_score",
    ]:
        assert field in row


def test_no_queue_write_occurs(client):
    response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
    )
    data = response.get_json()
    telemetry = data.get("telemetry", {})
    assert telemetry["queue_write_performed"] is False


def test_no_pdf_generation_or_delivery_occurs(client):
    response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
    )
    data = response.get_json()
    telemetry = data.get("telemetry", {})
    assert telemetry["report_export_approved"] is False
    assert telemetry["durable_write_performed"] is False


def test_no_learning_or_calibration_occurs(client):
    response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
    )
    data = response.get_json()
    telemetry = data.get("telemetry", {})
    assert telemetry["learning_apply_performed"] is False
    assert telemetry["calibration_write_performed"] is False


def test_no_button3_mutation_occurs(client):
    response = client.post(
        "/api/button1-button2/event-card-matchup/select-preview",
        json={"operator_selected": False, "candidate_rows": []},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["safety_flags"]["button3_mutation_performed"] is False


def test_dashboard_display_includes_ranking_labels(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Readiness Band" in html
    assert "Readiness Score" in html
    assert "Recommended Operator Action" in html
    assert "Key Reasons" in html
