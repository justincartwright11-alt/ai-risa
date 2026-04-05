import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_manifest.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.4-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_catalog"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_manifest = json.load(f)["release_resolution_wave_packet_review_session_routing_manifest"]

# Build routing-catalog records
catalog_records = []
for i, manifest_record in enumerate(routing_manifest, 1):
    catalog_id = f"resolution-wave-packet-review-session-routing-catalog-{i:04d}"
    catalog_record = {
        "resolution_wave_packet_review_session_routing_catalog_id": catalog_id,
        "source_resolution_wave_packet_review_session_routing_manifest_id": manifest_record["resolution_wave_packet_review_session_routing_manifest_id"],
        # Pure downstream projection: copy all source_* fields from manifest_record
        **{k: v for k, v in manifest_record.items() if k.startswith("source_")}
    }
    catalog_records.append(catalog_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_manifest_record_count": len(routing_manifest),
    "routing_catalog_record_count": len(catalog_records),
    "deterministic_ordering": True,
    LIST_KEY: catalog_records
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Catalog (v8.4)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-manifest record count: {len(routing_manifest)}
- Routing-catalog record count: {len(catalog_records)}
- Deterministic ordering: True

## Routing Catalog Records

{to_md_table(catalog_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
