import json
import os
import unittest

from operator_dashboard.app import app


class TestObservabilitySignals(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.predictions_dir = os.path.join(self.repo_root, "predictions")
        os.makedirs(self.predictions_dir, exist_ok=True)

        self.event_id = "OBS_TEST_EVENT_2099_01_01"
        self.decomposition_path = os.path.join(
            self.repo_root, f"event_decomposition_{self.event_id}.json"
        )
        self.prediction_path = os.path.join(
            self.predictions_dir, "obs_alpha_vs_obs_beta_prediction.json"
        )

    def tearDown(self):
        for path in (self.decomposition_path, self.prediction_path):
            if os.path.exists(path):
                os.remove(path)

    def test_observability_endpoint_returns_decomposition_and_adapter_metrics(self):
        with open(self.decomposition_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "decomposition_status": "decomposed",
                    "discovered_bout_slots": [
                        {"fighter_a": "Obs Alpha", "fighter_b": "Obs Beta"}
                    ],
                    "processing_summary": {"input_bout_count": 1},
                },
                f,
            )

        with open(self.prediction_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "debug_metrics": {
                        "completion_mode": "sparse_fallback",
                        "fallback_fields": ["method", "round"],
                        "winner_source": "fallback_matchup_fighter_a_id",
                    }
                },
                f,
            )

        resp = self.client.get(f"/api/queue/event/{self.event_id}/observability")
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertTrue(data["ok"])

        self.assertEqual(data["decomposition"]["decomposition_status"], "decomposed")
        self.assertEqual(data["decomposition"]["discovered_bout_slots"], 1)
        self.assertEqual(data["decomposition"]["input_bout_count"], 1)
        self.assertFalse(data["decomposition"]["is_incomplete"])

        self.assertTrue(data["adapter"]["available"])
        self.assertEqual(data["adapter"]["completion_mode"], "sparse_fallback")
        self.assertEqual(data["adapter"]["fallback_fields"], ["method", "round"])
        self.assertEqual(
            data["adapter"]["winner_source"], "fallback_matchup_fighter_a_id"
        )
        self.assertTrue(data["adapter"]["fallback_active"])

    def test_observability_endpoint_degrades_when_artifact_missing(self):
        resp = self.client.get("/api/queue/event/MISSING_EVENT/observability")
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertTrue(data["ok"])
        self.assertEqual(data["decomposition"]["decomposition_status"], None)
        self.assertEqual(data["decomposition"]["discovered_bout_slots"], 0)
        self.assertEqual(data["adapter"]["completion_mode"], None)
        self.assertEqual(data["adapter"]["fallback_fields"], [])
        self.assertEqual(data["adapter"]["winner_source"], None)


if __name__ == "__main__":
    unittest.main()
