import json
from pathlib import Path

import pytest

import ops.structural_signal_backfill_writer as writer


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _test_repo(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "repo"
    (repo_root / "ops" / "audit").mkdir(parents=True, exist_ok=True)
    (repo_root / "predictions").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(writer, "_repo_root", lambda: repo_root)
    return repo_root


def _make_source_file(tmp_path: Path, fight_id: str, *, include_structurals: bool = False) -> Path:
    payload = {
        "fight_id": fight_id,
        "predicted_winner": "Example",
        "confidence": 0.62,
        "method_tendency": "decision",
    }
    if include_structurals:
        payload["signal_gap"] = 0.5
    source = tmp_path / "predictions" / f"{fight_id}.json"
    _write_json(source, payload)
    return source


def _make_patch_file(tmp_path: Path, entries: list[dict]) -> Path:
    patch_file = tmp_path / "patch.json"
    patch_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    return patch_file


def test_dry_run_changes_no_files(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "dry_run_fight_prediction"
    source = _make_source_file(repo_root, fight_id)
    before = source.read_text(encoding="utf-8")

    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/dry_run_fight_prediction.json",
                "signal_gap": 0.12,
                "stoppage_propensity": 0.34,
                "round_finish_tendency": 0.56,
                "evidence_note": "existing metrics",
            }
        ],
    )

    summary = writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)

    assert summary["mode"] == "dry-run"
    assert summary["entry_count"] == 1
    assert source.read_text(encoding="utf-8") == before


def test_apply_writes_only_allowed_fields(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "apply_fields_fight_prediction"
    source = _make_source_file(repo_root, fight_id)
    original = _read_json(source)

    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/apply_fields_fight_prediction.json",
                "signal_gap": 0.21,
                "stoppage_propensity": 0.43,
                "round_finish_tendency": 0.65,
                "evidence_note": "existing metrics",
            }
        ],
    )

    writer.run_writer(patch_file=patch_file, dry_run=False, apply=True)
    updated = _read_json(source)

    assert updated["signal_gap"] == 0.21
    assert updated["stoppage_propensity"] == 0.43
    assert updated["round_finish_tendency"] == 0.65
    for key in original:
        if key not in {"signal_gap", "stoppage_propensity", "round_finish_tendency"}:
            assert updated[key] == original[key]


def test_unknown_extra_field_rejected(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "unknown_field_fight_prediction"
    _make_source_file(repo_root, fight_id)
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/unknown_field_fight_prediction.json",
                "signal_gap": 0.1,
                "stoppage_propensity": 0.2,
                "round_finish_tendency": 0.3,
                "evidence_note": "existing metrics",
                "bonus": 123,
            }
        ],
    )

    with pytest.raises(writer.WriterValidationError, match="Unknown fields"):
        writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)


def test_missing_source_file_rejected(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": "missing_source_fight_prediction",
                "source_file": "predictions/does_not_exist.json",
                "signal_gap": 0.1,
                "stoppage_propensity": 0.2,
                "round_finish_tendency": 0.3,
                "evidence_note": "existing metrics",
            }
        ],
    )

    with pytest.raises(writer.WriterValidationError, match="Missing source file"):
        writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)


def test_fight_id_mismatch_rejected(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    _make_source_file(repo_root, "source_truth_fight_prediction")
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": "different_fight_prediction",
                "source_file": "predictions/source_truth_fight_prediction.json",
                "signal_gap": 0.1,
                "stoppage_propensity": 0.2,
                "round_finish_tendency": 0.3,
                "evidence_note": "existing metrics",
            }
        ],
    )

    with pytest.raises(writer.WriterValidationError, match="fight_id mismatch"):
        writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)


def test_non_numeric_value_rejected(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "non_numeric_fight_prediction"
    _make_source_file(repo_root, fight_id)
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/non_numeric_fight_prediction.json",
                "signal_gap": "not-a-number",
                "stoppage_propensity": 0.2,
                "round_finish_tendency": 0.3,
                "evidence_note": "existing metrics",
            }
        ],
    )

    with pytest.raises(writer.WriterValidationError, match="signal_gap must be numeric"):
        writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)


def test_existing_field_overwrite_rejected_without_allow(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "existing_value_fight_prediction"
    _make_source_file(repo_root, fight_id, include_structurals=True)
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/existing_value_fight_prediction.json",
                "signal_gap": 0.1,
                "stoppage_propensity": 0.2,
                "round_finish_tendency": 0.3,
                "evidence_note": "existing metrics",
            }
        ],
    )

    with pytest.raises(writer.WriterValidationError, match="--allow-overwrite"):
        writer.run_writer(patch_file=patch_file, dry_run=True, apply=False, allow_overwrite=False)

    summary = writer.run_writer(patch_file=patch_file, dry_run=True, apply=False, allow_overwrite=True)
    assert summary["entry_count"] == 1


def test_audit_line_written_only_in_apply_mode(tmp_path, monkeypatch):
    repo_root = _test_repo(tmp_path, monkeypatch)
    fight_id = "audit_mode_fight_prediction"
    _make_source_file(repo_root, fight_id)
    patch_file = _make_patch_file(
        repo_root,
        [
            {
                "fight_id": fight_id,
                "source_file": "predictions/audit_mode_fight_prediction.json",
                "signal_gap": 0.11,
                "stoppage_propensity": 0.22,
                "round_finish_tendency": 0.33,
                "evidence_note": "existing metrics",
            }
        ],
    )

    audit_file = repo_root / "ops" / "audit" / "structural_signal_backfill_audit.jsonl"
    if audit_file.exists():
        before_count = len(audit_file.read_text(encoding="utf-8").splitlines())
    else:
        before_count = 0

    writer.run_writer(patch_file=patch_file, dry_run=True, apply=False)
    mid_count = len(audit_file.read_text(encoding="utf-8").splitlines()) if audit_file.exists() else 0
    assert mid_count == before_count

    writer.run_writer(patch_file=patch_file, dry_run=False, apply=True)
    after_count = len(audit_file.read_text(encoding="utf-8").splitlines())
    assert after_count == before_count + 1
