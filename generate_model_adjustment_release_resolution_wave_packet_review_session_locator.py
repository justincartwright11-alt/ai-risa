#!/usr/bin/env python3
"""
v6.9: Model Adjustment Release Resolution Wave Packet Review Session Locator Generator

Pure downstream projection of review-session-directory into locator layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_directory.json (v6.8)
Produces: model_adjustment_release_resolution_wave_packet_review_session_locator.json (v6.9)
          model_adjustment_release_resolution_wave_packet_review_session_locator.md (v6.9)

Behavior:
- One locator entry per upstream directory entry
- Preserves ordering and coverage exactly
- Adds locator ID and required source fields only
- Deterministic ordering, unique IDs, exact-once coverage
- Markdown is a pure projection of JSON
- No policy or release logic
"""

import json
import os
import sys

SOURCE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_directory.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_locator.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_locator.md",
}

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"

LOCATOR_VERSION = "v6.9-slice-1"
LOCATOR_LIST_KEY = "release_resolution_wave_packet_review_session_locator"


def main():
    if not os.path.exists(SOURCE_PATH):
        raise FileNotFoundError(f"Input directory JSON not found: {SOURCE_PATH}")
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        directory_payload = json.load(f)
    directory_records = directory_payload.get("release_resolution_wave_packet_review_session_directory")
    if not isinstance(directory_records, list):
        raise ValueError("Input directory JSON missing or malformed 'release_resolution_wave_packet_review_session_directory' list")
    locator_records = []
    for idx, dir_rec in enumerate(directory_records):
        locator_id = f"resolution-wave-packet-review-session-locator-{idx+1:04d}"
        locator_rec = {
            "resolution_wave_packet_review_session_locator_id": locator_id,
            "source_resolution_wave_packet_review_session_directory_id": dir_rec["resolution_wave_packet_review_session_directory_id"],
            # Downstream family convention: include all source_* fields from directory
        }
        for k, v in dir_rec.items():
            if k.startswith("source_resolution_wave_packet_review_session_") or k.startswith("source_resolution_wave_packet_") or k.startswith("source_resolution_wave_"):
                locator_rec[k] = v
        locator_records.append(locator_rec)
    output_payload = {
        "model_adjustment_release_resolution_wave_packet_review_session_locator_version": LOCATOR_VERSION,
        "generated_at_utc": FROZEN_TIMESTAMP,
        LOCATOR_LIST_KEY: locator_records,
        "input_directory_record_count": len(directory_records),
        "locator_record_count": len(locator_records),
        "deterministic_ordering": True,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
    with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
    md = generate_markdown(output_payload, locator_records)
    with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
    print(f"[STATUS] locator_records={len(locator_records)} input_directory_records={len(directory_records)} deterministic_ordering=True")

def generate_markdown(payload, records):
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Locator\n\n**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_locator_version']}\n**Generated At (UTC)**: {payload['generated_at_utc']}\n\n## Summary\n\n| Field | Value |\n|---|---|\n| input_directory_record_count | {payload['input_directory_record_count']} |\n| locator_record_count | {payload['locator_record_count']} |\n| deterministic_ordering | {payload['deterministic_ordering']} |\n\n"""
    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_locator_id']}\n\n- source_resolution_wave_packet_review_session_directory_id: {rec['source_resolution_wave_packet_review_session_directory_id']}\n"""
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_locator_id", "source_resolution_wave_packet_review_session_directory_id"):
                md += f"- {k}: {v}\n"
        md += "\n"
    return md

if __name__ == "__main__":
    main()
