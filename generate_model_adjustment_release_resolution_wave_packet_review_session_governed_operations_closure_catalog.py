# v64.12 Closure-Catalog Generator
# Purpose: Deterministically project closure-resolution records into closure-catalog records, one-to-one, with exact-once coverage, deterministic IDs, and upstream traceability.
# No policy, release, approval, prioritization, or execution-outcome logic. No edits to prior slices.

import json
import os
from datetime import datetime, timezone

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_resolution.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_catalog.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_catalog.md"

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-catalog-"

def load_closure_resolution(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def project_catalog_records(resolution_records):
    catalog_records = []
    for idx, rec in enumerate(resolution_records):
        catalog = {
            "id": deterministic_id(idx),
            "source_governed_operations_closure_resolution_id": rec["id"],
            "projected_at_utc": "2026-04-04T00:00:00Z",
            # Carry forward all fields required for traceability, but do not infer new state
            "trace": rec.get("trace", {}),
        }
        catalog_records.append(catalog)
    return catalog_records

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(records, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Closure Catalog\n\n")
        for rec in records:
            f.write(f"## {rec['id']}\n")
            f.write(f"- source_governed_operations_closure_resolution_id: {rec['source_governed_operations_closure_resolution_id']}\n")
            f.write(f"- projected_at_utc: {rec['projected_at_utc']}\n")
            if rec.get("trace"):
                f.write(f"- trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write("\n")

def main():
    resolution_records = load_closure_resolution(INPUT_PATH)
    catalog_records = project_catalog_records(resolution_records)
    write_json(catalog_records, OUTPUT_JSON_PATH)
    write_markdown(catalog_records, OUTPUT_MD_PATH)

if __name__ == "__main__":
    main()
