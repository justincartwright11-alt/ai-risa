import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_ledger.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_ledger.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.5-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_catalog_ledger"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_catalog = json.load(f)["release_resolution_wave_packet_review_session_routing_catalog"]

# Build routing-catalog-ledger records
ledger_records = []
for i, catalog_record in enumerate(routing_catalog, 1):
    ledger_id = f"resolution-wave-packet-review-session-routing-catalog-ledger-{i:04d}"
    ledger_record = {
        "resolution_wave_packet_review_session_routing_catalog_ledger_id": ledger_id,
        "source_resolution_wave_packet_review_session_routing_catalog_id": catalog_record["resolution_wave_packet_review_session_routing_catalog_id"],
        # Pure downstream projection: copy all source_* fields from catalog_record
        **{k: v for k, v in catalog_record.items() if k.startswith("source_")}
    }
    ledger_records.append(ledger_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_ledger_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_catalog_record_count": len(routing_catalog),
    "routing_catalog_ledger_record_count": len(ledger_records),
    "deterministic_ordering": True,
    LIST_KEY: ledger_records
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Catalog Ledger (v8.5)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-catalog record count: {len(routing_catalog)}
- Routing-catalog-ledger record count: {len(ledger_records)}
- Deterministic ordering: True

## Routing Catalog Ledger Records

{to_md_table(ledger_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
