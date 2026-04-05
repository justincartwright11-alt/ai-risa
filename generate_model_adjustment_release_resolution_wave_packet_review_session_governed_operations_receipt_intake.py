#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.py

Purpose: Deterministically generate the v44.1 governed operations receipt intake artifact as a strict 1:1 downstream projection of the v43.2 cadence handoff records.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.md

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

def resolve_handoff_id(rec):
    for key in [
        "governed_operations_cadence_handoff_id",
        "cadence_handoff_id",
        "handoff_id",
        "id"
    ]:
        if key in rec:
            return rec[key]
    raise ValueError(f"No valid handoff ID found in input record: {rec}")

def main():
    # Input/output paths
    handoff_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.json")
    receipt_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.json")
    receipt_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.md")

    # Load input JSON once
    if not handoff_path.exists():
        sys.exit(f"Input JSON not found: {handoff_path}")
    with handoff_path.open("r", encoding="utf-8") as f:
        handoff_data = json.load(f)
    if "records" not in handoff_data or not isinstance(handoff_data["records"], list):
        sys.exit("Input JSON missing 'records' array or not a list.")
    input_records = handoff_data["records"]
    if not input_records:
        sys.exit("Input JSON contains no records.")

    # Project receipt intake records
    seen_ids = set()
    receipt_records = []
    for idx, rec in enumerate(input_records):
        src_id = resolve_handoff_id(rec)
        if src_id in seen_ids:
            sys.exit(f"Duplicate handoff ID detected: {src_id}")
        seen_ids.add(src_id)
        receipt_id = f"resolution-wave-packet-review-session-governed-operations-receipt-intake-{str(idx+1).zfill(4)}"
        receipt_record = {
            "governed_operations_receipt_intake_id": receipt_id,
            "source_governed_operations_cadence_handoff_id": src_id,
            "source_record_index": idx + 1,
            "source_artifact": str(handoff_path).replace("\\", "/"),
            "cadence_handoff_record": rec
        }
        receipt_records.append(receipt_record)

    # Output contract
    contract = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake",
        "source_artifact": str(handoff_path).replace("\\", "/"),
        "record_count": len(receipt_records),
        "records": receipt_records
    }

    # Deterministic JSON output
    with receipt_json_path.open("w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, sort_keys=True, ensure_ascii=False)

    # Deterministic Markdown output
    with receipt_md_path.open("w", encoding="utf-8") as f:
        f.write("# v44.1 Governed Operations Receipt Intake\n\n")
        f.write(f"Source artifact: {contract['source_artifact']}\n\n")
        f.write(f"Record count: {contract['record_count']}\n\n")
        f.write("| governed_operations_receipt_intake_id | source_governed_operations_cadence_handoff_id | source_record_index |\n")
        f.write("|---|---|---|\n")
        for r in receipt_records:
            f.write(f"| {r['governed_operations_receipt_intake_id']} | {r['source_governed_operations_cadence_handoff_id']} | {r['source_record_index']} |\n")
        f.write("\n")
        for r in receipt_records:
            f.write(f"## {r['governed_operations_receipt_intake_id']}\n")
            f.write(f"Source handoff ID: {r['source_governed_operations_cadence_handoff_id']}\n\n")
            f.write(f"Source record index: {r['source_record_index']}\n\n")
            f.write("Cadence handoff record (verbatim):\n\n")
            f.write("```")
            json.dump(r['cadence_handoff_record'], f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n```")
            f.write("\n\n")

if __name__ == "__main__":
    main()
