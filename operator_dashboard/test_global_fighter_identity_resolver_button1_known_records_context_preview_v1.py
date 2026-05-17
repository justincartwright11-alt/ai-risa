"""Tests for Button 1 known-records context preview builder (v1)."""

import json
import socket

import pytest

from operator_dashboard.global_fighter_identity_known_records_context import (
    build_known_records_context_preview,
)
from operator_dashboard.global_fighter_identity_resolver_preview import (
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
    resolve_fighter_identity_preview,
)


def _valid_known_record(fid: str = "fighter_001", name: str = "Anderson Silva"):
    return {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": ["The Spider", "the spider", "Silva"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "height": "6'2\"",
        "reach": "77\"",
        "stance": "Southpaw",
        "record": {"wins": 34, "losses": 11, "draws": 0, "ignored": "x"},
        "active_years": [1997, 2020],
        "confidence_grade": "A",
        # Internal/write fields that must be excluded.
        "_internal_rank": 99,
        "merge_instruction": "force",
        "write_authorized": True,
        "database_pointer": "secret",
    }


def test_accepts_in_memory_known_fighter_records_only():
    result = build_known_records_context_preview([_valid_known_record()])
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert len(result.known_records) == 1

    bad = build_known_records_context_preview("not-a-list")
    assert bad.records_received_count == 0
    assert bad.records_accepted_count == 0
    assert bad.known_records == []
    assert any("list" in e for e in bad.errors)


def test_sanitizes_known_record_fields_and_keeps_safe_comparison_fields_only():
    result = build_known_records_context_preview([_valid_known_record()])
    rec = result.known_records[0]

    expected_keys = {
        "fighter_global_id",
        "full_name",
        "known_aliases",
        "nationality",
        "promotion",
        "sport_ruleset",
        "division",
        "date_of_birth",
        "height",
        "reach",
        "stance",
        "record",
        "active_years",
        "confidence_grade",
    }
    assert set(rec.keys()) == expected_keys
    assert rec["known_aliases"] == ["The Spider", "Silva"]
    assert rec["record"] == {"wins": 34, "losses": 11, "draws": 0}
    assert rec["active_years"] == (1997, 2020)


def test_excludes_raw_internal_and_write_fields():
    result = build_known_records_context_preview([_valid_known_record()])
    rec = result.known_records[0]
    assert "_internal_rank" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec
    assert "database_pointer" not in rec


def test_returns_known_records_compatible_with_identity_resolver_preview_api_shape():
    result = build_known_records_context_preview([_valid_known_record()])

    known = [KnownFighterRecord(**r) for r in result.known_records]
    candidate = IncomingFighterCandidate(
        name="Anderson Silva",
        nationality="BR",
        promotion="UFC",
        sport_ruleset="MMA",
        division="Middleweight",
        date_of_birth="1975-07-14",
        source_refs=[SourceRef(source_name="preview", source_type="preview")],
    )

    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.preview_only is True
    assert resolved.profile_create_performed is False
    assert resolved.profile_update_performed is False
    assert resolved.merge_performed is False
    assert resolved.database_write_performed is False


def test_fails_closed_on_malformed_records():
    malformed = [
        {"full_name": "Missing ID"},
        {"fighter_global_id": "fighter_002"},
        "not-an-object",
    ]
    result = build_known_records_context_preview(malformed)

    assert result.records_received_count == 3
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 3
    assert result.known_records == []


def test_empty_safe_context_when_no_records_exist():
    result_none = build_known_records_context_preview(None)
    result_empty = build_known_records_context_preview([])

    assert result_none.known_records == []
    assert result_none.records_received_count == 0
    assert result_none.records_accepted_count == 0

    assert result_empty.known_records == []
    assert result_empty.records_received_count == 0
    assert result_empty.records_accepted_count == 0


def test_preview_builder_never_writes_files(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during known-record context preview")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    result = build_known_records_context_preview([_valid_known_record()])
    assert result.records_accepted_count == 1
    assert opened_for_write == []


def test_preview_builder_never_calls_live_web(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = build_known_records_context_preview([_valid_known_record()])
    assert result.records_accepted_count == 1


def test_all_write_flags_remain_false():
    result = build_known_records_context_preview([_valid_known_record()])

    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False

    payload = result.to_dict()
    _ = json.dumps(payload)
