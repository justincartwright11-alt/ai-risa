#!/usr/bin/env python3
"""
v7.3: Model Adjustment Release Resolution Wave Packet Review Session Map Generator

Pure downstream projection of review-session-ledger into review-session-map.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_ledger.json (v7.2)
Produces: model_adjustment_release_resolution_wave_packet_review_session_map.json (v7.3)
          model_adjustment_release_resolution_wave_packet_review_session_map.md (v7.3)

Behavior:
- One map entry per upstream ledger entry
- Preserves all upstream ordering and fields (pass-through)
- Adds map-specific projection fields only (map_id)
- Deterministic ordering stable on input order
- No policy logic, no release logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON
"""

import json
import os
import sys

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_ledger.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_map.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_map.md",
}
FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
MAP_VERSION = "v7.3-slice-1"
MAP_LIST_KEY = "release_resolution_wave_packet_review_session_map"


def build_map_records(ledger_records):
    map_records = []
    for idx, ledger_rec in enumerate(ledger_records):
        map_id = f"resolution-wave-packet-review-session-map-{idx+1:04d}"
        map_rec = {
            "resolution_wave_packet_review_session_map_id": map_id,
            "source_resolution_wave_packet_review_session_ledger_id": ledger_rec["resolution_wave_packet_review_session_ledger_id"],
        }
        # Pass through all source_* fields and other relevant fields
        for k, v in ledger_rec.items():
            if k != "resolution_wave_packet_review_session_ledger_id":
                map_rec[k] = v
        map_records.append(map_rec)
    return map_records


def generate_markdown(payload, records):
    lines = []
    lines.append(f"# Model Adjustment Release Resolution Wave Packet Review Session Map\n")
    lines.append(f"**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_map_version']}\n")
    lines.append(f"**Generated At (UTC)**: {payload['generated_at_utc']}\n")
    lines.append(f"## Summary\n")
    lines.append("| Field | Value |\n")
    lines.append("|---|---|\n")
    lines.append(f"| input_ledger_record_count | {payload['input_ledger_record_count']} |\n")
    lines.append(f"| map_record_count | {payload['map_record_count']} |\n")
    lines.append(f"| deterministic_ordering | {payload['deterministic_ordering']} |\n\n")
    for rec in records:
        lines.append(f"## {rec['resolution_wave_packet_review_session_map_id']}\n")
        lines.append(f"- source_resolution_wave_packet_review_session_ledger_id: {rec['source_resolution_wave_packet_review_session_ledger_id']}\n")
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_map_id", "source_resolution_wave_packet_review_session_ledger_id"):
                lines.append(f"- {k}: {v}\n")
        lines.append("\n")
    return ''.join(lines)


def main():
    try:
        if not os.path.exists(INPUT_PATH):
            raise FileNotFoundError(f"Input ledger JSON not found: {INPUT_PATH}")
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            ledger_payload = json.load(f)
        ledger_records = ledger_payload.get("release_resolution_wave_packet_review_session_ledger")
        if not isinstance(ledger_records, list):
            raise ValueError("Input ledger JSON missing or malformed 'release_resolution_wave_packet_review_session_ledger' list")
        map_records = build_map_records(ledger_records)
        coverage_reconciled = len(ledger_records) == len(map_records)
        is_sorted = True  # ordering is preserved
        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_map_version": MAP_VERSION,
            "generated_at_utc": FROZEN_TIMESTAMP,
            "input_ledger_record_count": len(ledger_records),
            "map_record_count": len(map_records),
            "deterministic_ordering": is_sorted,
            MAP_LIST_KEY: map_records,
        }
        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
        with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
        md = generate_markdown(output_payload, map_records)
        with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
        print(f"[STATUS] map_records={len(map_records)} input_ledger_records={len(ledger_records)} deterministic_ordering=True")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
