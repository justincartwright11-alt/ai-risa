"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_handoff.py

Implements v46.3 kickoff spec: strict 1:1 deterministic handoff envelope over frozen dispatch-assessment records.

- Input: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_assessment.json
- Output: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_handoff.json, .md
- See v46.3 kickoff for all contracts and validation requirements.
"""
import json
import os
import sys

INPUT_JSON = os.path.join(
    "ops", "model_adjustments", "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_assessment.json"
)
OUTPUT_JSON = os.path.join(
    "ops", "model_adjustments", "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_handoff.json"
)
OUTPUT_MD = os.path.join(
    "ops", "model_adjustments", "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_handoff.md"
)

FAMILY_ID = "resolution-wave-packet-review-session-governed-operations-dispatch-handoff"
ARTIFACT_ID = "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_handoff"
SOURCE_ARTIFACT = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_assessment.json"

ID_FIELD = "governed_operations_dispatch_handoff_id"
UPSTREAM_ID_FIELDS = [
    "governed_operations_dispatch_assessment_id",
    "dispatch_assessment_id",
    "assessment_id",
    "id"
]

# Fail fast helper
def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def load_input():
    if not os.path.exists(INPUT_JSON):
        fail(f"Input JSON not found: {INPUT_JSON}")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data["records"], list):
        fail("Input JSON missing 'records' array.")
    return data

def resolve_upstream_id(record):
    for field in UPSTREAM_ID_FIELDS:
        if field in record and record[field]:
            return record[field]
    fail(f"No valid upstream dispatch-assessment ID found in record: {record}")

def make_dispatch_handoff_id(idx):
    return f"{FAMILY_ID}-{'%04d' % (idx+1)}"

def main():
    input_data = load_input()
    input_records = input_data["records"]
    n = len(input_records)
    output_records = []
    seen_upstream_ids = set()
    for idx, rec in enumerate(input_records):
        upstream_id = resolve_upstream_id(rec)
        if upstream_id in seen_upstream_ids:
            fail(f"Duplicate upstream dispatch-assessment ID: {upstream_id}")
        seen_upstream_ids.add(upstream_id)
        out_id = make_dispatch_handoff_id(idx)
        output_records.append({
            ID_FIELD: out_id,
            "source_governed_operations_dispatch_assessment_id": upstream_id,
            "source_record_index": idx+1,
            "source_artifact": SOURCE_ARTIFACT,
            "dispatch_assessment_record": rec
        })
    if len(output_records) != n:
        fail("Output record count does not match input record count.")
    # Top-level envelope with frozen metadata
    frozen_generated_at_utc = input_data.get("generated_at_utc", "2026-04-04T00:00:00Z")
    output = {
        "artifact": ARTIFACT_ID,
        "family": FAMILY_ID,
        "source_artifact": SOURCE_ARTIFACT,
        "record_count": n,
        "records": output_records,
        "generated_at_utc": frozen_generated_at_utc
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    # Markdown projection
    write_markdown(output)
    print(f"Wrote {OUTPUT_JSON} and {OUTPUT_MD}")

def write_markdown(output):
    lines = []
    lines.append(f"# {output['artifact']}")
    lines.append("")
    lines.append(f"Source artifact: `{output['source_artifact']}`")
    lines.append(f"Record count: {output['record_count']}")
    lines.append("")
    # Mapping table
    lines.append("| Dispatch Handoff ID | Source Dispatch-Assessment ID | Source Record Index |")
    lines.append("|--------------------|-------------------------------|---------------------|")
    for rec in output["records"]:
        lines.append(f"| {rec[ID_FIELD]} | {rec['source_governed_operations_dispatch_assessment_id']} | {rec['source_record_index']} |")
    lines.append("")
    # Per-record sections
    for rec in output["records"]:
        lines.append(f"## {rec[ID_FIELD]}")
        lines.append(f"Source dispatch-assessment ID: {rec['source_governed_operations_dispatch_assessment_id']}")
        lines.append(f"Source record index: {rec['source_record_index']}")
        lines.append(f"Source artifact: `{rec['source_artifact']}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(rec["dispatch_assessment_record"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
