
# v64.102 closure-release-final-prep-prep-record generator
# Pure downstream projection from closure-release-final-prep-handoff-package
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json, .md

import json
from pathlib import Path

HANDOFF_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json")
PREP_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json")
PREP_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-record-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def main():
    with HANDOFF_PATH.open("r", encoding="utf-8") as f:
        handoff_records = json.load(f)

    # Deterministic ordering by upstream id
    handoff_records = sorted(handoff_records, key=lambda r: r["id"])

    prep_records = []
    for idx, rec in enumerate(handoff_records):
        new_id = deterministic_id(idx)
        prep_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        prep_records.append(prep_record)

    # Write JSON
    with PREP_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(prep_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with PREP_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-prep-record\n\n")
        for rec in prep_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
