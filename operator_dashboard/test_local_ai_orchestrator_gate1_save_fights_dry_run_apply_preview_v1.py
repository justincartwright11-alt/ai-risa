"""Preview-only Gate 1 save-fights dry-run apply checks (v1)."""

import json
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


def _input_ref(key: str = "seed_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _valid_token(candidate_scope=None):
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("gate1_dry_run"))
    token = dict(plan.gate_approval_token_preview)
    if candidate_scope is not None:
        token["candidate_scope"] = candidate_scope
    return token


def _candidate_row(candidate_id: str, with_provenance: bool = True, duplicate: bool = False, conflict: bool = False):
    row = {
        "candidate_id": candidate_id,
        "fight_name": f"Fight {candidate_id}",
        "duplicate": duplicate,
        "conflict": conflict,
    }
    if with_provenance:
        row["source_url"] = f"https://example.com/{candidate_id}"
    return row


def test_valid_token_and_candidates_produces_dry_run_would_save_preview():
    token = _valid_token(candidate_scope=["c1"])
    rows = [_candidate_row("c1")]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.ok is True
    assert result.eligible_for_future_approval is True
    assert result.future_write_eligibility is True
    assert result.would_save_count == 1
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.mutation_performed is False
    assert result.queue_write_performed is False
    assert result.database_write_performed is False


def test_missing_token_fails_closed():
    result = run_gate1_save_fights_dry_run_apply_preview(None, [_candidate_row("c1")])

    assert result.ok is False
    assert result.eligible_for_future_approval is False
    assert any("missing gate_approval_token_preview" in reason for reason in result.blocking_reasons)


def test_wrong_gate_fails_closed():
    token = _valid_token()
    token["gate_name"] = "Approve Customer PDF Delivery"

    result = run_gate1_save_fights_dry_run_apply_preview(token, [_candidate_row("c1")])

    assert result.ok is False
    assert any("gate_name" in reason for reason in result.blocking_reasons)


def test_wrong_source_button_fails_closed():
    token = _valid_token()
    token["source_button"] = "button2_generate_pdfs"

    result = run_gate1_save_fights_dry_run_apply_preview(token, [_candidate_row("c1")])

    assert result.ok is False
    assert any("source_button" in reason for reason in result.blocking_reasons)


def test_candidate_scope_missing_is_safely_empty():
    token = _valid_token()
    result = run_gate1_save_fights_dry_run_apply_preview(token, [])

    assert result.ok is True
    assert result.candidate_scope_present is False
    assert result.candidate_scope_empty is True
    assert result.would_save_count == 0


def test_candidate_scope_filters_rows():
    token = _valid_token(candidate_scope=["c2"])
    rows = [_candidate_row("c1"), _candidate_row("c2")]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.scoped_candidate_count == 1
    assert result.would_save_count == 1
    assert result.would_save_candidate_ids == ["c2"]


def test_scope_with_no_matches_blocks_future_approval_eligibility():
    token = _valid_token(candidate_scope=["does_not_exist"])
    rows = [_candidate_row("c1")]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.ok is True
    assert result.eligible_for_future_approval is False
    assert result.future_write_eligibility is False
    assert any("candidate scope does not match" in reason for reason in result.blocking_reasons)


def test_duplicate_or_conflict_candidates_are_not_would_save():
    token = _valid_token()
    rows = [_candidate_row("c1", duplicate=True), _candidate_row("c2", conflict=True)]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 0
    assert result.duplicate_or_conflict_count == 2
    assert set(result.blocked_candidate_ids) == {"c1", "c2"}


def test_missing_provenance_candidates_are_not_would_save():
    token = _valid_token()
    rows = [_candidate_row("c1", with_provenance=False)]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 0
    assert result.provenance_missing_count == 1
    assert result.eligible_for_future_approval is False


def test_mixed_candidates_allow_partial_would_save_preview():
    token = _valid_token()
    rows = [
        _candidate_row("good"),
        _candidate_row("dup", duplicate=True),
        _candidate_row("no_src", with_provenance=False),
    ]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 1
    assert result.eligible_for_future_approval is True
    assert result.future_write_eligibility is True
    assert result.would_save_candidate_ids == ["good"]


def test_dry_run_cannot_authorize_itself_even_when_token_is_mutated():
    token = _valid_token()
    token["write_authorized"] = True

    result = run_gate1_save_fights_dry_run_apply_preview(token, [_candidate_row("c1")])

    assert result.ok is False
    assert result.write_authorized is False
    assert result.mutation_performed is False
    assert result.queue_write_performed is False
    assert result.database_write_performed is False


def test_dry_run_result_serializes_to_json():
    result = run_gate1_save_fights_dry_run_apply_preview(_valid_token(), [_candidate_row("c1")])
    payload = result.to_json()
    loaded = json.loads(payload)

    assert loaded["preview_only"] is True
    assert loaded["queue_write_performed"] is False
    assert loaded["database_write_performed"] is False


def test_dry_run_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during gate1 dry-run apply preview")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    result = run_gate1_save_fights_dry_run_apply_preview(_valid_token(), [_candidate_row("c1")])
    assert result.ok is True
    assert opened_for_write == []


def test_dry_run_performs_no_live_web_calls(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = run_gate1_save_fights_dry_run_apply_preview(_valid_token(), [_candidate_row("c1")])
    assert result.ok is True


def test_identity_conflict_status_blocks_would_save_preview():
    token = _valid_token()
    rows = [
        {
            **_candidate_row("conflict_row"),
            "fighter_a_identity_status": "identity_conflict",
            "identity_blocking_reasons": ["fighter_a:conflict"],
            "identity_ready_for_queue_review": False,
        }
    ]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 0
    assert "conflict_row" in result.blocked_candidate_ids
    assert "conflict_row" in result.identity_blocked_candidate_ids
    assert result.identity_blocked_count == 1
    assert result.identity_blocking_reasons_by_candidate.get("conflict_row")


def test_identity_source_missing_status_blocks_would_save_preview():
    token = _valid_token()
    rows = [
        {
            **_candidate_row("source_missing_row"),
            "fighter_b_identity_status": "identity_source_missing",
            "identity_ready_for_queue_review": False,
        }
    ]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 0
    assert "source_missing_row" in result.blocked_candidate_ids
    assert "source_missing_row" in result.identity_blocked_candidate_ids


def test_identity_ambiguous_status_blocks_would_save_preview():
    token = _valid_token()
    rows = [
        {
            **_candidate_row("ambiguous_row"),
            "fighter_a_identity_status": "identity_ambiguous",
        }
    ]

    result = run_gate1_save_fights_dry_run_apply_preview(token, rows)

    assert result.would_save_count == 0
    assert "ambiguous_row" in result.blocked_candidate_ids
    assert "ambiguous_row" in result.identity_blocked_candidate_ids
