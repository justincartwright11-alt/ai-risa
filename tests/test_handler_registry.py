import os
import tempfile
import shutil
import json
import unittest
from handlers import registry
from handlers import event_decomposition_handler, event_batch_intake_handler, fighter_gap_real_grounding_handler

class HandlerRegistryContractTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["AI_RISA_FIXED_TIMESTAMP"] = "2026-04-18T00:00:00Z"
        class DummyReporter:
            def __init__(self):
                self.events = []
            def report_execute_success(self, *args, **kwargs):
                self.events.append(("success", args, kwargs))
            def report_execute_artifact_fail(self, *args, **kwargs):
                self.events.append(("artifact_fail", args, kwargs))
            def report_execute_partial_success(self, *args, **kwargs):
                self.events.append(("partial_success", args, kwargs))
            def report_execute_blocked(self, *args, **kwargs):
                self.events.append(("blocked", args, kwargs))
        self.reporter = DummyReporter()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        del os.environ["AI_RISA_FIXED_TIMESTAMP"]

    def test_registry_maps_all_handlers(self):
        self.assertIs(registry.get_handler("event_decomposition"), event_decomposition_handler)
        self.assertIs(registry.get_handler("event_batch_intake"), event_batch_intake_handler)
        self.assertIs(registry.get_handler("fighter_gap_real_grounding"), fighter_gap_real_grounding_handler)

    def test_event_decomposition_handler(self):
        plan = {
            "task": {
                "task_type": "event_decomposition",
                "event_name": "E1",
                "event_date": "2026-04-18",
                "event_type": "",
                "promotion": "UFC ",
                "venue": " ",
                "location": "Las Vegas",
                "bouts": [
                    {"fighters": ["A ", "B"], "weight_class": "Lightweight", "scheduled_rounds": "3", "is_title_fight": "yes"},
                    {"fighters": ["C", "D"], "weight_class": "Welterweight", "scheduled_rounds": 5, "is_title_fight": False},
                    {"fighters": ["", ""], "weight_class": "", "scheduled_rounds": "", "is_title_fight": ""},
                    "not_a_dict"
                ]
            },
            "identifier": "E1",
            "queue": "event_coverage_queue.csv"
        }
        result = event_decomposition_handler.run(plan, self.reporter, self.temp_dir)
        artifact = os.path.join(self.temp_dir, "event_decomposition_E1.json")
        self.assertTrue(os.path.exists(artifact))
        with open(artifact) as f:
            data = json.load(f)
        self.assertEqual(data["event_name"], "E1")
        self.assertEqual(data["task_type"], "event_decomposition")
        self.assertEqual(data["source_queue"], "event_coverage_queue.csv")
        self.assertEqual(data["decomposition_status"], "decomposed")
        # Expanded event_metadata
        self.assertEqual(
            data["event_metadata"],
            {
                "event_name": "E1",
                "event_date": "2026-04-18",
                "event_type": None,
                "promotion": "UFC",
                "venue": None,
                "location": "Las Vegas"
            }
        )
        # Normalized bout dict shape and deterministic order
        bouts = data["discovered_bout_slots"]
        self.assertEqual(len(bouts), 2)
        self.assertEqual(bouts[0], {
            "bout_index": 0,
            "fighter_a": "A",
            "fighter_b": "B",
            "weight_class": "Lightweight",
            "scheduled_rounds": "3",
            "is_title_fight": True,
            "normalization_notes": []
        })
        self.assertEqual(bouts[1], {
            "bout_index": 1,
            "fighter_a": "C",
            "fighter_b": "D",
            "weight_class": "Welterweight",
            "scheduled_rounds": 5,
            "is_title_fight": False,
            "normalization_notes": []
        })
        # Expanded processing_summary
        summary = data["processing_summary"]
        self.assertEqual(summary["input_bout_count"], 4)
        self.assertEqual(summary["normalized_bout_count"], 2)
        self.assertEqual(summary["invalid_bout_count"], 2)
        self.assertEqual(summary["title_fight_count"], 1)
        self.assertEqual(summary["weight_classes_seen"], ["Lightweight", "Welterweight"])
        self.assertEqual(summary["normalization_actions"], [
            {"bout_index": 0, "notes": []},
            {"bout_index": 1, "notes": []},
            {"bout_index": 2, "notes": ["fighters_invalid"]},
            {"bout_index": 3, "notes": ["not_a_dict"]}
        ])
        self.assertEqual(data["version"], "ai-risa-phase3")
        self.assertEqual(data["generated_at"], "2026-04-18T00:00:00Z")
        self.assertEqual(result["result"], "success")

    def test_event_batch_intake_handler(self):
        plan = {
            "task": {
                "task_type": "event_batch_intake",
                "batch_contents": [
                    {"event_name": "E1", "event_date": "2026-04-18", "promotion": "UFC"},
                    {"event_name": "E2", "event_date": "2026-04-19", "promotion": "Bellator"},
                    {"event_name": "", "event_date": "2026-04-20", "promotion": " ", "extra": "x"},
                    "not_a_dict"
                ]
            },
            "identifier": "B1",
            "queue": "event_batch_queue.csv"
        }
        result = event_batch_intake_handler.run(plan, self.reporter, self.temp_dir)
        artifact = os.path.join(self.temp_dir, "event_batch_intake_B1.json")
        self.assertTrue(os.path.exists(artifact))
        with open(artifact) as f:
            data = json.load(f)
        self.assertEqual(data["event_batch"], "B1")
        self.assertEqual(data["task_type"], "event_batch_intake")
        self.assertEqual(data["source_queue"], "event_batch_queue.csv")
        # Normalized batch entry shape and deterministic order
        entries = data["normalized_batch_entries"]
        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0], {
            "entry_index": 0,
            "event_name": "E1",
            "event_date": "2026-04-18",
            "promotion": "UFC",
            "entry_status": "accepted",
            "normalization_notes": []
        })
        self.assertEqual(entries[1], {
            "entry_index": 1,
            "event_name": "E2",
            "event_date": "2026-04-19",
            "promotion": "Bellator",
            "entry_status": "accepted",
            "normalization_notes": []
        })
        self.assertEqual(entries[2], {
            "entry_index": 2,
            "event_name": None,
            "event_date": "2026-04-20",
            "promotion": None,
            "entry_status": "skipped",
            "normalization_notes": ["missing_event_name"]
        })
        self.assertEqual(entries[3], {
            "entry_index": 3,
            "event_name": None,
            "event_date": None,
            "promotion": None,
            "entry_status": "skipped",
            "normalization_notes": ["not_a_dict"]
        })
        # Intake classification
        self.assertEqual(data["accepted_count"], 2)
        self.assertEqual(data["skipped_count"], 2)
        self.assertEqual(len(data["accepted_entries"]), 2)
        self.assertEqual(len(data["skipped_entries"]), 2)
        # Expanded intake_summary
        summary = data["intake_summary"]
        self.assertEqual(summary["input_entry_count"], 4)
        self.assertEqual(summary["normalized_entry_count"], 4)
        self.assertEqual(summary["accepted_count"], 2)
        self.assertEqual(summary["skipped_count"], 2)
        self.assertEqual(summary["promotions_seen"], ["Bellator", "UFC"])
        self.assertEqual(summary["normalization_actions"], [
            {"entry_index": 0, "notes": []},
            {"entry_index": 1, "notes": []},
            {"entry_index": 2, "notes": ["missing_event_name"]},
            {"entry_index": 3, "notes": ["not_a_dict"]}
        ])
        self.assertEqual(data["version"], "ai-risa-phase3")
        self.assertEqual(data["generated_at"], "2026-04-18T00:00:00Z")
        self.assertEqual(result["result"], "success")

    def test_fighter_gap_real_grounding_handler(self):
        plan = {
            "task": {
                "task_type": "fighter_gap_real_grounding",
                "fighter_id": "F1",
                "field1": "value1",
                "field2": "",
                "field3": " ",
                "field4": None
            },
            "identifier": "F1",
            "queue": "fighter_gap_queue.csv"
        }
        result = fighter_gap_real_grounding_handler.run(plan, self.reporter, self.temp_dir)
        artifact = os.path.join(self.temp_dir, "fighter_gap_real_grounding_F1.json")
        self.assertTrue(os.path.exists(artifact))
        with open(artifact) as f:
            data = json.load(f)
        self.assertEqual(data["fighter_id"], "F1")
        self.assertEqual(data["task_type"], "fighter_gap_real_grounding")
        self.assertEqual(data["source_queue"], "fighter_gap_queue.csv")
        self.assertEqual(data["grounding_mode"], "real")
        # Normalized snapshots
        self.assertEqual(data["task_snapshot"], {
            "field1": "value1",
            "field2": None,
            "field3": None,
            "field4": None,
            "fighter_id": "F1",
            "task_type": "fighter_gap_real_grounding"
        })
        self.assertIn("source_snapshot", data)
        self.assertEqual(data["input_fields_seen"], ["field1", "field2", "field3", "field4", "fighter_id", "task_type"])
        self.assertEqual(data["normalization_notes"], [])
        # Missing-fields classification
        self.assertEqual(data["missing_fields_summary"], {
            "missing_required_fields": ["field2"],
            "missing_optional_fields": ["field3", "field4"],
            "missing_count": 3,
            "has_critical_gaps": True
        })
        # Enrichment summary
        self.assertEqual(data["enrichment_summary"], {
            "fields_present_count": 2,
            "fields_missing_count": 3,
            "fields_enriched_count": 0,
            "coverage_status": "partial",
            "enrichment_actions": []
        })
        self.assertEqual(data["version"], "ai-risa-phase3")
        self.assertEqual(data["generated_at"], "2026-04-18T00:00:00Z")
        self.assertEqual(result["result"], "success")

if __name__ == "__main__":
    unittest.main()
