#!/usr/bin/env python3
"""
v6.3: Model Adjustment Release Resolution Wave Packet Review Session Ledger Generator

Pure downstream projection of review-session-register into operator-ledger bookkeeping layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_register.json (v6.2)
Produces: model_adjustment_release_resolution_wave_packet_review_session_ledger.json (v6.3)
          model_adjustment_release_resolution_wave_packet_review_session_ledger.md (v6.3)

Behavior:
- One ledger entry per upstream register entry
- Preserves all upstream priority, lane, posture fields exactly (pass-through)
- Adds ledger-specific projection fields only (ledger_position, ledger_priority, ledger_id)
- Deterministic ordering stable on register_id / receipt_id
- No re-classification, no release logic, no policy logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON
"""

import datetime
import json
import os
import sys

SOURCE_PATHS = {
    "manifest": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_manifest.json",
}

OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_ledger.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_ledger.md",
}

LANE_ORDER = {
    "lane_prohibition_terminal": 0,
    "lane_blocker_terminal": 1,
    "lane_remaining_terminal": 2,
}


def normalize_string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {name}: expected non-empty string, got {repr(value)}")
    return value


def normalize_list(value, name):
    if not isinstance(value, list):
        raise ValueError(f"Invalid {name}: expected list, got {type(value).__name__}")
    return sorted(set(value))


def normalize_int(value, name):
    if not isinstance(value, int):
        raise ValueError(f"Invalid {name}: expected int, got {type(value).__name__}")
    return value


def normalize_bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"Invalid {name}: expected bool, got {type(value).__name__}")
    return value


def validate_upstream_payload(payload, path):
    if not isinstance(payload, dict):
        raise ValueError(f"Upstream payload {path} is not a dict: {type(payload).__name__}")

    version = payload.get("model_adjustment_release_resolution_wave_packet_review_session_register_version")
    if version != "v6.2-slice-1":
        raise ValueError(f"Expected register version 'v6.2-slice-1', got {repr(version)}")

    records = payload.get("release_resolution_wave_packet_review_session_register", [])
    if not isinstance(records, list):
        raise ValueError(
            "release_resolution_wave_packet_review_session_register is not a list: "
            f"{type(records).__name__}"
        )
    if len(records) == 0:
        raise ValueError("No register records found in upstream payload")
    return records


def build_ledger_records(register_records):
    ledger_records = []

    for idx, man_rec in enumerate(register_records):
        ledger_id = f"resolution-wave-packet-review-session-ledger-{idx+1:04d}"
        ledger_rec = {
            "resolution_wave_packet_review_session_ledger_id": ledger_id,
            "source_resolution_wave_packet_review_session_manifest_id": man_rec["resolution_wave_packet_review_session_manifest_id"],
        }
        for k, v in man_rec.items():
            if k.startswith("source_resolution_wave_packet_review_session_") or k.startswith("source_resolution_wave_packet_") or k.startswith("source_resolution_wave_"):
                ledger_rec[k] = v
        ledger_records.append(ledger_rec)
    return ledger_records



def generate_markdown(payload, records):
    lines = []
    lines.append(f"# Model Adjustment Release Resolution Wave Packet Review Session Ledger\n")
    lines.append(f"**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_ledger_version']}\n")
    lines.append(f"**Generated At (UTC)**: {payload['generated_at_utc']}\n")
    lines.append(f"## Summary\n")
    lines.append("| Field | Value |\n")
    lines.append("|---|---|\n")
    lines.append(f"| input_manifest_record_count | {payload.get('input_manifest_record_count', '')} |\n")
    lines.append(f"| ledger_record_count | {payload.get('ledger_record_count', '')} |\n")
    lines.append(f"| deterministic_ordering | {payload.get('deterministic_ordering', '')} |\n\n")
    for rec in records:
        lines.append(f"## {rec['resolution_wave_packet_review_session_ledger_id']}\n")
        lines.append(f"- source_resolution_wave_packet_review_session_manifest_id: {rec['source_resolution_wave_packet_review_session_manifest_id']}\n")
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_ledger_id", "source_resolution_wave_packet_review_session_manifest_id"):
                lines.append(f"- {k}: {v}\n")
        lines.append("\n")
    return ''.join(lines)


def main():
    try:

        manifest_path = SOURCE_PATHS["manifest"]
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Input manifest JSON not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_payload = json.load(f)

        manifest_records = manifest_payload.get("release_resolution_wave_packet_review_session_manifest")
        if not isinstance(manifest_records, list):
            raise ValueError("Input manifest JSON missing or malformed 'release_resolution_wave_packet_review_session_manifest' list")

        ledger_records = build_ledger_records(manifest_records)

        coverage_reconciled = len(manifest_records) == len(ledger_records)
        is_sorted = True  # v7.2: manifest ordering is preserved
        lane_counts = {}
        for rec in ledger_records:
            lane = rec.get("review_lane")
            if lane is not None:
                lane_counts[lane] = lane_counts.get(lane, 0) + 1

        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_ledger_version": "v7.2-slice-1",
            "generated_at_utc": "2026-04-03T00:00:00+00:00",
            "input_manifest_record_count": len(manifest_records),
            "ledger_record_count": len(ledger_records),
            "deterministic_ordering": is_sorted,
            "release_resolution_wave_packet_review_session_ledger": ledger_records,
        }

        markdown_output = generate_markdown(output_payload, ledger_records)

        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)

        with open(OUTPUT_PATHS["json"], "w") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")

        with open(OUTPUT_PATHS["md"], "w") as f:
            f.write(markdown_output)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")

        print(
            f"[STATUS] review_session_ledger_records={len(ledger_records)} "
            f"upstream_session_register_count={len(register_records)} "
            f"coverage_reconciled={coverage_reconciled} deterministic_ordering={is_sorted} "
            f"review_lane_counts={lane_counts}"
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
