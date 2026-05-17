"""Integration tests: projection-ledger normalizer wired into source-pack builder (preview v1)."""

import socket

from operator_dashboard.global_fighter_known_records_source_pack_preview import (
    build_known_records_source_pack_preview,
)


def _source_ref(name="safe_source", typ="projection"):
    return {
        "source_name": name,
        "source_type": typ,
        "source_url": "https://example.test/source",
        "source_date": "2026-05-17",
    }


def _projection_row(fid, name, src_name="projection_source", confidence="A", with_refs=True, **overrides):
    known_record = {
        "fighter_id": fid,
        "fighter_name": name,
        "aliases": [name + " Alias"],
        "country": "US",
        "organization": "UFC",
        "ruleset": "MMA",
        "weight_class": "Middleweight",
        "win_loss_record": {"wins": 10, "losses": 2, "draws": 0},
        "career_years": [2015, 2026],
        "confidence": confidence,
    }
    if with_refs:
        known_record["source_refs"] = [_source_ref()]

    row = {
        "projection": {"known_record": known_record},
        "projection_name": src_name,
        # Unsafe fields that must be excluded from output.
        "database_pointer": "secret",
        "merge_instruction": "secret",
        "ranking_write_instruction": "secret",
        "write_authorized": True,
    }
    row.update(overrides)
    return row


def test_01_projection_rows_integrate_through_source_pack_builder():
    result = build_known_records_source_pack_preview(
        approved_historical_records=[_projection_row("a1", "A")],
        result_ledger_records=[_projection_row("r1", "B")],
        report_history_records=[_projection_row("h1", "C")],
        global_read_projection_records=[_projection_row("g1", "D")],
    )
    assert result.records_received_count == 4
    assert result.records_accepted_count == 4
    assert result.blocked_records_count == 0


def test_02_each_advanced_projection_source_normalizes_safely():
    result = build_known_records_source_pack_preview(
        approved_historical_records=[_projection_row("a1", "A")],
        result_ledger_records=[_projection_row("r1", "B")],
        report_history_records=[_projection_row("h1", "C")],
        global_read_projection_records=[_projection_row("g1", "D")],
    )
    by_id = {rec["fighter_global_id"]: rec for rec in result.known_records}
    assert by_id["a1"]["loader_source_type"] == "approved_historical"
    assert by_id["r1"]["loader_source_type"] == "result_ledger"
    assert by_id["h1"]["loader_source_type"] == "report_history"
    assert by_id["g1"]["loader_source_type"] == "global_read_projection"


def test_03_precedence_dedupe_remains_stable_with_projection_rows():
    high = _projection_row("dup1", "Anderson Silva", src_name="approved", confidence="A", with_refs=True)
    low = _projection_row(
        "dup1",
        "Anderson Silva",
        src_name="global",
        confidence="B",
        with_refs=True,
        projection={
            "known_record": {
                "fighter_id": "dup1",
                "fighter_name": "Anderson Silva",
                "organization": "Bellator",
                "confidence": "B",
                "source_refs": [_source_ref("global", "global_read_projection")],
            }
        },
    )
    result = build_known_records_source_pack_preview(
        approved_historical_records=[high],
        global_read_projection_records=[low],
    )
    assert result.records_accepted_count == 1
    rec = result.known_records[0]
    assert rec["loader_source_type"] == "approved_historical"
    assert rec["promotion"] == "UFC"


def test_04_missing_provenance_or_confidence_fails_closed_for_projection_rows():
    missing_refs = _projection_row("x1", "No Refs", with_refs=False)
    missing_conf = _projection_row("x2", "No Confidence")
    del missing_conf["projection"]["known_record"]["confidence"]

    result = build_known_records_source_pack_preview(
        approved_historical_records=[missing_refs, missing_conf],
    )
    assert result.records_received_count == 2
    assert result.records_accepted_count == 0
    assert result.blocked_records_count == 2


def test_05_raw_internal_write_fields_excluded_and_write_flags_false():
    result = build_known_records_source_pack_preview(
        result_ledger_records=[_projection_row("r1", "Alex Pereira")]
    )
    rec = result.known_records[0]
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "ranking_write_instruction" not in rec
    assert "write_authorized" not in rec

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

    result = build_known_records_source_pack_preview(
        approved_historical_records=[_projection_row("a1", "A")]
    )
    assert result.records_accepted_count == 1
    assert opened_for_write == []


def test_07_never_calls_live_web(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = build_known_records_source_pack_preview(
        report_history_records=[_projection_row("h1", "H")]
    )
    assert result.records_accepted_count == 1
