#!/usr/bin/env python3
"""
v7.4: Model Adjustment Release Resolution Wave Packet Review Session Index Map Generator

Pure downstream projection of review-session-map into review-session-index-map.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_map.json (v7.3)
Produces: model_adjustment_release_resolution_wave_packet_review_session_index_map.json (v7.4)
          model_adjustment_release_resolution_wave_packet_review_session_index_map.md (v7.4)

Behavior:
- One index-map entry per upstream map entry
- Preserves all upstream ordering and fields (pass-through)
- Adds index-map-specific projection fields only (index_map_id)
- Deterministic ordering stable on input order
- No policy logic, no release logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON
"""

import json
import os
import sys

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_map.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_index_map.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_index_map.md",
}
FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
INDEX_MAP_VERSION = "v7.4-slice-1"
INDEX_MAP_LIST_KEY = "release_resolution_wave_packet_review_session_index_map"


def build_index_map_records(map_records):
    index_map_records = []
    for idx, map_rec in enumerate(map_records):
        index_map_id = f"resolution-wave-packet-review-session-index-map-{idx+1:04d}"
        index_map_rec = {
            "resolution_wave_packet_review_session_index_map_id": index_map_id,
            "source_resolution_wave_packet_review_session_map_id": map_rec["resolution_wave_packet_review_session_map_id"],
        }
        # Pass through all source_* fields and other relevant fields
        for k, v in map_rec.items():
            if k != "resolution_wave_packet_review_session_map_id":
                index_map_rec[k] = v
        index_map_records.append(index_map_rec)
    return index_map_records


def generate_markdown(payload, records):
    lines = []
    lines.append(f"# Model Adjustment Release Resolution Wave Packet Review Session Index Map\n")
    lines.append(f"**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_index_map_version']}\n")
    lines.append(f"**Generated At (UTC)**: {payload['generated_at_utc']}\n")
    lines.append(f"## Summary\n")
    lines.append("| Field | Value |\n")
    lines.append("|---|---|\n")
    lines.append(f"| input_map_record_count | {payload['input_map_record_count']} |\n")
    lines.append(f"| index_map_record_count | {payload['index_map_record_count']} |\n")
    lines.append(f"| deterministic_ordering | {payload['deterministic_ordering']} |\n\n")
    for rec in records:
        lines.append(f"## {rec['resolution_wave_packet_review_session_index_map_id']}\n")
        lines.append(f"- source_resolution_wave_packet_review_session_map_id: {rec['source_resolution_wave_packet_review_session_map_id']}\n")
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_index_map_id", "source_resolution_wave_packet_review_session_map_id"):
                lines.append(f"- {k}: {v}\n")
        lines.append("\n")
    return ''.join(lines)


def main():
    try:
        if not os.path.exists(INPUT_PATH):
            raise FileNotFoundError(f"Input map JSON not found: {INPUT_PATH}")
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            map_payload = json.load(f)
        map_records = map_payload.get("release_resolution_wave_packet_review_session_map")
        if not isinstance(map_records, list):
            raise ValueError("Input map JSON missing or malformed 'release_resolution_wave_packet_review_session_map' list")
        index_map_records = build_index_map_records(map_records)
        coverage_reconciled = len(map_records) == len(index_map_records)
        is_sorted = True  # ordering is preserved
        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_index_map_version": INDEX_MAP_VERSION,
            "generated_at_utc": FROZEN_TIMESTAMP,
            "input_map_record_count": len(map_records),
            "index_map_record_count": len(index_map_records),
            "deterministic_ordering": is_sorted,
            INDEX_MAP_LIST_KEY: index_map_records,
        }
        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
        with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
        md = generate_markdown(output_payload, index_map_records)
        with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
        print(f"[STATUS] index_map_records={len(index_map_records)} input_map_records={len(map_records)} deterministic_ordering=True")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
