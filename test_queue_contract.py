from pathlib import Path

from agent_queue_reader import AgentQueueReader
from agent_task_dispatcher import AgentTaskDispatcher


def test_read_all_queues_returns_normalized_queue_metadata(tmp_path: Path):
    queue_file = tmp_path / "event_coverage_queue.csv"
    queue_file.write_text(
        "event_name,event_date,sport,league,active\nONE SAMURAI 1,2026-04-29,mixed_rules,mixed_rules,false\n",
        encoding="utf-8",
    )

    reader = AgentQueueReader(repo_root=tmp_path)
    queues = reader.read_all_queues()

    event_queue = queues["event_coverage_queue.csv"]
    assert event_queue["exists"] is True
    assert event_queue["fieldnames"] == ["event_name", "event_date", "sport", "league", "active"]
    assert event_queue["rows"] == [
        {
            "event_name": "ONE SAMURAI 1",
            "event_date": "2026-04-29",
            "sport": "mixed_rules",
            "league": "mixed_rules",
            "active": "false",
        }
    ]

    intake_queue = queues["fighter_intake_unresolved_queue.csv"]
    assert intake_queue["exists"] is False
    assert intake_queue["rows"] == []


def test_dispatcher_surfaces_fighter_intake_queue_before_event_queue():
    dispatcher = AgentTaskDispatcher()
    queues = {
        "fixture_gap_queue_ranked.csv": {"rows": []},
        "fighter_gap_queue_ranked.csv": {"rows": []},
        "fighter_intake_unresolved_queue.csv": {
            "rows": [
                {
                    "fighter_name": "Jane Example",
                    "canonical_fighter_id": "jane_example",
                    "unresolved_fields": "date_of_birth|stance",
                    "active": "false",
                }
            ]
        },
        "event_coverage_queue.csv": {
            "rows": [
                {
                    "event_name": "Fallback Event",
                    "active": "false",
                }
            ]
        },
        "fixture_gap_queue.csv": {"rows": []},
        "fighter_gap_queue.csv": {"rows": []},
    }

    next_task = dispatcher.select_next_task(queues)

    assert next_task == {
        "queue": "fighter_intake_unresolved_queue.csv",
        "item": {
            "fighter_name": "Jane Example",
            "canonical_fighter_id": "jane_example",
            "unresolved_fields": "date_of_birth|stance",
            "active": "false",
        },
    }