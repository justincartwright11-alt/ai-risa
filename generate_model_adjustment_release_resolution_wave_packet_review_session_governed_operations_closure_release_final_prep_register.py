
# v64.95 closure-release-final-prep-register generator
# Pure downstream projection from closure-release-final-prep-map
# Reads: C:/ai_risa_data/ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_map.json
# Writes: C:/ai_risa_data/ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_register.json, .md


import json
from pathlib import Path

INPUT_PATH = Path("C:/ai_risa_data/ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_map.json")
OUTPUT_JSON_PATH = Path("C:/ai_risa_data/ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_register.json")
OUTPUT_MD_PATH = Path("C:/ai_risa_data/ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_register.md")

LOCKED_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-register-"
ID_WIDTH = 4

def deterministic_id(idx):
    return f"{ID_PREFIX}{str(idx+1).zfill(ID_WIDTH)}"


def main():
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        upstream = json.load(f)

    # Deterministic ordering by upstream id
    upstream_sorted = sorted(upstream, key=lambda r: r["id"])
    out = []
    for idx, record in enumerate(upstream_sorted):
        new_id = deterministic_id(idx)
        out.append({
            "id": new_id,
            "upstream_id": record["id"],
            "generated_at_utc": LOCKED_GENERATED_AT_UTC,
            "trace": record.get("trace", {}),
            "data": record.get("data", {}),
            "handoff_status": record.get("handoff_status", "pending")
        })

    # Write JSON
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown as a faithful projection of JSON
    with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-register\n\n")
        for record in out:
            f.write(f"- id: {record['id']}\n")
            f.write(f"  upstream_id: {record['upstream_id']}\n")
            f.write(f"  generated_at_utc: {record['generated_at_utc']}\n")
            f.write(f"  handoff_status: {record['handoff_status']}\n")
            f.write(f"  trace: {json.dumps(record['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(record['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
