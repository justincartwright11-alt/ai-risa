"""Tests for readonly known fighter records loader preview (v1)."""

import json
import socket

import pytest

from operator_dashboard.global_fighter_known_records_readonly_loader import (
    load_known_records_readonly_preview,
)


def _test_record(fid: str = "fighter_001", name: str = "Anderson Silva"):
    return {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": ["The Spider"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "confidence_grade": "A",
        "loader_source_type": "test",
        "loader_source_name": "test_seed",
        "completeness_flags": {"has_identity_core": True},
        # Unsafe fields that must be excluded
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }


def test_01_accept_in_memory_override_records():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert result.source_type == "in_memory"
    assert len(result.known_records) == 1


def test_02_accept_safe_local_seed_records_when_explicitly_supplied():
    result = load_known_records_readonly_preview(
        in_memory_records=None,
        local_seed_records=[_test_record()],
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert result.source_type == "local_seed"


def test_03_in_memory_takes_priority_over_local_seed():
    result = load_known_records_readonly_preview(
        in_memory_records=[_test_record("fighter_001", "Memory Fighter")],
        local_seed_records=[_test_record("fighter_002", "Seed Fighter")],
    )
    assert result.source_type == "in_memory"
    assert result.known_records[0]["full_name"] == "Memory Fighter"


def test_04_return_empty_safe_context_when_no_records_exist():
    result_none = load_known_records_readonly_preview()
    result_empty = load_known_records_readonly_preview(in_memory_records=[])

    assert result_none.known_records == []
    assert result_none.records_received_count == 0
    assert result_none.source_type == "empty"

    assert result_empty.known_records == []
    assert result_empty.records_received_count == 0
    assert result_empty.source_type == "in_memory"  # Empty list is still in_memory source


def test_05_sanitize_records_into_resolver_compatible_format():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
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
        "loader_source_type",
        "loader_source_name",
        "completeness_flags",
    }
    assert set(rec.keys()) == expected_keys


def test_06_exclude_raw_internal_write_fields():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    rec = result.known_records[0]

    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_07_preserve_source_provenance_fields():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    rec = result.known_records[0]

    assert rec.get("loader_source_type") == "test"
    assert rec.get("loader_source_name") == "test_seed"


def test_08_preserve_confidence_data_completeness_hints():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    rec = result.known_records[0]

    assert rec["confidence_grade"] == "A"
    assert rec["completeness_flags"] == {"has_identity_core": True}


def test_09_fail_closed_on_malformed_record_shape():
    malformed = [
        {"full_name": "Missing ID"},
        {"fighter_global_id": "fighter_002"},
        "not-an-object",
        None,
    ]
    result = load_known_records_readonly_preview(in_memory_records=malformed)

    assert result.records_received_count == 4
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 4
    assert result.known_records == []


def test_10_fail_closed_on_non_list_input():
    result = load_known_records_readonly_preview(in_memory_records="not-a-list")
    assert result.known_records == []
    assert result.records_accepted_count == 0
    assert any("list" in e for e in result.errors)


def test_11_mixed_valid_invalid_records_keep_only_valid():
    mixed = [
        _test_record("fighter_001", "Valid Fighter"),
        {"full_name": "Missing ID"},
        _test_record("fighter_003", "Another Valid"),
    ]
    result = load_known_records_readonly_preview(in_memory_records=mixed)

    assert result.records_received_count == 3
    assert result.records_accepted_count == 2
    assert result.malformed_records_count == 1
    assert {r["full_name"] for r in result.known_records} == {"Valid Fighter", "Another Valid"}


def test_12_never_writes_files(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.records_accepted_count == 1
    assert opened_for_write == []


def test_13_never_calls_live_web(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.records_accepted_count == 1


def test_14_never_creates_updates_merges_profiles():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False


def test_15_never_performs_database_ranking_writes():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False


def test_16_never_performs_queue_result_learning_calibration_mutations():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False


def test_17_all_write_flags_remain_false():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False


def test_18_result_serializes_to_dict_and_json():
    result = load_known_records_readonly_preview(in_memory_records=[_test_record()])
    d = result.to_dict()
    assert isinstance(d, dict)
    payload = json.dumps(d)
    assert isinstance(payload, str)


def test_19_coerce_invalid_aliases_to_empty_list():
    rec = {
        "fighter_global_id": "f1",
        "full_name": "Fighter",
        "known_aliases": "not-a-list",
    }
    result = load_known_records_readonly_preview(in_memory_records=[rec])
    assert result.records_accepted_count == 1
    assert result.known_records[0]["known_aliases"] == []


def test_20_default_missing_confidence_grade_to_c():
    rec = {
        "fighter_global_id": "f1",
        "full_name": "Fighter",
    }
    result = load_known_records_readonly_preview(in_memory_records=[rec])
    assert result.records_accepted_count == 1
    assert result.known_records[0]["confidence_grade"] == "C"
