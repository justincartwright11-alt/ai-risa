import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_directory.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_locator.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_locator.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.1-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_locator"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_directory = json.load(f)["release_resolution_wave_packet_review_session_routing_directory"]

# Build routing-locator records
locator_records = []
for i, directory_record in enumerate(routing_directory, 1):
    locator_id = f"resolution-wave-packet-review-session-routing-locator-{i:04d}"
    locator_record = {
        "resolution_wave_packet_review_session_routing_locator_id": locator_id,
        "source_resolution_wave_packet_review_session_routing_directory_id": directory_record["resolution_wave_packet_review_session_routing_directory_id"],
        # Pure downstream projection: copy all source_* fields from directory_record
        **{k: v for k, v in directory_record.items() if k.startswith("source_")}
    }
    locator_records.append(locator_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_locator_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_directory_record_count": len(routing_directory),
    "routing_locator_record_count": len(locator_records),
    "deterministic_ordering": True,
    LIST_KEY: locator_records
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Locator (v8.1)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-directory record count: {len(routing_directory)}
- Routing-locator record count: {len(locator_records)}
- Deterministic ordering: True

## Routing Locator Records

{to_md_table(locator_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
