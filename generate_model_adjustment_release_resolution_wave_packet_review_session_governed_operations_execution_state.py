# v64.6 Execution-State Generator
# Purpose: Deterministically project execution-ledger records into execution-state records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, release, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os
from datetime import datetime, timezone

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_execution_ledger.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_execution_state.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_execution_state.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-execution-state-"

def load_execution_ledger(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_state_records(ledger_records):
    state_records = []
    for idx, rec in enumerate(ledger_records):
        state = {
            "id": deterministic_id(idx),
            "source_governed_operations_execution_ledger_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        state_records.append(state)
    return state_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Execution State\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_execution_ledger_id: {rec['source_governed_operations_execution_ledger_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")
            if rec.get("trace"):
                f.write(f"- trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write("\n")

def main():
    ledger_records = load_execution_ledger(INPUT_PATH)
    state_records = project_state_records(ledger_records)
    write_json(state_records, OUTPUT_JSON_PATH)
    write_markdown(state_records, OUTPUT_MD_PATH)

if __name__ == "__main__":
    main()
