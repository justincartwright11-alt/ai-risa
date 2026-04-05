"""
Runtime history ledger for upcoming schedule cadence/runtime control (v67.9).
Emits one audit entry per cadence invocation after runtime+alerting completes.
"""
import json
from pathlib import Path
from datetime import datetime

HISTORY_JSON = Path("ops/events/upcoming_schedule_runtime_history.json")
HISTORY_MD = Path("ops/events/upcoming_schedule_runtime_history.md")

# Deterministic run_id: ISO timestamp + invocation source

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def append_history(entry):
    ledger = load_json(HISTORY_JSON, {"history": []})
    # Deduplicate by run_id
    ledger["history"] = [e for e in ledger["history"] if e["run_id"] != entry["run_id"]]
    ledger["history"].append(entry)
    # Sort by invoked_at ascending
    ledger["history"] = sorted(ledger["history"], key=lambda e: e["invoked_at"])
    save_json(HISTORY_JSON, ledger)
    # Emit Markdown
    with open(HISTORY_MD, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Runtime History\n\n")
        for e in ledger["history"]:
            f.write(f"- Run ID: {e['run_id']}\n")
            f.write(f"  Invoked at: {e['invoked_at']}\n")
            f.write(f"  Source: {e['invocation_source']}\n")
            f.write(f"  Due: {e['due_decision']}\n")
            f.write(f"  Cycle Invoked: {e['cycle_invoked']}\n")
            f.write(f"  Cycle Status: {e['cycle_status']}\n")
            f.write(f"  Alerting Status: {e['alerting_status']}\n")
            f.write(f"  Heartbeat Health: {e['heartbeat_health']}\n")
            f.write(f"  Lock Status: {e['lock_status']}\n")
            f.write(f"  Notification Summary: {e['notification_summary']}\n")
            f.write(f"  Terminal Status: {e['terminal_status']}\n\n")
