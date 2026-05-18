"""Tests for Button 1 multisport approved-source event-card fixtures (v1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.button1_multisport_approved_source_event_card_fixtures_v1 import (
    get_button1_multisport_event_card_fixtures_v1,
    prepare_event_card_fixture_for_button1_v1,
)
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


def _valid_gate1_token_preview():
    plan = build_three_button_workflow_plan(
        "button1_find_fights", LocalAIJobInputRef(ref_type="entity", ref_key="fixture_seed", snapshot_hash="snap_v1")
    )
    return dict(plan.gate_approval_token_preview)


def test_fixture_pack_has_one_governed_url_backed_fixture_per_target_sport():
    fixtures = get_button1_multisport_event_card_fixtures_v1()
    sports = {row["sport"] for row in fixtures}

    assert sports == {"boxing", "mma", "kickboxing", "muay_thai"}
    assert len(fixtures) == 4
    assert all(str(row.get("source_url", "")).startswith("https://") for row in fixtures)


def test_each_fixture_prepares_into_source_backed_button1_candidate():
    fixtures = get_button1_multisport_event_card_fixtures_v1()

    for fixture in fixtures:
        prepared = prepare_event_card_fixture_for_button1_v1(fixture)
        assert prepared["source_backed"] is True
        assert prepared["preview_only"] is True
        assert prepared["approval_required"] is True
        assert prepared["provenance"]["source_url"] == fixture["source_url"]
        assert prepared["sport"] == fixture["sport"]
        assert prepared["ready_state"] in {"ready_to_save", "needs_review"}


def test_tier_expectations_hold_for_all_four_sport_fixtures():
    fixtures = get_button1_multisport_event_card_fixtures_v1()

    for fixture in fixtures:
        prepared = prepare_event_card_fixture_for_button1_v1(fixture)
        assert prepared["tier"] == fixture["expected_tier"]


def test_muay_thai_fixture_requires_review_and_blocks_unsafe_queue_save():
    fixture = next(row for row in get_button1_multisport_event_card_fixtures_v1() if row["sport"] == "muay_thai")
    prepared = prepare_event_card_fixture_for_button1_v1(fixture)

    assert prepared["requires_secondary_confirmation"] is True
    assert prepared["queue_save_eligible"] is False
    assert prepared["unsafe_queue_save_blocked"] is True
    assert prepared["ready_state"] == "needs_review"


def test_gate1_dry_run_can_preview_prepared_rows_without_any_queue_write_side_effects():
    fixtures = get_button1_multisport_event_card_fixtures_v1()
    prepared_rows = [prepare_event_card_fixture_for_button1_v1(row) for row in fixtures]
    token = _valid_gate1_token_preview()

    result = run_gate1_save_fights_dry_run_apply_preview(token, prepared_rows)

    assert result.ok is True
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.mutation_performed is False
    assert result.queue_write_performed is False
    assert result.database_write_performed is False


def test_non_muay_tier_a_rows_remain_queue_save_eligible_but_still_approval_gated():
    fixtures = [row for row in get_button1_multisport_event_card_fixtures_v1() if row["sport"] != "muay_thai"]

    for fixture in fixtures:
        prepared = prepare_event_card_fixture_for_button1_v1(fixture)
        assert prepared["tier"] == "A"
        assert prepared["queue_save_eligible"] is True
        assert prepared["approval_required"] is True
        assert prepared["preview_only"] is True
