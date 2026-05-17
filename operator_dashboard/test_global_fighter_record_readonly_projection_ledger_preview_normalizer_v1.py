"""Focused tests for read-only projection ledger preview normalizer (v1)."""

import json
import socket

from operator_dashboard.global_fighter_record_readonly_projection_ledger_preview import (
    build_projection_ledger_known_records_preview,
)


def _source_ref(name="safe_source", typ="projection"):
    return {
        "source_name": name,
        "source_type": typ,
        "source_url": "https://example.test/source",
        "source_date": "2026-05-17",
    }


def _projection(fid, name, src_name="projection_source", **overrides):
    row = {
        "projection": {
            "known_record": {
                "fighter_id": fid,
                "fighter_name": name,
                "aliases": [name + " Alias"],
                "country": "US",
                "organization": "UFC",
                "ruleset": "MMA",
                "weight_class": "Middleweight",
                "win_loss_record": {"wins": 10, "losses": 2, "draws": 0},
                "career_years": [2015, 2026],
                "confidence": "A",
                "source_refs": [_source_ref()],
            }
        },
        "projection_name": src_name,
        # Unsafe fields that must never appear in known_records.
        "database_pointer": "secret",
        "merge_instruction": "secret",
        "ranking_write_instruction": "secret",
        "private_operator_notes": "secret",
        "raw_ledger_internals": {"x": 1},
        "unverified_source_payloads": {"x": 2},
        "write_authorized": True,
        "profile_create_performed": True,
    }
    row.update(overrides)
    return row


def test_01_normalizes_all_six_projection_sources():
    result = build_projection_ledger_known_records_preview(
        manual_operator_records=[_projection("m1", "A", "manual")],
        approved_historical_records=[_projection("a1", "B", "approved")],
        result_ledger_records=[_projection("r1", "C", "result")],
        report_history_records=[_projection("h1", "D", "history")],
        local_seed_records=[_projection("l1", "E", "local")],
        global_read_projection_records=[_projection("g1", "F", "global")],
    )
    assert result.records_received_count == 6
    assert result.records_accepted_count == 6
    assert result.malformed_records_count == 0
    assert result.blocked_records_count == 0


def test_02_output_is_resolver_compatible_safe_shape():
    result = build_projection_ledger_known_records_preview(
        approved_historical_records=[_projection("a1", "Sean Strickland")]
    )
    rec = result.known_records[0]

    required_keys = {
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
        "completeness_flags",
        "source_refs",
        "projection_source_type",
        "projection_source_name",
        "projection_generated_at_preview",
    }
    assert required_keys.issubset(set(rec.keys()))


def test_03_raw_internal_and_write_fields_excluded():
    result = build_projection_ledger_known_records_preview(
        result_ledger_records=[_projection("r1", "Alex Pereira")]
    )
    rec = result.known_records[0]
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "ranking_write_instruction" not in rec
    assert "private_operator_notes" not in rec
    assert "raw_ledger_internals" not in rec
    assert "unverified_source_payloads" not in rec
    assert "write_authorized" not in rec
    assert "profile_create_performed" not in rec


def test_04_missing_name_or_id_is_malformed_and_skipped():
    bad = _projection("", "", "bad")
    result = build_projection_ledger_known_records_preview(
        approved_historical_records=[bad]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 0
    assert result.malformed_records_count == 1


def test_05_missing_source_refs_is_blocked():
    row = _projection("a1", "Sean Strickland")
    row["projection"]["known_record"]["source_refs"] = []
    result = build_projection_ledger_known_records_preview(
        approved_historical_records=[row]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 0
    assert result.blocked_records_count == 1


def test_06_missing_projection_confidence_is_blocked():
    row = _projection("a1", "Sean Strickland")
    del row["projection"]["known_record"]["confidence"]
    result = build_projection_ledger_known_records_preview(
        approved_historical_records=[row]
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 0
    assert result.blocked_records_count == 1


def test_07_precedence_and_dedupe_follow_design_order():
    high = _projection("dup-1", "Anderson Silva", "manual", projection={
        "known_record": {
            "fighter_id": "dup-1",
            "fighter_name": "Anderson Silva",
            "organization": "UFC",
            "confidence": "A",
            "source_refs": [_source_ref("manual", "manual_operator")],
        }
    })
    low = _projection("dup-1", "Anderson Silva", "global", projection={
        "known_record": {
            "fighter_id": "dup-1",
            "fighter_name": "Anderson Silva",
            "organization": "Other",
            "confidence": "B",
            "source_refs": [_source_ref("global", "global_read_projection")],
        }
    })
    result = build_projection_ledger_known_records_preview(
        manual_operator_records=[high],
        global_read_projection_records=[low],
    )
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["promotion"] == "UFC"
    assert rec["projection_source_type"] == "manual_operator"


def test_08_accepts_records_container_shape():
    result = build_projection_ledger_known_records_preview(
        approved_historical_records={"records": [_projection("a1", "Sean Strickland")]}
    )
    assert result.records_received_count == 1
    assert result.records_accepted_count == 1


def test_09_zero_write_flags_always_false():
    result = build_projection_ledger_known_records_preview(
        report_history_records=[_projection("h1", "Tom Aspinall")]
    )
    assert result.preview_only is True
    assert result.profile_create_performed is False
    assert result.profile_update_performed is False
    assert result.merge_performed is False
    assert result.database_write_performed is False
    assert result.ranking_write_performed is False
    assert result.learning_apply_performed is False
    assert result.calibration_write_performed is False


def test_10_result_is_json_serializable():
    result = build_projection_ledger_known_records_preview(
        local_seed_records=[_projection("l1", "Merab Dvalishvili")]
    )
    payload = json.dumps(result.to_dict())
    assert isinstance(payload, str)


def test_11_no_filesystem_writes(monkeypatch):
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

    result = build_projection_ledger_known_records_preview(
        manual_operator_records=[_projection("m1", "A")]
    )
    assert result.records_accepted_count == 1
    assert opened_for_write == []


def test_12_no_live_web_calls(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = build_projection_ledger_known_records_preview(
        manual_operator_records=[_projection("m1", "A")]
    )
    assert result.records_accepted_count == 1
