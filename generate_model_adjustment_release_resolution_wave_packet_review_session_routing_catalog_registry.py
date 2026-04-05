import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_ledger.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_registry.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_registry.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.6-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_catalog_registry"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_catalog_ledger = json.load(f)["release_resolution_wave_packet_review_session_routing_catalog_ledger"]

# Build routing-catalog-registry records
registry_records = []
for i, ledger_record in enumerate(routing_catalog_ledger, 1):
    registry_id = f"resolution-wave-packet-review-session-routing-catalog-registry-{i:04d}"
    registry_record = {
        "resolution_wave_packet_review_session_routing_catalog_registry_id": registry_id,
        "source_resolution_wave_packet_review_session_routing_catalog_ledger_id": ledger_record["resolution_wave_packet_review_session_routing_catalog_ledger_id"],
        # Pure downstream projection: copy all source_* fields from ledger_record
        **{k: v for k, v in ledger_record.items() if k.startswith("source_")}
    }
    registry_records.append(registry_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_registry_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_catalog_ledger_record_count": len(routing_catalog_ledger),
    "routing_catalog_registry_record_count": len(registry_records),
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Catalog Registry (v8.6)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-catalog-ledger record count: {len(routing_catalog_ledger)}
- Routing-catalog-registry record count: {len(registry_records)}
- Deterministic ordering: True

## Routing Catalog Registry Records

{to_md_table(registry_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
