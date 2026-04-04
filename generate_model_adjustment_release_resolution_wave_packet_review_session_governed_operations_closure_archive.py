# v64.23 Closure-Archive Generator
# Purpose: Deterministically project closure-summary records into closure-archive records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, release, approval, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_summary.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_archive.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_archive.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-archive-"


def load_closure_summary(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_archive_records(summary_records):
    archive_records = []
    for idx, rec in enumerate(summary_records):
        archive = {
            "id": deterministic_id(idx),
            "source_governed_operations_closure_summary_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        archive_records.append(archive)
    return archive_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Closure Archive\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_closure_summary_id: {rec['source_governed_operations_closure_summary_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")
            if rec.get("trace"):
                f.write(f"- trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write("\n")

def main():
    summary_records = load_closure_summary(INPUT_PATH)
    archive_records = project_archive_records(summary_records)
    write_json(archive_records, OUTPUT_JSON_PATH)
    write_markdown(archive_records, OUTPUT_MD_PATH)

if __name__ == "__main__":
    main()
