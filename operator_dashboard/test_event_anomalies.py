import unittest
from anomaly_utils import AnomalyAggregator


class TestAnomalyAggregator(unittest.TestCase):
    def setUp(self):
        self.aggregator = AnomalyAggregator()

    def test_anomaly_index_contract(self):
        queue_rows = [
            {"event_id": "song_vs_figueiredo", "status": "complete", "blockers": "", "completed_at": "2026-01-01T12:00:00Z"},
            {"event_id": "blocked_event", "status": "blocked", "blockers": "", "completed_at": "2026-01-02T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "song_vs_figueiredo", "status": "complete", "artifact_exists": False, "artifact_safe": True},
            {"event_id": "blocked_event", "status": "blocked", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        types = set(a['type'] for a in anomalies)
        self.assertIn('complete_missing_artifact', types)
        self.assertIn('blocked_no_blockers', types)

    def test_event_anomaly_contract(self):
        queue_rows = [
            {"event_id": "song_vs_figueiredo", "status": "complete", "blockers": "", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "song_vs_figueiredo", "status": "complete", "artifact_exists": False, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows, event_id="song_vs_figueiredo")
        self.assertTrue(any(a['event_id'] == 'song_vs_figueiredo' for a in anomalies))

    def test_non_empty_anomaly_hit(self):
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": False, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertGreater(len(anomalies), 0)

    def test_miss_case(self):
        # Should pass if no anomalies are present for a clean event
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        # Accept empty, None, or any falsey value as valid no-anomaly states
        self.assertTrue(anomalies is None or anomalies == [] or not anomalies, f"Expected no anomalies, got: {anomalies}")

    def test_severity_ordering(self):
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
            {"event_id": "e2", "status": "blocked", "blockers": "", "completed_at": "2026-01-02T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": False, "artifact_safe": True},
            {"event_id": "e2", "status": "blocked", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertGreater(anomalies[0]['severity'], anomalies[-1]['severity'])

    def test_tied_severity_deterministic_ordering(self):
        queue_rows = [
            {"event_id": "a", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
            {"event_id": "b", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "a", "status": "complete", "artifact_exists": False, "artifact_safe": True},
            {"event_id": "b", "status": "complete", "artifact_exists": False, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        # Should be sorted by event_id if tied
        self.assertLess(anomalies[0]['event_id'], anomalies[1]['event_id'])

    def test_blocked_blank_blockers(self):
        queue_rows = [
            {"event_id": "blocked_event", "status": "blocked", "blockers": "", "completed_at": "2026-01-02T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "blocked_event", "status": "blocked", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertTrue(any(a['type'] == 'blocked_no_blockers' for a in anomalies))

    def test_complete_missing_artifact(self):
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": False, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [{'event_id': 'e1', 'status': 'captured', 'timestamp': '2026-01-01T12:00:00Z'}]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertTrue(any(a['type'] == 'complete_missing_artifact' for a in anomalies))

    def test_complete_no_recent_activity(self):
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = []
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertTrue(any(a['type'] == 'complete_no_recent_activity' for a in anomalies))

    def test_malformed_ledger_recovery(self):
        queue_rows = [
            {"event_id": "e1", "status": "complete", "completed_at": "2026-01-01T12:00:00Z"},
        ]
        evidence_rows = [
            {"event_id": "e1", "status": "complete", "artifact_exists": True, "artifact_safe": True},
        ]
        comparison_rows = []
        timeline_rows = []
        ledger_rows = [
            {"event_id": "e1", "error": "Malformed ledger entry"},
        ]
        anomalies = self.aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        self.assertTrue(any(a['type'] == 'malformed_ledger' for a in anomalies))

if __name__ == "__main__":
    unittest.main()

