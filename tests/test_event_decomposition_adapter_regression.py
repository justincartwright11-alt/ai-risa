import json
from pathlib import Path

from domain.metadata import extract_bouts_from_payload, normalize_bout_candidate
from handlers import event_decomposition_handler


class DummyReporter:
    def __init__(self):
        self.events = []

    def report_execute_success(self, *args, **kwargs):
        self.events.append(("success", args, kwargs))

    def report_execute_artifact_failure(self, *args, **kwargs):
        self.events.append(("artifact_fail", args, kwargs))

    def report_execute_partial_success(self, *args, **kwargs):
        self.events.append(("partial_success", args, kwargs))


def _write_event_json(base_dir: Path, filename: str, payload: dict):
    events_dir = base_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    event_path = events_dir / filename
    event_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return event_path


def test_extract_bouts_resolves_from_event_name_and_date(tmp_path, monkeypatch):
    _write_event_json(
        tmp_path,
        "one_samurai_1_2026_04_29.json",
        {
            "event_name": "ONE SAMURAI 1",
            "bouts": [
                {"fighter_a": "Nadaka Yoshinari", "fighter_b": "Banluelok Sitwatcharachai"},
                {"fighter_a": "Petphupa Aekpujean", "fighter_b": "Mongkolkaew Sor Sommai"},
            ],
        },
    )
    monkeypatch.chdir(tmp_path)

    task = {
        "event_name": "ONE SAMURAI 1",
        "event_date": "2026-04-29",
    }
    bouts = extract_bouts_from_payload(task)

    assert len(bouts) == 2
    assert bouts[0]["fighter_a"] == "Nadaka Yoshinari"
    assert bouts[0]["fighter_b"] == "Banluelok Sitwatcharachai"


def test_normalize_bout_candidate_accepts_alternate_fighter_keys():
    bout = normalize_bout_candidate(
        {
            "fighter_1": "Fighter Red",
            "fighter_2": "Fighter Blue",
            "weight_class": "flyweight",
            "scheduled_rounds": "3",
        },
        idx=0,
    )

    assert bout["fighter_a"] == "Fighter Red"
    assert bout["fighter_b"] == "Fighter Blue"
    assert "fighters_invalid" not in bout["normalization_notes"]


def test_normalize_bout_candidate_rejects_placeholder_names():
    bout = normalize_bout_candidate(
        {
            "fighter_a": "TBD",
            "fighter_b": "Real Opponent",
        },
        idx=1,
    )

    assert bout["fighter_a"] is None
    assert "fighters_invalid" in bout["normalization_notes"]


def test_event_decomposition_integrity_with_source_json(tmp_path, monkeypatch):
    _write_event_json(
        tmp_path,
        "one_samurai_1_2026_04_29.json",
        {
            "bouts": [
                {"fighter_a": "A", "fighter_b": "B", "weight_class": "Lightweight"},
                {"fighter_1": "C", "fighter_2": "D", "division": "Welterweight"},
                {"fighter_a": "", "fighter_b": "E"},
            ]
        },
    )
    monkeypatch.chdir(tmp_path)

    reporter = DummyReporter()
    plan = {
        "task": {
            "task_type": "event_decomposition",
            "event_name": "ONE SAMURAI 1",
            "event_date": "2026-04-29",
            "promotion": "ONE",
        },
        "identifier": "ONE SAMURAI 1",
        "queue": "event_coverage_queue.csv",
    }

    result = event_decomposition_handler.run(plan, reporter, str(tmp_path))

    assert result["result"] == "success"
    artifact = tmp_path / "event_decomposition_ONE SAMURAI 1.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))

    assert data["decomposition_status"] == "decomposed"
    assert len(data["discovered_bout_slots"]) == 2
    assert data["processing_summary"]["input_bout_count"] == 3
    assert data["processing_summary"]["normalized_bout_count"] == 2
    assert data["processing_summary"]["invalid_bout_count"] == 1


def test_event_decomposition_no_crash_with_missing_bouts(tmp_path):
    reporter = DummyReporter()
    plan = {
        "task": {
            "task_type": "event_decomposition",
            "event_name": "No Source Event",
            "event_date": "2026-05-01",
        },
        "identifier": "No Source Event",
        "queue": "event_coverage_queue.csv",
    }

    result = event_decomposition_handler.run(plan, reporter, str(tmp_path))

    assert result["result"] == "success"
    artifact = tmp_path / "event_decomposition_No Source Event.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))

    assert data["decomposition_status"] == "incomplete"
    assert data["discovered_bout_slots"] == []
    assert data["processing_summary"]["input_bout_count"] == 0
    assert data["processing_summary"]["normalized_bout_count"] == 0
    assert data["processing_summary"]["status"] == "no_valid_bouts"
