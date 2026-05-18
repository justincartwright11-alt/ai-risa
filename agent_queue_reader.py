import csv
import os

QUEUE_FILES = [
    "event_coverage_queue.csv",
    "fixture_gap_queue.csv",
    "fixture_gap_queue_ranked.csv",
    "fighter_intake_unresolved_queue.csv",
    "fighter_gap_queue.csv",
    "fighter_gap_queue_ranked.csv"
]

class AgentQueueReader:
    def __init__(self, repo_root=None):
        self.repo_root = repo_root or os.getcwd()

    def read_queue(self, filename):
        path = os.path.join(self.repo_root, filename)
        if not os.path.exists(path):
            return {
                "filename": filename,
                "path": path,
                "exists": False,
                "rows": [],
            }
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return {
                "filename": filename,
                "path": path,
                "exists": True,
                "fieldnames": reader.fieldnames or [],
                "rows": list(reader),
            }

    def read_all_queues(self):
        queues = {}
        for qf in QUEUE_FILES:
            queues[qf] = self.read_queue(qf)
        return queues
