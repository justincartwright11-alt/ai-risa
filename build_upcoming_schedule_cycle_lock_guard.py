"""
build_upcoming_schedule_cycle_lock_guard.py

Single-instance execution guard for the full upcoming schedule cycle.

Guards build_upcoming_schedule_cycle_orchestrator.py with a lock file.
Emits:
- ops/events/upcoming_schedule_cycle_lock_guard.json
- ops/events/upcoming_schedule_cycle_lock_guard.md

See v66.8 locked spec for full requirements.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import subprocess
import atexit

LOCK_PATH = Path("ops/events/upcoming_schedule_cycle.lock")
GUARD_JSON_PATH = Path("ops/events/upcoming_schedule_cycle_lock_guard.json")
GUARD_MD_PATH = Path("ops/events/upcoming_schedule_cycle_lock_guard.md")
ORCHESTRATOR = "build_upcoming_schedule_cycle_orchestrator.py"
PYTHON = r"C:\\Users\\jusin\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe"


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def emit_guard_artifacts(result):
    with open(GUARD_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(GUARD_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Cycle Lock Guard\n\n")
        f.write(f"Run at: {result['timestamp']} UTC\n\n")
        f.write(f"Lock path: {LOCK_PATH}\n\n")
        f.write(f"Guard status: {result['status']}\n\n")
        if result['status'] == "blocked":
            f.write(f"Blocked reason: {result['reason']}\n\n")
        if result['status'] == "ran":
            f.write(f"Orchestrator status: {result['orchestrator_status']}\n")
            f.write(f"Orchestrator summary: {result.get('orchestrator_summary_path', 'N/A')}\n")
            f.write(f"Orchestrator report: {result.get('orchestrator_report_path', 'N/A')}\n")
            if result.get('orchestrator_summary_hash'):
                f.write(f"Summary hash: {result['orchestrator_summary_hash']}\n")
            if result.get('orchestrator_report_hash'):
                f.write(f"Report hash: {result['orchestrator_report_hash']}\n")
        f.write("\n")

def main():
    timestamp = datetime.utcnow().isoformat() + "Z"
    result = {
        "timestamp": timestamp,
        "status": None,
        "reason": None,
        "lock_path": str(LOCK_PATH),
    }
    # Check for active lock
    if LOCK_PATH.exists():
        result["status"] = "blocked"
        result["reason"] = "active lock present"
        emit_guard_artifacts(result)
        sys.exit(1)
    # Create lock file
    try:
        LOCK_PATH.write_text(f"locked at {timestamp}\n", encoding="utf-8")
    except Exception as e:
        result["status"] = "error"
        result["reason"] = f"failed to create lock: {e}"
        emit_guard_artifacts(result)
        sys.exit(1)
    def cleanup():
        try:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()
        except Exception:
            pass
    atexit.register(cleanup)
    try:
        proc = subprocess.run([PYTHON, ORCHESTRATOR], capture_output=True, text=True, check=False)
        result["status"] = "ran"
        result["orchestrator_status"] = "success" if proc.returncode == 0 else f"fail (code {proc.returncode})"
        # Record orchestrator summary/report if present
        summary_path = Path("ops/events/upcoming_schedule_cycle_summary.json")
        report_path = Path("ops/events/upcoming_schedule_cycle_report.md")
        if summary_path.exists():
            result["orchestrator_summary_path"] = str(summary_path)
            result["orchestrator_summary_hash"] = hash_file(summary_path)
        if report_path.exists():
            result["orchestrator_report_path"] = str(report_path)
            result["orchestrator_report_hash"] = hash_file(report_path)
    except Exception as e:
        result["status"] = "error"
        result["reason"] = f"orchestrator run failed: {e}"
    finally:
        cleanup()
    emit_guard_artifacts(result)
    if result["status"] != "ran":
        sys.exit(1)

if __name__ == "__main__":
    main()
