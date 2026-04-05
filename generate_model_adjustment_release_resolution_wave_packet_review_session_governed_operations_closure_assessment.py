#!/usr/bin/env python3
"""
Generator: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment
Slice: v49.2-controlled-release-resolution-wave-packet-review-session-governed-operations-closure-assessment

Strict 1:1 deterministic assessment envelope over frozen closure-intake records.

Input:  ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_intake.json
Output: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment.json
        ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment.md

See script docstring for full contract.
"""
import json
import os
import sys
from pathlib import Path
from collections import Counter

# --- Config ---
INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_execution_state.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment.md"
ASSESSMENT_ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-assessment-"
ASSESSMENT_ID_PAD = 4

# --- Utility ---
def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def resolve_upstream_id(rec):
    # For v64.7, upstream is execution-state record's id
    for k in [
        "governed_operations_execution_state_id",
        "id"
    ]:
        if k in rec and rec[k]:
            return rec[k]
    fail("No resolvable upstream execution-state ID in record: " + json.dumps(rec, indent=2))

def load_input():
    if not os.path.exists(INPUT_JSON):
        fail(f"Input JSON not found: {INPUT_JSON}")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        fail("Input JSON must be a list of execution-state records.")
    return data

def main():
    input_records = load_input()
    record_count = len(input_records)
    if record_count == 0:
        fail("Input records array is empty.")

    # Resolve upstream IDs and check for duplicates
    resolved_ids = []
    for rec in input_records:
        resolved_ids.append(resolve_upstream_id(rec))
    if len(set(resolved_ids)) != len(resolved_ids):
        fail("Duplicate resolved upstream execution-state IDs detected.")

    # Build output records
    output_records = []
    for idx, (rec, resolved_id) in enumerate(zip(input_records, resolved_ids), 1):
        assessment_id = f"{ASSESSMENT_ID_PREFIX}{str(idx).zfill(ASSESSMENT_ID_PAD)}"
        output_records.append({
            "governed_operations_closure_assessment_id": assessment_id,
            "source_governed_operations_execution_state_id": resolved_id,
            "source_record_index": idx,
            "source_artifact": INPUT_JSON,
            "execution_state_record": rec
        })

    # Top-level metadata
    output = {
        "artifact": "model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_assessment",
        "source_artifact": INPUT_JSON,
        "record_count": record_count,
        "records": output_records,
        "generated_at_utc": "2026-04-04T00:00:00Z"
    }

    # Write JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Write Markdown
    write_markdown(output)
    print(f"Wrote {OUTPUT_JSON} and {OUTPUT_MD}")

def write_markdown(output):
    lines = []
    lines.append(f"# Model Adjustment Release Resolution Wave Packet Review Session Governed Operations Closure Assessment\n")
    lines.append(f"Source artifact: `{output['source_artifact']}`  ")
    lines.append(f"Record count: {output['record_count']}\n")
    # Mapping table
    lines.append("| Closure Assessment ID | Source Execution State ID | Source Index |")
    lines.append("|---|---|---|")
    for rec in output["records"]:
        lines.append(f"| {rec['governed_operations_closure_assessment_id']} | {rec['source_governed_operations_execution_state_id']} | {rec['source_record_index']} |")
    lines.append("")
    # Per-record sections
    for rec in output["records"]:
        lines.append(f"## {rec['governed_operations_closure_assessment_id']}")
        lines.append(f"Source execution state ID: {rec['source_governed_operations_execution_state_id']}")
        lines.append(f"Source record index: {rec['source_record_index']}")
        lines.append(f"Source artifact: `{rec['source_artifact']}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(rec["execution_state_record"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
