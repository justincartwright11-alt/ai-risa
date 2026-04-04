import json
from pathlib import Path

# Locked input/output paths
INPUT_PATH = Path(r"ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_manifest.json")
OUTPUT_JSON_PATH = Path(r"ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_directory.json")
OUTPUT_MD_PATH = Path(r"ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_directory.md")

ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-directory-"

# Use the frozen generated_at_utc from the input
with INPUT_PATH.open("r", encoding="utf-8") as f:
    input_records = json.load(f)

# Deterministic ordering by input id
input_records_sorted = sorted(input_records, key=lambda r: r["id"])

directory_records = []
for idx, record in enumerate(input_records_sorted, 1):
    directory_id = f"{ID_PREFIX}{idx:04d}"
    directory_record = {
        "id": directory_id,
        "upstream_id": record["id"],
        "generated_at_utc": record["generated_at_utc"],
        "trace": record.get("trace", {}),
        "data": record.get("data", {})
    }
    directory_records.append(directory_record)

# Write JSON output (deterministic, pretty)
with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
    json.dump(directory_records, f, indent=2, ensure_ascii=False)
    f.write("\n")

# Write Markdown output as a faithful projection of JSON
with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
    f.write("# closure-release-final-prep-prep-directory\n\n")
    for rec in directory_records:
        f.write(f"- id: {rec['id']}\n")
        f.write(f"  upstream_id: {rec['upstream_id']}\n")
        f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
        f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
        f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")
