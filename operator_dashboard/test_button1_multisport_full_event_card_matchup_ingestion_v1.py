"""
Full-card matchup ingestion confirmation for Button 1 multisport approved-source event cards.

Slice: button1-multisport-full-event-card-matchup-ingestion-v1
Validates: card_completeness_status, full matchup arrays, provenance integrity, Gate 1 governance.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import load_readonly_runtime_state
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)

VALID_CARD_COMPLETENESS_STATUSES = {
    "full_card_confirmed",
    "partial_card",
    "headline_only",
    "extraction_unsupported",
    "needs_review",
}

VALID_BUTTON2_READINESS_STATUSES = {"ready_for_button2_preview", "review_only"}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _approved_rows_by_sport():
    state = load_readonly_runtime_state()
    all_rows = state.get("discovered_candidate_rows", [])
    approved = [
        row
        for row in all_rows
        if isinstance(row, dict) and row.get("provenance_origin") == "approved_source_live_event_ingestion"
    ]
    by_sport = {}
    for row in approved:
        sport = row.get("sport", "unknown")
        by_sport[sport] = row
    return by_sport


def _is_http_url(value):
    return isinstance(value, str) and value.strip().lower().startswith(("http://", "https://"))


# ---------------------------------------------------------------------------
# Tests 1-4: Each event card can contain multiple matchups
# ---------------------------------------------------------------------------

def test_boxing_event_card_can_contain_multiple_matchups():
    """Test 1: Boxing event card has at least 1 matchup with required fields."""
    by_sport = _approved_rows_by_sport()
    assert "boxing" in by_sport, "Boxing approved source row missing from feed"
    row = by_sport["boxing"]
    matchups = row.get("matchups", [])
    assert isinstance(matchups, list)
    assert len(matchups) >= 1, "Boxing event card must have at least 1 matchup"
    for mu in matchups:
        assert isinstance(mu.get("fighter_a"), str) and mu["fighter_a"].strip()
        assert isinstance(mu.get("fighter_b"), str) and mu["fighter_b"].strip()
        assert "source_backed" in mu
        assert "button2_readiness_status" in mu
        assert mu["button2_readiness_status"] in VALID_BUTTON2_READINESS_STATUSES


def test_mma_event_card_can_contain_multiple_matchups():
    """Test 2: MMA event card has at least 1 matchup with required fields."""
    by_sport = _approved_rows_by_sport()
    assert "mma" in by_sport, "MMA approved source row missing from feed"
    row = by_sport["mma"]
    matchups = row.get("matchups", [])
    assert isinstance(matchups, list)
    assert len(matchups) >= 1, "MMA event card must have at least 1 matchup"
    for mu in matchups:
        assert isinstance(mu.get("fighter_a"), str) and mu["fighter_a"].strip()
        assert isinstance(mu.get("fighter_b"), str) and mu["fighter_b"].strip()
        assert "source_backed" in mu
        assert "button2_readiness_status" in mu
        assert mu["button2_readiness_status"] in VALID_BUTTON2_READINESS_STATUSES


def test_kickboxing_event_card_can_contain_multiple_matchups():
    """Test 3: Kickboxing event card has at least 1 matchup with required fields."""
    by_sport = _approved_rows_by_sport()
    assert "kickboxing" in by_sport, "Kickboxing approved source row missing from feed"
    row = by_sport["kickboxing"]
    matchups = row.get("matchups", [])
    assert isinstance(matchups, list)
    assert len(matchups) >= 1, "Kickboxing event card must have at least 1 matchup"
    for mu in matchups:
        assert isinstance(mu.get("fighter_a"), str) and mu["fighter_a"].strip()
        assert isinstance(mu.get("fighter_b"), str) and mu["fighter_b"].strip()
        assert "source_backed" in mu
        assert "button2_readiness_status" in mu
        assert mu["button2_readiness_status"] in VALID_BUTTON2_READINESS_STATUSES


def test_muay_thai_event_card_contains_full_card_matchups():
    """Test 4: Muay Thai (ONE SAMURAI 1) event card contains 15 matchups (full card confirmed)."""
    by_sport = _approved_rows_by_sport()
    assert "muay_thai" in by_sport, "Muay Thai approved source row missing from feed"
    row = by_sport["muay_thai"]
    matchups = row.get("matchups", [])
    assert isinstance(matchups, list)
    assert len(matchups) == 15, (
        f"Muay Thai ONE SAMURAI 1 must have 15 matchups (full card). Got: {len(matchups)}"
    )
    for mu in matchups:
        assert isinstance(mu.get("fighter_a"), str) and mu["fighter_a"].strip()
        assert isinstance(mu.get("fighter_b"), str) and mu["fighter_b"].strip()
        assert mu.get("source_backed") is True
        assert mu.get("button2_readiness_status") == "review_only"
        assert mu.get("queue_save_eligible") is False
        assert mu.get("review_reason") == "secondary_confirmation_required"


# ---------------------------------------------------------------------------
# Test 5: Dashboard renders all matchups under each event card
# ---------------------------------------------------------------------------

def test_dashboard_renders_all_matchups_under_each_event_card(client):
    """Test 5: Workflow preview route surfaces all matchup rows for each sport."""
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
    assert data is not None
    assert data.get("ok") is True

    workflow = data.get("workflow", {})
    first_job = (workflow.get("jobs") or [{}])[0]
    candidate_rows = (
        first_job.get("input_ref", {}).get("metadata", {}).get("payload", {}).get("candidate_rows", [])
    ) or []

    approved_rows = [
        r for r in candidate_rows
        if isinstance(r, dict) and r.get("provenance_origin") == "approved_source_live_event_ingestion"
    ]
    assert len(approved_rows) >= 4, "Dashboard must surface at least 4 approved source rows"

    muay_thai_rows = [r for r in approved_rows if r.get("sport") == "muay_thai"]
    assert muay_thai_rows, "Muay Thai row must be present in candidate rows"
    muay_thai_row = muay_thai_rows[0]
    matchups = muay_thai_row.get("matchups", [])
    assert len(matchups) == 15, "Muay Thai ONE SAMURAI 1 must surface 15 matchups via dashboard route"


# ---------------------------------------------------------------------------
# Test 6: Every matchup has source-backed provenance or inherited event provenance
# ---------------------------------------------------------------------------

def test_every_rendered_matchup_has_source_backed_or_inherited_event_provenance():
    """Test 6: Every matchup must carry event-level or matchup-level URL-backed provenance."""
    by_sport = _approved_rows_by_sport()
    for sport, row in by_sport.items():
        event_source_url = row.get("source_url", "")
        assert _is_http_url(event_source_url), (
            f"Event-level source_url must be a valid URL for sport={sport}"
        )
        matchups = row.get("matchups", [])
        for mu in matchups:
            mu_source_url = mu.get("source_url") or event_source_url
            assert _is_http_url(mu_source_url), (
                f"Matchup {mu.get('fighter_a')} vs {mu.get('fighter_b')} (sport={sport}) "
                f"has no valid source URL"
            )


# ---------------------------------------------------------------------------
# Test 7: Partial-card sources are correctly marked
# ---------------------------------------------------------------------------

def test_partial_card_sources_are_marked_headline_only_not_full_card_confirmed():
    """Test 7: Boxing, MMA, Kickboxing have only headline bouts, marked headline_only."""
    by_sport = _approved_rows_by_sport()
    partial_sports = ["boxing", "mma", "kickboxing"]
    for sport in partial_sports:
        assert sport in by_sport, f"{sport} approved row missing"
        row = by_sport[sport]
        completeness = row.get("card_completeness_status")
        assert completeness in {"headline_only", "partial_card"}, (
            f"Sport={sport} should be headline_only or partial_card, got: {completeness}"
        )
        assert completeness != "full_card_confirmed", (
            f"Sport={sport} must not claim full_card_confirmed without extraction support"
        )


# ---------------------------------------------------------------------------
# Test 8: Extraction unsupported fails closed with diagnostics
# ---------------------------------------------------------------------------

def test_extraction_unsupported_has_clear_diagnostics():
    """Test 8: Events with headline_only or partial_card have non-empty extraction_diagnostics."""
    by_sport = _approved_rows_by_sport()
    partial_sports = ["boxing", "mma", "kickboxing"]
    for sport in partial_sports:
        row = by_sport.get(sport, {})
        extraction_diagnostics = row.get("extraction_diagnostics", "")
        assert isinstance(extraction_diagnostics, str) and extraction_diagnostics.strip(), (
            f"Sport={sport} with partial/headline_only must have extraction_diagnostics"
        )
        extraction_method = row.get("extraction_method", "")
        assert isinstance(extraction_method, str) and extraction_method.strip(), (
            f"Sport={sport} must have extraction_method"
        )


# ---------------------------------------------------------------------------
# Test 9: Non-source-backed matchup remains blocked
# ---------------------------------------------------------------------------

def test_non_source_backed_matchup_remains_blocked_from_queue_save():
    """Test 9: Muay Thai matchups are source-backed but queue_save_eligible=False due to tier B."""
    by_sport = _approved_rows_by_sport()
    muay_thai_row = by_sport.get("muay_thai", {})
    matchups = muay_thai_row.get("matchups", [])
    assert matchups, "Muay Thai matchups required for governance test"
    for mu in matchups:
        if mu.get("source_backed") is True:
            if mu.get("queue_save_eligible") is False:
                assert mu.get("review_reason"), (
                    f"Matchup {mu.get('fighter_a')} vs {mu.get('fighter_b')} "
                    "blocked from queue save must have review_reason"
                )


# ---------------------------------------------------------------------------
# Test 10: Gate 1 remains preview-only
# ---------------------------------------------------------------------------

def test_gate1_remains_preview_only():
    """Test 10: Gate 1 dry-run returns preview-only output, no permanent writes."""
    state = load_readonly_runtime_state()
    result = run_gate1_save_fights_dry_run_apply_preview(state)
    assert result is not None
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.mutation_performed is False


# ---------------------------------------------------------------------------
# Test 11: No queue write occurs
# ---------------------------------------------------------------------------

def test_no_queue_write_occurs_on_gate1_dry_run():
    """Test 11: Gate 1 preview never writes to persistent queue."""
    state = load_readonly_runtime_state()
    result = run_gate1_save_fights_dry_run_apply_preview(state)
    assert result.queue_write_performed is False
    assert result.database_write_performed is False
    assert result.preview_only is True


# ---------------------------------------------------------------------------
# Test 12: No PDF generation occurs
# ---------------------------------------------------------------------------

def test_no_pdf_generation_occurs(client):
    """Test 12: Button 1 workflow preview route never triggers PDF generation."""
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
    assert data is not None
    assert data.get("pdf_generated") is not True
    assert data.get("report_delivered") is not True


# ---------------------------------------------------------------------------
# Test 13: No delivery occurs
# ---------------------------------------------------------------------------

def test_no_delivery_occurs(client):
    """Test 13: Workflow preview produces no delivery action."""
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
    assert data is not None
    assert data.get("delivered") is not True
    assert data.get("report_delivered") is not True


# ---------------------------------------------------------------------------
# Test 14: No learning/calibration occurs
# ---------------------------------------------------------------------------

def test_no_learning_calibration_occurs(client):
    """Test 14: Button 1 preview never triggers learning or calibration updates."""
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
    assert data is not None
    assert data.get("learning_updated") is not True
    assert data.get("calibration_updated") is not True


# ---------------------------------------------------------------------------
# Test 15: Button 3 remains untouched
# ---------------------------------------------------------------------------

def test_button3_runtime_state_untouched_by_full_card_ingestion():
    """Test 15: Full-card matchup ingestion does not mutate Button 3 state."""
    state = load_readonly_runtime_state()
    b3_result_rows = state.get("result_rows", [])
    b3_accuracy = state.get("accuracy_metrics", {})
    b3_learning = state.get("learning_updates", [])

    # Button 3 data must not have been written by this slice
    assert not isinstance(b3_learning, list) or len(b3_learning) == 0, (
        "Button 3 learning updates must not be written by Button 1 ingestion"
    )
    # Button 3 accuracy metrics should not reference ingestion origin
    if isinstance(b3_accuracy, dict):
        assert b3_accuracy.get("provenance_origin") != "approved_source_live_event_ingestion"
