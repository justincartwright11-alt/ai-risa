# v64.32 Closure-Release-Resolution Generator
# Purpose: Deterministically project closure-release-state records into closure-release-resolution records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, approval, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_state.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_resolution.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_resolution.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-resolution-"


def load_release_state(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_release_resolution_records(state_records):
    resolution_records = []
    for idx, rec in enumerate(state_records):
        resolution = {
            "id": deterministic_id(idx),
            "source_governed_operations_closure_release_state_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        resolution_records.append(resolution)
    return resolution_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Closure Release Resolution\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_closure_release_state_id: {rec['source_governed_operations_closure_release_state_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")
            if rec.get("trace"):
                f.write(f"- trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write("\n")

def main():
    state_records = load_release_state(INPUT_PATH)
    resolution_records = project_release_resolution_records(state_records)
    write_json(resolution_records, OUTPUT_JSON_PATH)
    write_markdown(resolution_records, OUTPUT_MD_PATH)

if __name__ == "__main__":
    main()
