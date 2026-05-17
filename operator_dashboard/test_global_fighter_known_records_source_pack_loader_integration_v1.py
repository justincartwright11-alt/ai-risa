"""Integration tests: source-pack builder in readonly loader (v1)."""

import pytest
import socket
from operator_dashboard.global_fighter_known_records_readonly_loader import load_known_records_readonly_preview

def _rec(fid, name, src, **kw):
    out = {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": [name + " Alias"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "confidence_grade": "A",
        "loader_source_type": src,
        "loader_source_name": src + "_source",
        "completeness_flags": {"has_identity_core": True},
        # Unsafe fields
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }
    out.update(kw)
    return out

def test_01_source_pack_path_accepts_all_six_sources():
    result = load_known_records_readonly_preview(
        manual_operator_records=[_rec("f1", "A", "manual_operator")],
        local_seed_records=[_rec("f2", "B", "local_seed")],
        approved_historical_records=[_rec("f3", "C", "approved_historical")],
        report_history_records=[_rec("f4", "D", "report_history")],
        result_ledger_records=[_rec("f5", "E", "result_ledger")],
        global_read_projection_records=[_rec("f6", "F", "global_read_projection")],
    )
    assert result.source_type == "source_pack"
    assert result.records_received_count == 6
    assert result.records_accepted_count == 6
    assert all("database_pointer" not in r for r in result.known_records)
    assert all("merge_instruction" not in r for r in result.known_records)
    assert all("write_authorized" not in r for r in result.known_records)
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.database_write_performed is False

def test_02_legacy_in_memory_and_local_seed_paths_unchanged():
    # in_memory only
    result = load_known_records_readonly_preview(
        in_memory_records=[_rec("f1", "A", "in_memory")]
    )
    assert result.source_type == "in_memory"
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    # local_seed only
    result2 = load_known_records_readonly_preview(
        local_seed_records=[_rec("f2", "B", "local_seed")]
    )
    assert result2.source_type == "local_seed"
    assert result2.records_received_count == 1
    assert result2.records_accepted_count == 1

def test_03_precedence_and_dedupe_preserved():
    # manual_operator should win over global_read_projection
    high = _rec("f1", "Anderson Silva", "manual_operator", promotion="UFC")
    low = _rec("f1", "Anderson Silva", "global_read_projection", promotion="Bellator")
    result = load_known_records_readonly_preview(
        manual_operator_records=[high],
        global_read_projection_records=[low],
    )
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["promotion"] == "UFC"
    assert rec["loader_source_type"] == "manual_operator"

def test_04_malformed_rows_fail_closed():
    result = load_known_records_readonly_preview(
        manual_operator_records=[{"full_name": "Missing ID"}, "not-a-dict", None]
    )
    assert result.records_received_count == 3
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 3

def test_05_all_write_flags_remain_false():
    result = load_known_records_readonly_preview(
        manual_operator_records=[_rec("f1", "A", "manual_operator")]
    )
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False

def test_06_never_writes_files(monkeypatch):
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
    result = load_known_records_readonly_preview(
        manual_operator_records=[_rec("f1", "A", "manual_operator")]
    )
    assert result.records_accepted_count == 1
    assert opened_for_write == []

def test_07_never_calls_live_web(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")
    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    result = load_known_records_readonly_preview(
        manual_operator_records=[_rec("f1", "A", "manual_operator")]
    )
    assert result.records_accepted_count == 1
