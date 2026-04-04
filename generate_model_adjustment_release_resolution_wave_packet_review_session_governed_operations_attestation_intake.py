"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake.py

Strict 1:1 deterministic intake envelope over frozen reconciliation-handoff records.
- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_reconciliation_handoff.json
- Output: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake.json
- Output: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake.md

Contracts:
- Deterministic, exact-once, order-preserving, no semantic mutation.
- IDs: resolution-wave-packet-review-session-governed-operations-attestation-intake-0001, ...
- Fail fast on schema or ID issues.
- Carry forward generated_at_utc from input.
"""
import json
import os
import sys
from pathlib import Path
from hashlib import sha256

INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_reconciliation_handoff.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake.md")

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-attestation-intake-"
ID_FIELD = "governed_operations_attestation_intake_id"
UPSTREAM_ID_FIELDS = [
    "governed_operations_reconciliation_handoff_id",
    "reconciliation_handoff_id",
    "handoff_id",
    "id"
]
SOURCE_ARTIFACT = str(INPUT_PATH)

FROZEN_GENERATED_AT_UTC = "2024-04-04T00:00:00Z"

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def load_input():
    if not INPUT_PATH.exists():
        fail(f"Input JSON not found: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data["records"], list):
        fail("Input JSON missing 'records' array.")
    return data

def resolve_upstream_id(rec):
    for field in UPSTREAM_ID_FIELDS:
        if field in rec and rec[field]:
            return rec[field]
    fail(f"No resolvable upstream reconciliation-handoff ID in record: {rec}")

def main():
    data = load_input()
    input_records = data["records"]
    record_count = len(input_records)
    if record_count == 0:
        fail("Input records array is empty.")
    # Carry forward generated_at_utc if present, else use frozen
    generated_at_utc = data.get("generated_at_utc", FROZEN_GENERATED_AT_UTC)
    # Resolve upstream IDs and check for duplicates
    resolved_ids = []
    for rec in input_records:
        resolved_ids.append(resolve_upstream_id(rec))
    if len(set(resolved_ids)) != len(resolved_ids):
        fail("Duplicate resolved upstream reconciliation-handoff IDs detected.")
    # Build output records
    output_records = []
    for idx, (rec, upstream_id) in enumerate(zip(input_records, resolved_ids), 1):
        output_records.append({
            ID_FIELD: f"{ID_PREFIX}{str(idx).zfill(4)}",
            "source_governed_operations_reconciliation_handoff_id": upstream_id,
            "source_record_index": idx,
            "source_artifact": SOURCE_ARTIFACT,
            "reconciliation_handoff_record": rec
        })
    # Top-level output
    output = {
        "artifact": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_attestation_intake",
        "source_artifact": SOURCE_ARTIFACT,
        "generated_at_utc": generated_at_utc,
        "record_count": record_count,
        "records": output_records
    }
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    # Markdown output
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Model Adjustment: Attestation Intake\n")
        f.write(f"\nSource artifact: {SOURCE_ARTIFACT}\n")
        f.write(f"\nRecord count: {record_count}\n")
        f.write("\n| Attestation Intake ID | Source Reconciliation-Handoff ID | Source Record Index |\n")
        f.write("|----------------------|-------------------------------|---------------------|\n")
        for r in output_records:
            f.write(f"| {r[ID_FIELD]} | {r['source_governed_operations_reconciliation_handoff_id']} | {r['source_record_index']} |\n")
        for r in output_records:
            f.write(f"\n---\n\n## {r[ID_FIELD]}\n\n")
            f.write(f"- Source reconciliation-handoff ID: {r['source_governed_operations_reconciliation_handoff_id']}\n")
            f.write(f"- Source record index: {r['source_record_index']}\n")
            f.write(f"- Source artifact: {r['source_artifact']}\n")
            f.write(f"\n### Reconciliation-handoff record\n\n")
            f.write("```")
            json.dump(r["reconciliation_handoff_record"], f, indent=2, ensure_ascii=False)
            f.write("\n```")
    print(f"Wrote {OUTPUT_JSON_PATH} and {OUTPUT_MD_PATH}")

if __name__ == "__main__":
    main()
