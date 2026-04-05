# v64.39 Closure-Release-Map Generator
# Purpose: Deterministically project closure-release-routing records into closure-release-map records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, approval, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_routing.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_map.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_map.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-map-"


def load_release_routing(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_release_map_records(routing_records):
    map_records = []
    for idx, rec in enumerate(routing_records):
        map_rec = {
            "id": deterministic_id(idx),
            "source_governed_operations_closure_release_routing_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        map_records.append(map_rec)
    return map_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Closure Release Map\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_closure_release_routing_id: {rec['source_governed_operations_closure_release_routing_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")
            if rec.get("trace"):
                f.write(f"- trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write("\n")

def main():
    routing_records = load_release_routing(INPUT_PATH)
    map_records = project_release_map_records(routing_records)
    write_json(map_records, OUTPUT_JSON_PATH)
    write_markdown(map_records, OUTPUT_MD_PATH)

if __name__ == "__main__":
    main()
