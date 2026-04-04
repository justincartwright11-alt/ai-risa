#!/usr/bin/env python3
"""
Generator: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff
Slice: v56.3-controlled-release-resolution-wave-packet-review-session-governed-operations-distribution-handoff

Strict 1:1 deterministic distribution handoff envelope over frozen distribution-assessment records.

Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_assessment.json
Output:
  - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff.json
  - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff.md

Contracts:
- Parse input JSON once, fail fast on schema breakage
- For each input record, resolve upstream ID in strict order
- Output record count == input record count
- Deterministic, sequential, zero-padded distribution-handoff IDs
- Preserve input order
- Carry forward or freeze generated_at_utc
- Markdown is a pure projection of JSON
"""
import json
import sys
from pathlib import Path

INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_assessment.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff.md")

HANDOFF_ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-distribution-handoff-"
HANDOFF_ID_PAD = 4
SOURCE_ARTIFACT = str(INPUT_PATH)

FROZEN_GENERATED_AT_UTC = "2024-01-01T00:00:00Z"

ID_FIELDS = [
    "governed_operations_distribution_assessment_id",
    "distribution_assessment_id",
    "assessment_id",
    "id"
]

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def load_input():
    if not INPUT_PATH.exists():
        fail(f"Input JSON not found: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "records" not in data or not isinstance(data["records"], list):
        fail("Input JSON missing 'records' array or invalid schema.")
    return data

def resolve_upstream_id(record):
    for field in ID_FIELDS:
        if field in record and record[field]:
            return record[field]
    fail("No resolvable upstream distribution-assessment ID in record.")

def main():
    data = load_input()
    input_records = data["records"]
    record_count = len(input_records)
    if record_count == 0:
        fail("Input records array is empty.")

    # Carry forward or freeze generated_at_utc
    generated_at_utc = data.get("generated_at_utc", FROZEN_GENERATED_AT_UTC)

    # Build output records
    seen_ids = set()
    output_records = []
    for idx, rec in enumerate(input_records):
        resolved_id = resolve_upstream_id(rec)
        if resolved_id in seen_ids:
            fail(f"Duplicate resolved upstream distribution-assessment ID: {resolved_id}")
        seen_ids.add(resolved_id)
        handoff_id = f"{HANDOFF_ID_PREFIX}{str(idx+1).zfill(HANDOFF_ID_PAD)}"
        output_records.append({
            "governed_operations_distribution_handoff_id": handoff_id,
            "source_governed_operations_distribution_assessment_id": resolved_id,
            "source_record_index": idx + 1,
            "source_artifact": SOURCE_ARTIFACT,
            "distribution_assessment_record": rec
        })
    if len(output_records) != record_count:
        fail("Output record count does not match input record count.")

    # Top-level output JSON
    output_json = {
        "artifact": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_distribution_handoff",
        "source_artifact": SOURCE_ARTIFACT,
        "generated_at_utc": generated_at_utc,
        "record_count": record_count,
        "records": output_records
    }
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Model Adjustment Distribution Handoff\n\n")
        f.write(f"Source artifact: `{SOURCE_ARTIFACT}`\n\n")
        f.write(f"Record count: {record_count}\n\n")
        f.write("| Distribution Handoff ID | Source Assessment ID | Source Index |\n")
        f.write("|------------------------|---------------------|--------------|\n")
        for r in output_records:
            f.write(f"| {r['governed_operations_distribution_handoff_id']} | {r['source_governed_operations_distribution_assessment_id']} | {r['source_record_index']} |\n")
        f.write("\n")
        for r in output_records:
            f.write(f"## {r['governed_operations_distribution_handoff_id']}\n\n")
            f.write(f"Source assessment ID: {r['source_governed_operations_distribution_assessment_id']}\n\n")
            f.write(f"Source record index: {r['source_record_index']}\n\n")
            f.write(f"Source artifact: `{SOURCE_ARTIFACT}`\n\n")
            f.write("Distribution assessment record:\n\n")
            f.write("```")
            f.write(json.dumps(r['distribution_assessment_record'], indent=2, ensure_ascii=False))
            f.write("\n```")
            f.write("\n\n")

if __name__ == "__main__":
    main()
