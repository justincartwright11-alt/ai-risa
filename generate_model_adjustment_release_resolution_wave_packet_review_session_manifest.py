#!/usr/bin/env python3
"""
v7.1: Model Adjustment Release Resolution Wave Packet Review Session Manifest Generator

Pure downstream projection of review-session-registry into manifest layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_registry.json (v7.0)
Produces: model_adjustment_release_resolution_wave_packet_review_session_manifest.json (v7.1)
          model_adjustment_release_resolution_wave_packet_review_session_manifest.md (v7.1)

Behavior:
- One manifest entry per upstream registry entry
- Preserves ordering and coverage exactly
- Adds manifest ID and required source fields only
- Deterministic ordering, unique IDs, exact-once coverage
- Markdown is a pure projection of JSON
- No policy or release logic
"""

import json
import os
import sys

SOURCE_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_registry.json"
OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_manifest.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_manifest.md",
}

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"

MANIFEST_VERSION = "v7.1-slice-1"
MANIFEST_LIST_KEY = "release_resolution_wave_packet_review_session_manifest"


def main():
    if not os.path.exists(SOURCE_PATH):
        raise FileNotFoundError(f"Input registry JSON not found: {SOURCE_PATH}")
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        registry_payload = json.load(f)
    registry_records = registry_payload.get("release_resolution_wave_packet_review_session_registry")
    if not isinstance(registry_records, list):
        raise ValueError("Input registry JSON missing or malformed 'release_resolution_wave_packet_review_session_registry' list")
    manifest_records = []
    for idx, reg_rec in enumerate(registry_records):
        manifest_id = f"resolution-wave-packet-review-session-manifest-{idx+1:04d}"
        manifest_rec = {
            "resolution_wave_packet_review_session_manifest_id": manifest_id,
            "source_resolution_wave_packet_review_session_registry_id": reg_rec["resolution_wave_packet_review_session_registry_id"],
            # Downstream family convention: include all source_* fields from registry
        }
        for k, v in reg_rec.items():
            if k.startswith("source_resolution_wave_packet_review_session_") or k.startswith("source_resolution_wave_packet_") or k.startswith("source_resolution_wave_"):
                manifest_rec[k] = v
        manifest_records.append(manifest_rec)
    output_payload = {
        "model_adjustment_release_resolution_wave_packet_review_session_manifest_version": MANIFEST_VERSION,
        "generated_at_utc": FROZEN_TIMESTAMP,
        MANIFEST_LIST_KEY: manifest_records,
        "input_registry_record_count": len(registry_records),
        "manifest_record_count": len(manifest_records),
        "deterministic_ordering": True,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)
    with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
    md = generate_markdown(output_payload, manifest_records)
    with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
    print(f"[STATUS] manifest_records={len(manifest_records)} input_registry_records={len(registry_records)} deterministic_ordering=True")

def generate_markdown(payload, records):
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Manifest\n\n**Version**: {payload['model_adjustment_release_resolution_wave_packet_review_session_manifest_version']}\n**Generated At (UTC)**: {payload['generated_at_utc']}\n\n## Summary\n\n| Field | Value |\n|---|---|\n| input_registry_record_count | {payload['input_registry_record_count']} |\n| manifest_record_count | {payload['manifest_record_count']} |\n| deterministic_ordering | {payload['deterministic_ordering']} |\n\n"""
    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_manifest_id']}\n\n- source_resolution_wave_packet_review_session_registry_id: {rec['source_resolution_wave_packet_review_session_registry_id']}\n"""
        for k, v in rec.items():
            if k not in ("resolution_wave_packet_review_session_manifest_id", "source_resolution_wave_packet_review_session_registry_id"):
                md += f"- {k}: {v}\n"
        md += "\n"
    return md

if __name__ == "__main__":
    main()
