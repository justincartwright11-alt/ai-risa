"""Runtime confirmation tests for multisport approved-source event-card fixtures (v1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.approved_combat_sport_source_registry import (
    classify_source_url,
    get_source_governance,
)
from operator_dashboard.button1_multisport_approved_source_event_card_fixtures_v1 import (
    build_button1_runtime_payload_from_fixtures_v1,
)
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJob, LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


def _button1_discovery_job(payload):
    return LocalAIJob(
        job_type="discovery_job",
        source_button="button1_find_fights",
        input_ref=LocalAIJobInputRef(
            ref_type="entity",
            ref_key="runtime_fixture_set",
            snapshot_hash="snap_v1",
            metadata={"payload": payload},
        ),
    )


def _valid_gate1_token_preview():
    plan = build_three_button_workflow_plan(
        "button1_find_fights", LocalAIJobInputRef(ref_type="entity", ref_key="runtime_fixture_set", snapshot_hash="snap_v1")
    )
    return dict(plan.gate_approval_token_preview)


def test_runtime_fixture_payload_exposes_all_four_sports_as_visible_rows():
    payload = build_button1_runtime_payload_from_fixtures_v1()

    rows = payload["candidate_rows"]
    sports = {row["sport"] for row in rows}

    assert len(rows) == 4
    assert sports == {"boxing", "mma", "kickboxing", "muay_thai"}
    assert set(payload["sports_visible"]) == sports


def test_runtime_rows_remain_classified_and_provenance_backed():
    payload = build_button1_runtime_payload_from_fixtures_v1()

    for row in payload["candidate_rows"]:
        source_url = row["source_url"]
        classification = classify_source_url(source_url)
        governance = get_source_governance(source_url)

        assert classification is not None
        assert classification["sport"] == row["sport"]
        assert isinstance(row.get("provenance"), dict)
        assert row["provenance"].get("source_url") == source_url
        assert governance["approved_for_event_card_discovery"] is True


def test_button1_preview_runner_sees_all_fixture_rows_as_discovered_and_extracted():
    payload = build_button1_runtime_payload_from_fixtures_v1()
    out = run_preview_job(_button1_discovery_job(payload))

    assert out.status == "preview_ready"
    summary = out.output_preview.summary
    assert summary["discovered_count"] == 4
    assert summary["extracted_count"] == 4
    assert summary["ready_for_report_count"] == 4
    assert summary["approval_required"] is True


def test_gate1_dry_run_confirms_governed_behavior_for_runtime_fixture_set():
    payload = build_button1_runtime_payload_from_fixtures_v1()
    token = _valid_gate1_token_preview()

    result = run_gate1_save_fights_dry_run_apply_preview(token, payload["candidate_rows"])

    assert result.ok is True
    assert result.preview_only is True
    assert result.mutation_performed is False
    assert result.queue_write_performed is False
    assert result.database_write_performed is False
    assert result.would_save_count == 4
    assert result.provenance_missing_count == 0


def test_muay_thai_fixture_stays_governed_and_not_auto_queue_saved_in_runtime_confirmation():
    payload = build_button1_runtime_payload_from_fixtures_v1()
    rows = payload["candidate_rows"]
    muay_thai_row = next(row for row in rows if row["sport"] == "muay_thai")

    assert muay_thai_row["ready_state"] == "needs_review"
    assert muay_thai_row["queue_save_eligible"] is False
    assert muay_thai_row["requires_secondary_confirmation"] is True
    assert muay_thai_row["unsafe_queue_save_blocked"] is True
