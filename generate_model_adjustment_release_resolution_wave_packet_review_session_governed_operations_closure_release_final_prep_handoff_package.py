# v64.83 closure-release-final-prep-handoff-package generator
# Pure downstream projection from v64.82 package
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json, .md

import json
import hashlib
from datetime import datetime

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.md"

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # locked for determinism

# Deterministic ID generator (SHA256 of upstream id + suffix)
def make_id(upstream_id):
    return hashlib.sha256((upstream_id + "|handoff").encode("utf-8")).hexdigest()

def main():

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        upstream = json.load(f)

    records = []
    for rec in upstream:
        new_id = make_id(rec["id"])
        out = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
            "handoff_status": "pending"
        }
        records.append(out)

    # Deterministic ordering by id
    records.sort(key=lambda r: r["id"])

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# v64.83 Closure Release Final Prep Handoff Package\n\n")
        f.write(f"Generated at: {FROZEN_GENERATED_AT_UTC}\n\n")
        for rec in records:
            f.write(f"## Record: {rec['id']}\n")
            f.write(f"- Upstream ID: {rec['upstream_id']}\n")
            f.write(f"- Handoff Status: {rec['handoff_status']}\n")
            f.write(f"- Trace: {json.dumps(rec['trace'])}\n")
            f.write(f"- Data: {json.dumps(rec['data'])}\n\n")

if __name__ == "__main__":
    main()
