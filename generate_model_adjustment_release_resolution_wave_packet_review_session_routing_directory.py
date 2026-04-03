import json
from pathlib import Path

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_index.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_directory.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_directory.md"

FROZEN_TIMESTAMP = "2026-04-03T00:00:00+00:00"
VERSION = "v8.0-slice-1"
LIST_KEY = "release_resolution_wave_packet_review_session_routing_directory"

# Load input
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    routing_index = json.load(f)["release_resolution_wave_packet_review_session_routing_index"]

# Build routing-directory records
directory_records = []
for i, index_record in enumerate(routing_index, 1):
    directory_id = f"resolution-wave-packet-review-session-routing-directory-{i:04d}"
    directory_record = {
        "resolution_wave_packet_review_session_routing_directory_id": directory_id,
        "source_resolution_wave_packet_review_session_routing_index_id": index_record["resolution_wave_packet_review_session_routing_index_id"],
        # Pure downstream projection: copy all source_* fields from index_record
        **{k: v for k, v in index_record.items() if k.startswith("source_")}
    }
    directory_records.append(directory_record)

# Compose output JSON
data = {
    "model_adjustment_release_resolution_wave_packet_review_session_routing_directory_version": VERSION,
    "generated_at_utc": FROZEN_TIMESTAMP,
    "input_routing_index_record_count": len(routing_index),
    "routing_directory_record_count": len(directory_records),
    "deterministic_ordering": True,
    LIST_KEY: directory_records
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

md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Routing Directory (v8.0)

- Version: {VERSION}
- generated_at_utc: {FROZEN_TIMESTAMP}
- Input routing-index record count: {len(routing_index)}
- Routing-directory record count: {len(directory_records)}
- Deterministic ordering: True

## Routing Directory Records

{to_md_table(directory_records)}
"""

with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md)
