# v64.55 Closure-Release-Final-Directory Generator
# Purpose: Deterministically project closure-release-final-manifest records into closure-release-final-directory records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, approval, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_manifest.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_directory.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_directory.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-directory-"

def load_final_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_final_directory_records(final_manifest_records):
    final_directory_records = []
    for idx, rec in enumerate(final_manifest_records):
        directory = {
            "id": deterministic_id(idx),
            "source_governed_operations_closure_release_final_manifest_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        final_directory_records.append(directory)
    return final_directory_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Closure Release Final Directory\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_closure_release_final_manifest_id: {rec['source_governed_operations_closure_release_final_manifest_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")

if __name__ == "__main__":
    final_manifest_records = load_final_manifest(INPUT_PATH)
    final_directory_records = project_final_directory_records(final_manifest_records)
    write_json(final_directory_records, OUTPUT_JSON_PATH)
    write_markdown(final_directory_records, OUTPUT_MD_PATH)
