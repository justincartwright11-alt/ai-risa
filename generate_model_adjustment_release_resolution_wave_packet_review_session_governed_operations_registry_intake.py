#!/usr/bin/env python3
"""
Generator for v52.1: controlled-release-resolution-wave-packet-review-session-governed-operations-registry-intake
Strict 1:1 deterministic intake envelope over frozen audit-handoff records.

Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_audit_handoff.json
Output: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_registry_intake.json
        ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_registry_intake.md
"""
import json
import os
import sys
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_audit_handoff.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_registry_intake.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_registry_intake.md"

REGISTRY_ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-registry-intake-"
REGISTRY_ID_PAD = 4

FIXED_GENERATED_AT_UTC = "2024-01-01T00:00:00Z"

# Fail fast utility
def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def resolve_upstream_id(rec):
    for key in [
        "governed_operations_audit_handoff_id",
        "audit_handoff_id",
        "handoff_id",
        "id"
    ]:
        if key in rec and rec[key]:
            return rec[key]
    fail("Could not resolve upstream audit-handoff ID in record: " + json.dumps(rec, indent=2))

def main():
    # Load input
    if not os.path.exists(INPUT_PATH):
        fail(f"Input JSON not found: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data["records"], list):
        fail("Input JSON missing 'records' array.")
    input_records = data["records"]
    if not input_records:
        fail("Input JSON 'records' array is empty.")

    # Carry forward or freeze generated_at_utc
    generated_at_utc = data.get("generated_at_utc", FIXED_GENERATED_AT_UTC)

    # Build output records
    seen_upstream_ids = set()
    output_records = []
    for idx, rec in enumerate(input_records, 1):
        upstream_id = resolve_upstream_id(rec)
        if upstream_id in seen_upstream_ids:
            fail(f"Duplicate upstream audit-handoff ID: {upstream_id}")
        seen_upstream_ids.add(upstream_id)
        registry_id = f"{REGISTRY_ID_PREFIX}{str(idx).zfill(REGISTRY_ID_PAD)}"
        output_records.append({
            "governed_operations_registry_intake_id": registry_id,
            "source_governed_operations_audit_handoff_id": upstream_id,
            "source_record_index": idx,
            "source_artifact": INPUT_PATH,
            "audit_handoff_record": rec
        })

    # Validate record count
    if len(output_records) != len(input_records):
        fail("Output record count does not match input record count.")

    # Top-level output JSON
    output_json = {
        "artifact": "controlled-release-resolution-wave-packet-review-session-governed-operations-registry-intake",
        "source_artifact": INPUT_PATH,
        "generated_at_utc": generated_at_utc,
        "record_count": len(output_records),
        "records": output_records
    }

    # Write JSON output
    Path(os.path.dirname(OUTPUT_JSON_PATH)).mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    # Write Markdown output
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Controlled Release Resolution Wave Packet Review Session Governed Operations Registry Intake\n\n")
        f.write(f"Source artifact: `{INPUT_PATH}`\n\n")
        f.write(f"Record count: {len(output_records)}\n\n")
        f.write("| Registry-Intake ID | Source Audit-Handoff ID | Source Record Index |\n")
        f.write("|--------------------|------------------------|---------------------|\n")
        for r in output_records:
            f.write(f"| {r['governed_operations_registry_intake_id']} | {r['source_governed_operations_audit_handoff_id']} | {r['source_record_index']} |\n")
        f.write("\n")
        for r in output_records:
            f.write(f"## {r['governed_operations_registry_intake_id']}\n\n")
            f.write(f"Source audit-handoff ID: {r['source_governed_operations_audit_handoff_id']}\n\n")
            f.write(f"Source record index: {r['source_record_index']}\n\n")
            f.write(f"Source artifact: `{INPUT_PATH}`\n\n")
            f.write("Audit handoff record:\n\n")
            f.write("```")
            f.write(json.dumps(r['audit_handoff_record'], indent=2, ensure_ascii=False))
            f.write("\n```")
            f.write("\n\n")

if __name__ == "__main__":
    main()
