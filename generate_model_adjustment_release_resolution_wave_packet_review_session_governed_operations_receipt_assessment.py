#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.py

Purpose: Deterministically generate the v44.2 governed operations receipt assessment artifact as a strict 1:1 downstream projection of the v44.1 receipt intake records.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.md

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

def resolve_intake_id(rec):
    for key in [
        "governed_operations_receipt_intake_id",
        "receipt_intake_id",
        "intake_id",
        "id"
    ]:
        if key in rec:
            return rec[key]
    raise ValueError(f"No valid receipt-intake ID found in input record: {rec}")

def main():
    # Input/output paths
    intake_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.json")
    assessment_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.json")
    assessment_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.md")

    # Load input JSON once
    if not intake_path.exists():
        sys.exit(f"Input JSON not found: {intake_path}")
    with intake_path.open("r", encoding="utf-8") as f:
        intake_data = json.load(f)
    if "records" not in intake_data or not isinstance(intake_data["records"], list):
        sys.exit("Input JSON missing 'records' array or not a list.")
    input_records = intake_data["records"]
    if not input_records:
        sys.exit("Input JSON contains no records.")

    # Project assessment records
    seen_ids = set()
    assessment_records = []
    for idx, rec in enumerate(input_records):
        src_id = resolve_intake_id(rec)
        if src_id in seen_ids:
            sys.exit(f"Duplicate receipt-intake ID detected: {src_id}")
        seen_ids.add(src_id)
        assessment_id = f"resolution-wave-packet-review-session-governed-operations-receipt-assessment-{str(idx+1).zfill(4)}"
        assessment_record = {
            "governed_operations_receipt_assessment_id": assessment_id,
            "source_governed_operations_receipt_intake_id": src_id,
            "source_record_index": idx + 1,
            "source_artifact": str(intake_path).replace("\\", "/"),
            "receipt_intake_record": rec
        }
        assessment_records.append(assessment_record)

    # Output contract
    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment",
        "source_artifact": str(intake_path).replace("\\", "/"),
        "record_count": len(assessment_records),
        "records": assessment_records
    }

    # Deterministic JSON output
    with assessment_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with assessment_md_path.open("w", encoding="utf-8") as f:
        f.write("# v44.2 Governed Operations Receipt Assessment\n\n")
        f.write(f"Source artifact: {contract['source_artifact']}\n\n")
        f.write(f"Record count: {contract['record_count']}\n\n")
        f.write("| governed_operations_receipt_assessment_id | source_governed_operations_receipt_intake_id | source_record_index |\n")
        f.write("|---|---|---|\n")
        for r in assessment_records:
            f.write(f"| {r['governed_operations_receipt_assessment_id']} | {r['source_governed_operations_receipt_intake_id']} | {r['source_record_index']} |\n")
        f.write("\n")
        for r in assessment_records:
            f.write(f"## {r['governed_operations_receipt_assessment_id']}\n")
            f.write(f"Source receipt-intake ID: {r['source_governed_operations_receipt_intake_id']}\n\n")
            f.write(f"Source record index: {r['source_record_index']}\n\n")
            f.write("Receipt intake record (verbatim):\n\n")
            f.write("```")
            json.dump(r['receipt_intake_record'], f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n```")
            f.write("\n\n")

if __name__ == "__main__":
    main()
