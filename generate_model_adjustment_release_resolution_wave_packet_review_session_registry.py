#!/usr/bin/env python3
"""
v7.0: Model Adjustment Release Resolution Wave Packet Review Session Registry Generator

Pure downstream projection of review-session-locator into registry layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_locator.json (v6.9)
Produces: model_adjustment_release_resolution_wave_packet_review_session_registry.json (v7.0)
          model_adjustment_release_resolution_wave_packet_review_session_registry.md (v7.0)

Behavior:
- One registry entry per upstream locator entry
- Preserves ordering and coverage exactly
- Adds registry ID and required source fields only
- Deterministic ordering, unique IDs, exact-once coverage
- Markdown is a pure projection of JSON
- No policy or release logic
"""

import json
import os
import sys

SOURCE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_locator.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_registry.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_registry.md",
}

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"

REGISTRY_VERSION = "v7.0-slice-1"
REGISTRY_LIST_KEY = "release_resolution_wave_packet_review_session_registry"


def main():
    if not os.path.exists(SOURCE_PATH):
        raise FileNotFoundError(f"Input locator JSON not found: {SOURCE_PATH}")
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        locator_payload = json.load(f)
    locator_records = locator_payload.get("release_resolution_wave_packet_review_session_locator")
    if not isinstance(locator_records, list):
        raise ValueError("Input locator JSON missing or malformed 'release_resolution_wave_packet_review_session_locator' list")
    registry_records = []
    for idx, loc_rec in enumerate(locator_records):
        registry_id = f"resolution-wave-packet-review-session-registry-{idx+1:04d}"
        registry_rec = {
            "resolution_wave_packet_review_session_registry_id": registry_id,
            "source_resolution_wave_packet_review_session_locator_id": loc_rec["resolution_wave_packet_review_session_locator_id"],
            # Downstream family convention: include all source_* fields from locator
        }
        for k, v in loc_rec.items():
            if k.startswith("source_resolution_wave_packet_review_session_") or k.startswith("source_resolution_wave_packet_") or k.startswith("source_resolution_wave_"):
                registry_rec[k] = v
        registry_records.append(registry_rec)
    output_payload = {
        "model_adjustment_release_resolution_wave_packet_review_session_registry_version": REGISTRY_VERSION,
        "generated_at_utc": FROZEN_TIMESTAMP,
        REGISTRY_LIST_KEY: registry_records,
        "input_locator_record_count": len(locator_records),
        "registry_record_count": len(registry_records),
        "deterministic_ordering": True,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
    with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
    md = generate_markdown(output_payload, registry_records)
    with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
    print(f"[STATUS] registry_records={len(registry_records)} input_locator_records={len(locator_records)} deterministic_ordering=True")

def generate_markdown(payload, records):
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Registry\n\n**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_registry_version']}\n**Generated At (UTC)**: {payload['generated_at_utc']}\n\n## Summary\n\n| Field | Value |\n|---|---|\n| input_locator_record_count | {payload['input_locator_record_count']} |\n| registry_record_count | {payload['registry_record_count']} |\n| deterministic_ordering | {payload['deterministic_ordering']} |\n\n"""
    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_registry_id']}\n\n- source_resolution_wave_packet_review_session_locator_id: {rec['source_resolution_wave_packet_review_session_locator_id']}\n"""
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_registry_id", "source_resolution_wave_packet_review_session_locator_id"):
                md += f"- {k}: {v}\n"
        md += "\n"
    return md

if __name__ == "__main__":
    main()
