import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_locator.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_registry.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_registry.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.2-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_registry"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_locator = json.load(f)["release_resolution_wave_packet_review_session_routing_locator"]

# Build routing-registry records
registry_records = []
for i, locator_record in enumerate(routing_locator, 1):
    registry_id = f"resolution-wave-packet-review-session-routing-registry-{i:04d}"
    registry_record = {
        "resolution_wave_packet_review_session_routing_registry_id": registry_id,
        "source_resolution_wave_packet_review_session_routing_locator_id": locator_record["resolution_wave_packet_review_session_routing_locator_id"],
        # Pure downstream projection: copy all source_* fields from locator_record
        **{k: v for k, v in locator_record.items() if k.startswith("source_")}
    }
    registry_records.append(registry_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_registry_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_locator_record_count": len(routing_locator),
    "routing_registry_record_count": len(registry_records),
    "deterministic_ordering": True,
    LIST_KEY: registry_records
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Registry (v8.2)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-locator record count: {len(routing_locator)}
- Routing-registry record count: {len(registry_records)}
- Deterministic ordering: True

## Routing Registry Records

{to_md_table(registry_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
