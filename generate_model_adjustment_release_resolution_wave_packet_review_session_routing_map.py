#!/usr/bin/env python3
"""
v7.5: Model Adjustment Release Resolution Wave Packet Review Session Routing Map Generator

Pure downstream projection of review-session-index-map into review-session-routing-map.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_index_map.json (v7.4)
Produces: model_adjustment_release_resolution_wave_packet_review_session_routing_map.json (v7.5)
          model_adjustment_release_resolution_wave_packet_review_session_routing_map.md (v7.5)

Behavior:
- One routing-map entry per upstream index-map entry
- Preserves all upstream ordering and fields (pass-through)
- Adds routing-map-specific projection fields only (routing_map_id)
- Deterministic ordering stable on input order
- No policy logic, no release logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON
"""

import json
import os
import sys

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_index_map.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_map.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_map.md",
}
FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
ROUTING_MAP_VERSION = "v7.5-slice-1"
ROUTING_MAP_LIST_KEY = "release_resolution_wave_packet_review_session_routing_map"


def build_routing_map_records(index_map_records):
    routing_map_records = []
    for idx, index_map_rec in enumerate(index_map_records):
        routing_map_id = f"resolution-wave-packet-review-session-routing-map-{idx+1:04d}"
        routing_map_rec = {
            "resolution_wave_packet_review_session_routing_map_id": routing_map_id,
            "source_resolution_wave_packet_review_session_index_map_id": index_map_rec["resolution_wave_packet_review_session_index_map_id"],
        }
        # Pass through all source_* fields and other relevant fields
        for k, v in index_map_rec.items():
            if k != "resolution_wave_packet_review_session_index_map_id":
                routing_map_rec[k] = v
        routing_map_records.append(routing_map_rec)
    return routing_map_records


def generate_markdown(payload, records):
    lines = []
    lines.append(f"# Model Adjustment Release Resolution Wave Packet Review Session Routing Map\n")
    lines.append(f"**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_routing_map_version']}\n")
    lines.append(f"**Generated At (UTC)**: {payload['generated_at_utc']}\n")
    lines.append(f"## Summary\n")
    lines.append("| Field | Value |\n")
    lines.append("|---|---|\n")
    lines.append(f"| input_index_map_record_count | {payload['input_index_map_record_count']} |\n")
    lines.append(f"| routing_map_record_count | {payload['routing_map_record_count']} |\n")
    lines.append(f"| deterministic_ordering | {payload['deterministic_ordering']} |\n\n")
    for rec in records:
        lines.append(f"## {rec['resolution_wave_packet_review_session_routing_map_id']}\n")
        lines.append(f"- source_resolution_wave_packet_review_session_index_map_id: {rec['source_resolution_wave_packet_review_session_index_map_id']}\n")
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_routing_map_id", "source_resolution_wave_packet_review_session_index_map_id"):
                lines.append(f"- {k}: {v}\n")
        lines.append("\n")
    return ''.join(lines)


def main():
    try:
        if not os.path.exists(INPUT_PATH):
            raise FileNotFoundError(f"Input index-map JSON not found: {INPUT_PATH}")
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            index_map_payload = json.load(f)
        index_map_records = index_map_payload.get("release_resolution_wave_packet_review_session_index_map")
        if not isinstance(index_map_records, list):
            raise ValueError("Input index-map JSON missing or malformed 'release_resolution_wave_packet_review_session_index_map' list")
        routing_map_records = build_routing_map_records(index_map_records)
        coverage_reconciled = len(index_map_records) == len(routing_map_records)
        is_sorted = True  # ordering is preserved
        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_routing_map_version": ROUTING_MAP_VERSION,
            "generated_at_utc": FROZEN_TIMESTAMP,
            "input_index_map_record_count": len(index_map_records),
            "routing_map_record_count": len(routing_map_records),
            "deterministic_ordering": is_sorted,
            ROUTING_MAP_LIST_KEY: routing_map_records,
        }
        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
        with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
        md = generate_markdown(output_payload, routing_map_records)
        with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
        print(f"[STATUS] routing_map_records={len(routing_map_records)} input_index_map_records={len(index_map_records)} deterministic_ordering=True")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
