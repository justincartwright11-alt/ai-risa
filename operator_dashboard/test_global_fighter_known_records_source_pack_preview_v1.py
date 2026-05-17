"""Tests for known records source-pack preview builder (v1)."""

import json
import socket

import pytest

from operator_dashboard.global_fighter_known_records_source_pack_preview import (
    build_known_records_source_pack_preview,
)


def _record(fid: str, name: str, src: str, **overrides):
    out = {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": [name + " Alias"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "height": "6'2\"",
        "reach": "77\"",
        "stance": "Orthodox",
        "record": {"wins": 20, "losses": 2, "draws": 0},
        "active_years": [1997, 2020],
        "confidence_grade": "A",
        "loader_source_type": src,
        "loader_source_name": src + "_source",
        "completeness_flags": {"has_identity_core": True},
        # Unsafe fields that must be dropped
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }
    out.update(overrides)
    return out


def test_01_returns_empty_safe_context_when_no_inputs():
    result = build_known_records_source_pack_preview()
    assert result.preview_only is True
    assert result.known_records == []
    assert result.records_received_count == 0
    assert result.records_accepted_count == 0
    assert result.source_type == "source_pack"


def test_02_accepts_manual_operator_source_records():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert result.known_records[0]["loader_source_type"] == "manual_operator"


def test_03_accepts_all_six_source_classes():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "A", "manual_operator")],
        local_seed_records=[_record("f2", "B", "local_seed")],
        approved_historical_records=[_record("f3", "C", "approved_historical")],
        report_history_records=[_record("f4", "D", "report_history")],
        result_ledger_records=[_record("f5", "E", "result_ledger")],
        global_read_projection_records=[_record("f6", "F", "global_read_projection")],
    )
    assert result.records_received_count == 6
    assert result.records_accepted_count == 6


def test_04_dedupes_by_fighter_global_id_and_applies_precedence():
    high = _record("f1", "Anderson Silva", "manual_operator", promotion="UFC")
    low = _record("f1", "Anderson Silva", "global_read_projection", promotion="Bellator")
    result = build_known_records_source_pack_preview(
        manual_operator_records=[high],
        global_read_projection_records=[low],
    )
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["promotion"] == "UFC"
    assert rec["loader_source_type"] == "manual_operator"


def test_05_dedupes_by_normalized_full_name_after_id_dedupe():
    r1 = _record("f1", "Anderson Silva", "report_history")
    r2 = _record("f2", "  anderson   silva ", "manual_operator")
    result = build_known_records_source_pack_preview(
        report_history_records=[r1],
        manual_operator_records=[r2],
    )
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["loader_source_type"] == "manual_operator"


def test_06_fills_missing_fields_from_lower_precedence_duplicate():
    high = _record("f1", "Anderson Silva", "manual_operator", stance=None, reach=None)
    low = _record("f1", "Anderson Silva", "result_ledger", stance="Southpaw", reach="79\"")
    result = build_known_records_source_pack_preview(
        manual_operator_records=[high],
        result_ledger_records=[low],
    )
    rec = result.known_records[0]
    assert rec["loader_source_type"] == "manual_operator"
    assert rec["stance"] == "Southpaw"
    assert rec["reach"] == "79\""


def test_07_aliases_are_merged_uniquely_across_duplicates():
    high = _record("f1", "Anderson Silva", "manual_operator", known_aliases=["The Spider"])
    low = _record("f1", "Anderson Silva", "local_seed", known_aliases=["the spider", "Spider King"])
    result = build_known_records_source_pack_preview(
        manual_operator_records=[high],
        local_seed_records=[low],
    )
    aliases = result.known_records[0]["known_aliases"]
    assert aliases == ["The Spider", "Spider King"]


def test_08_excludes_internal_and_write_fields():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    rec = result.known_records[0]
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_09_rejects_missing_required_fields_fail_closed():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[
            {"full_name": "Missing ID"},
            {"fighter_global_id": "f2"},
        ]
    )
    assert result.records_received_count == 2
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 2


def test_10_rejects_non_mapping_row_fail_closed():
    result = build_known_records_source_pack_preview(
        manual_operator_records=["not-an-object", None]
    )
    assert result.records_received_count == 2
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 2


def test_11_non_list_source_input_is_safely_ignored_with_error():
    result = build_known_records_source_pack_preview(
        manual_operator_records="bad",
        local_seed_records=[_record("f1", "Anderson Silva", "local_seed")],
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    assert any("manual_operator_records must be a list" in e for e in result.errors)


def test_12_confidence_grade_defaults_to_c_when_invalid():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator", confidence_grade="ZZ")]
    )
    assert result.records_accepted_count == 1
    assert result.known_records[0]["confidence_grade"] == "C"


def test_13_aliases_coerced_to_empty_list_when_invalid_shape():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator", known_aliases="bad")]
    )
    assert result.records_accepted_count == 1
    assert result.known_records[0]["known_aliases"] == []


def test_14_provenance_defaults_to_source_class_when_missing():
    rec = _record("f1", "Anderson Silva", "manual_operator")
    del rec["loader_source_type"]
    del rec["loader_source_name"]
    result = build_known_records_source_pack_preview(
        result_ledger_records=[rec]
    )
    out = result.known_records[0]
    assert out["loader_source_type"] == "result_ledger"
    assert out["loader_source_name"] == "result_ledger"


def test_15_result_envelope_has_all_zero_write_flags():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False


def test_16_to_dict_and_json_serialization_work():
    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    d = result.to_dict()
    assert isinstance(d, dict)
    payload = json.dumps(d)
    assert isinstance(payload, str)


def test_17_never_writes_files(monkeypatch):
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

    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    assert result.records_accepted_count == 1
    assert opened_for_write == []


def test_18_never_calls_live_web(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = build_known_records_source_pack_preview(
        manual_operator_records=[_record("f1", "Anderson Silva", "manual_operator")]
    )
    assert result.records_accepted_count == 1


def test_19_mixed_valid_invalid_keeps_only_valid_rows():
    result = build_known_records_source_pack_preview(
        approved_historical_records=[
            _record("f1", "Anderson Silva", "approved_historical"),
            {"fighter_global_id": "missing_name"},
            _record("f2", "Israel Adesanya", "approved_historical"),
        ]
    )
    assert result.records_received_count == 3
    assert result.records_accepted_count == 2
    assert result.malformed_records_count == 1


def test_20_loader_source_lineage_present_on_cross_source_merge():
    high = _record("f1", "Anderson Silva", "manual_operator")
    low = _record("f1", "Anderson Silva", "global_read_projection")
    result = build_known_records_source_pack_preview(
        manual_operator_records=[high],
        global_read_projection_records=[low],
    )
    rec = result.known_records[0]
    assert rec["loader_source_type"] == "manual_operator"
    assert rec.get("loader_source_lineage") == ["manual_operator", "global_read_projection"]


def test_21_normalizes_report_history_projection_shape_preview_only():
    result = build_known_records_source_pack_preview(
        report_history_records=[
            {
                "projection_name": "report_history_projected_v1",
                "projection": {
                    "fighter_id": "rh-100",
                    "fighter_name": "Alex Pereira",
                    "aliases": ["Poatan", "poatan"],
                    "country": "BR",
                    "organization": "UFC",
                    "ruleset": "MMA",
                    "weight_class": "Light Heavyweight",
                    "dob": "1987-07-07",
                    "win_loss_record": {"wins": 12, "losses": 2, "draws": 0},
                    "career_years": [2015, 2026],
                    "confidence": "B",
                    "source_refs": [
                        {
                            "source_name": "report_history_projection",
                            "source_type": "report_history",
                            "source_url": "https://example.test/report",
                            "source_date": "2026-05-17",
                        }
                    ],
                },
            }
        ]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["fighter_global_id"] == "rh-100"
    assert rec["full_name"] == "Alex Pereira"
    assert rec["known_aliases"] == ["Poatan"]
    assert rec["nationality"] == "BR"
    assert rec["promotion"] == "UFC"
    assert rec["sport_ruleset"] == "MMA"
    assert rec["division"] == "Light Heavyweight"
    assert rec["date_of_birth"] == "1987-07-07"
    assert rec["record"] == {"wins": 12, "losses": 2, "draws": 0}
    assert rec["active_years"] == (2015, 2026)
    assert rec["confidence_grade"] == "B"
    assert rec["loader_source_type"] == "report_history"
    assert rec["loader_source_name"] == "report_history_projected_v1"


def test_22_normalizes_global_projection_nested_known_record_shape():
    result = build_known_records_source_pack_preview(
        global_read_projection_records=[
            {
                "projection": {
                    "known_record": {
                        "global_fighter_id": "gdb-42",
                        "display_name": "Tom Aspinall",
                        "aliases": ["Honey Badger"],
                        "country": "UK",
                        "confidence": "A",
                        "source_refs": [
                            {
                                "source_name": "global_db_projection",
                                "source_type": "global_read_projection",
                                "source_url": "https://example.test/global",
                                "source_date": "2026-05-17",
                            }
                        ],
                        "projection_origin_id": "gdb:row:42",
                        "projection_snapshot_ts": "2026-05-17T00:00:00Z",
                    }
                },
                "source_name": "global_db_projection_safe",
                "database_pointer": "must_drop",
                "write_authorized": True,
            }
        ]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["fighter_global_id"] == "gdb-42"
    assert rec["full_name"] == "Tom Aspinall"
    assert rec["loader_source_type"] == "global_read_projection"
    assert rec["loader_source_name"] == "global_db_projection_safe"
    assert rec["loader_record_origin_id"] == "gdb:row:42"
    assert rec["loader_snapshot_ts"] == "2026-05-17T00:00:00Z"
    assert "database_pointer" not in rec
    assert "write_authorized" not in rec


def test_23_accepts_records_container_shape_for_advanced_projection_source():
    result = build_known_records_source_pack_preview(
        approved_historical_records={
            "records": [
                {
                    "known_record": {
                        "fighter_id": "ah-1",
                        "fighter_name": "Sean Strickland",
                        "confidence": "A",
                            "source_refs": [
                                {
                                    "source_name": "approved_projection",
                                    "source_type": "approved_historical",
                                    "source_url": "https://example.test/approved",
                                    "source_date": "2026-05-17",
                                }
                            ],
                    }
                }
            ]
        }
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["fighter_global_id"] == "ah-1"
    assert rec["full_name"] == "Sean Strickland"
    assert rec["confidence_grade"] == "A"
    assert rec["loader_source_type"] == "approved_historical"
