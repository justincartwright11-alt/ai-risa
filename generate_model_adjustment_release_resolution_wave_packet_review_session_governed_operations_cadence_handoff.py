#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.py

Purpose: Deterministically generate the v43.2 governed operations cadence handoff artifact as a strict 1:1 downstream projection of the v43.1 cadence assessment records.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.md

Rules:
- Parse input JSON once only
- Fail fast on missing/invalid schema or duplicate IDs
- Output record count must match input exactly (1:1 projection)
- Deterministic ordering (preserve input order)
- No semantic mutation or normalization
- No upstream edits
- No RC/merge/push
"""
import json
from pathlib import Path
import sys

def resolve_assessment_id(rec):
    for key in [
        "governed_operations_cadence_assessment_id",
        "cadence_assessment_id",
        "assessment_id",
        "id"
    ]:
        if key in rec:
            return rec[key]
    raise ValueError("No valid assessment ID found in input record: {}".format(rec))

def main():
    # Input/output paths
    assessment_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.json")
    handoff_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.json")
    handoff_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.md")

    # Load input JSON once
    if not assessment_path.exists():
        sys.exit(f"Input JSON not found: {assessment_path}")
    with assessment_path.open("r", encoding="utf-8") as f:
        assessment_data = json.load(f)
    if "records" not in assessment_data or not isinstance(assessment_data["records"], list):
        sys.exit("Input JSON missing 'records' array or not a list.")
    input_records = assessment_data["records"]
    if not input_records:
        sys.exit("Input JSON contains no records.")

    # Project handoff records
    seen_ids = set()
    handoff_records = []
    for idx, rec in enumerate(input_records):
        src_id = resolve_assessment_id(rec)
        if src_id in seen_ids:
            sys.exit(f"Duplicate assessment ID detected: {src_id}")
        seen_ids.add(src_id)
        handoff_id = f"resolution-wave-packet-review-session-governed-operations-cadence-handoff-{str(idx+1).zfill(4)}"
        handoff_record = {
            "cadence_handoff_id": handoff_id,
            "source_cadence_assessment_id": src_id,
            "source_record_index": idx + 1,
            "source_artifact": str(assessment_path).replace("\\", "/"),
            "assessment_record": rec
        }
        handoff_records.append(handoff_record)

    # Output contract
    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff",
        "source_artifact": str(assessment_path).replace("\\", "/"),
        "record_count": len(handoff_records),
        "records": handoff_records
    }

    # Deterministic JSON output
    with handoff_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with handoff_md_path.open("w", encoding="utf-8") as f:
        f.write("# v43.2 Governed Operations Cadence Handoff\n\n")
        f.write(f"Source artifact: {contract['source_artifact']}\n\n")
        f.write(f"Record count: {contract['record_count']}\n\n")
        f.write("| cadence_handoff_id | source_cadence_assessment_id | source_record_index |\n")
        f.write("|---|---|---|\n")
        for r in handoff_records:
            f.write(f"| {r['cadence_handoff_id']} | {r['source_cadence_assessment_id']} | {r['source_record_index']} |\n")
        f.write("\n")
        for r in handoff_records:
            f.write(f"## {r['cadence_handoff_id']}\n")
            f.write(f"Source assessment ID: {r['source_cadence_assessment_id']}\n\n")
            f.write(f"Source record index: {r['source_record_index']}\n\n")
            f.write("Assessment record (verbatim):\n\n")
            f.write("```")
            json.dump(r['assessment_record'], f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n```")
            f.write("\n\n")

if __name__ == "__main__":
    main()
