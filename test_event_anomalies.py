import csv
from anomaly_utils import AnomalyAggregator

# Minimal test for anomaly aggregation

def test_anomaly_aggregation():
    # Simulate queue and evidence rows
    queue_rows = [
        {"event_name": "song_vs_figueiredo", "status": "completed"},
        {"event_name": "prochazka_vs_ulberg", "status": "pending"}
    ]
    evidence_rows = [
        {"event_name": "song_vs_figueiredo", "status": "pending"},
        {"event_name": "prochazka_vs_ulberg", "status": "pending"}
    ]
    comparison_rows = []
    timeline_rows = []
    aggregator = AnomalyAggregator()
    anomalies = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows)
    print("Anomalies:", anomalies)

if __name__ == "__main__":
    test_anomaly_aggregation()
