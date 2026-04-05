
# v64.105 closure-release-final-prep-prep-resolution generator
# Pure downstream projection from closure-release-final-prep-prep-state
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_state.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_resolution.json, .md

import json
from pathlib import Path

STATE_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_state.json")
RESOLUTION_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_resolution.json")
RESOLUTION_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_resolution.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-resolution-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def main():
    with STATE_PATH.open("r", encoding="utf-8") as f:
        state_records = json.load(f)

    # Deterministic ordering by upstream id
    state_records = sorted(state_records, key=lambda r: r["id"])

    resolution_records = []
    for idx, rec in enumerate(state_records):
        new_id = deterministic_id(idx)
        resolution_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        resolution_records.append(resolution_record)

    # Write JSON
    with RESOLUTION_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(resolution_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with RESOLUTION_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-prep-resolution\n\n")
        for rec in resolution_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
