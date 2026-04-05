#!/usr/bin/env python3
"""
Generator for v63.2: controlled-release-resolution-wave-packet-review-session-governed-operations-enablement-assessment

Strict 1:1 deterministic assessment envelope over frozen enablement-intake records.
- Preserves order and payload semantics
- Adds only enablement-assessment identity and source linkage
- Fails fast on schema breakage or contract violation
"""
import json
import sys
from pathlib import Path

# --- Config ---
INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_enablement_intake.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_enablement_assessment.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_enablement_assessment.md")
ARTIFACT_ID = "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_enablement_assessment"
SOURCE_ARTIFACT = str(INPUT_PATH)
ASSESSMENT_ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-enablement-assessment-"
ASSESSMENT_ID_PAD = 4
FIXED_GENERATED_AT_UTC = None  # Will be set from input or fallback

# --- Helpers ---
def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def resolve_upstream_id(rec):
    for key in [
        "governed_operations_enablement_intake_id",
        "enablement_intake_id",
        "intake_id",
        "id"
    ]:
        if key in rec and rec[key]:
            return rec[key]
    fail("Could not resolve upstream enablement-intake ID in record: " + json.dumps(rec, indent=2))

def load_input():
    if not INPUT_PATH.exists():
        fail(f"Input JSON not found: {INPUT_PATH}")
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data["records"], list):
        fail("Input JSON missing 'records' array or not a list.")
    return data

def check_unique(seq):
    seen = set()
    for x in seq:
        if x in seen:
            return False
        seen.add(x)
    return True

def main():
    input_data = load_input()
    input_records = input_data["records"]
    record_count = len(input_records)
    if record_count == 0:
        fail("Input records array is empty.")

    # Determine generated_at_utc
    generated_at_utc = input_data.get("generated_at_utc") or "2023-01-01T00:00:00Z"

    # Build output records
    output_records = []
    resolved_ids = []
    for idx, rec in enumerate(input_records, 1):
        upstream_id = resolve_upstream_id(rec)
        resolved_ids.append(upstream_id)
        assessment_id = f"{ASSESSMENT_ID_PREFIX}{str(idx).zfill(ASSESSMENT_ID_PAD)}"
        output_records.append({
            "governed_operations_enablement_assessment_id": assessment_id,
            "source_governed_operations_enablement_intake_id": upstream_id,
            "source_record_index": idx,
            "source_artifact": SOURCE_ARTIFACT,
            "enablement_intake_record": rec
        })

    # Check uniqueness and count
    if not check_unique(resolved_ids):
        fail("Duplicate resolved upstream enablement-intake IDs detected.")
    if len(output_records) != record_count:
        fail("Output record count does not match input record count.")

    # Top-level output JSON
    output_json = {
        "artifact": ARTIFACT_ID,
        "source_artifact": SOURCE_ARTIFACT,
        "generated_at_utc": generated_at_utc,
        "record_count": record_count,
        "records": output_records
    }

    # Write JSON
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    # Write Markdown
    write_markdown(output_json)

def write_markdown(output_json):
    lines = []
    lines.append(f"# {output_json['artifact']}")
    lines.append(f"Source artifact: `{output_json['source_artifact']}`")
    lines.append(f"Record count: {output_json['record_count']}")
    lines.append("")
    lines.append("| Enablement Assessment ID | Source Enablement Intake ID | Source Index |")
    lines.append("|-------------------------|-----------------------------|--------------|")
    for rec in output_json["records"]:
        lines.append(f"| {rec['governed_operations_enablement_assessment_id']} | {rec['source_governed_operations_enablement_intake_id']} | {rec['source_record_index']} |")
    lines.append("")
    for rec in output_json["records"]:
        lines.append(f"## {rec['governed_operations_enablement_assessment_id']}")
        lines.append(f"Source enablement-intake ID: `{rec['source_governed_operations_enablement_intake_id']}`")
        lines.append(f"Source record index: {rec['source_record_index']}")
        lines.append(f"Source artifact: `{rec['source_artifact']}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(rec["enablement_intake_record"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
