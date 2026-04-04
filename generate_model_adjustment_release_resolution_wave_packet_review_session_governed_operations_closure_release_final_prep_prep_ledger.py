# v64.85 closure-release-final-prep-prep-ledger generator
# Pure downstream projection from v64.84 prep record
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.json, .md

import json
from datetime import datetime

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.md"

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # locked for determinism
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-ledger-"

# Deterministic ID: 0001, 0002, ...
def make_id(idx):
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        upstream = json.load(f)

    records = []
    for idx, rec in enumerate(upstream, 1):
        out = {
            "id": make_id(idx),
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
            "handoff_status": rec.get("handoff_status", "pending")
        }
        records.append(out)

    # Deterministic ordering by id
    records.sort(key=lambda r: r["id"])

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# v64.85 Closure Release Final Prep Prep Ledger\n\n")
        f.write(f"Generated at: {FROZEN_GENERATED_AT_UTC}\n\n")
        for rec in records:
            f.write(f"## Record: {rec['id']}\n")
            f.write(f"- Upstream ID: {rec['upstream_id']}\n")
            f.write(f"- Handoff Status: {rec['handoff_status']}\n")
            f.write(f"- Trace: {json.dumps(rec['trace'])}\n")
            f.write(f"- Data: {json.dumps(rec['data'])}\n\n")

if __name__ == "__main__":
    main()
