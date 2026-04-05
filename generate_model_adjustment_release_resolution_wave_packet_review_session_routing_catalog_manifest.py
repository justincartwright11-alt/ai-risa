import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_registry.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.7-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_catalog_manifest"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_catalog_registry = json.load(f)["release_resolution_wave_packet_review_session_routing_catalog_registry"]

# Build routing-catalog-manifest records
manifest_records = []
for i, registry_record in enumerate(routing_catalog_registry, 1):
    manifest_id = f"resolution-wave-packet-review-session-routing-catalog-manifest-{i:04d}"
    manifest_record = {
        "resolution_wave_packet_review_session_routing_catalog_manifest_id": manifest_id,
        "source_resolution_wave_packet_review_session_routing_catalog_registry_id": registry_record["resolution_wave_packet_review_session_routing_catalog_registry_id"],
        # Pure downstream projection: copy all source_* fields from registry_record
        **{k: v for k, v in registry_record.items() if k.startswith("source_")}
    }
    manifest_records.append(manifest_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_catalog_registry_record_count": len(routing_catalog_registry),
    "routing_catalog_manifest_record_count": len(manifest_records),
    "deterministic_ordering": True,
    LIST_KEY: manifest_records
}

with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

# Compose Markdown as a pure projection of JSON
def to_md_table(records):
    if not records:
        return "| (no records) |\n"
    headers = list(records[0].keys())
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for rec in records:
        lines.append("| " + " | ".join(str(rec[h]) for h in headers) + " |")
    return "\n".join(lines)

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Catalog Manifest (v8.7)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-catalog-registry record count: {len(routing_catalog_registry)}
- Routing-catalog-manifest record count: {len(manifest_records)}
- Deterministic ordering: True

## Routing Catalog Manifest Records

{to_md_table(manifest_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
