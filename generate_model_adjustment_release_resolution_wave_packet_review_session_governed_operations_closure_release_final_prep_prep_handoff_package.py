# v64.119 closure-release-final-prep-prep-handoff-package generator
# Pure downstream projection from closure-release-final-prep-prep-package
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_package.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_handoff_package.json, .md

import json
import hashlib
from datetime import datetime

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_package.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_handoff_package.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_handoff_package.md"

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # locked for determinism


def deterministic_id(record, idx):
    # Deterministic ID: hash of upstream id + suffix
    upstream_id = record["id"]
    base = f"{upstream_id}|v64.119-handoff"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        upstream = json.load(f)

    out_records = []
    for idx, rec in enumerate(upstream):
        new_id = deterministic_id(rec, idx)
        out = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", []),
            # Pure projection: copy all fields, no new logic
            "closure_release_final_prep_prep_package": rec,
        }
        out_records.append(out)

    # Deterministic ordering by new_id
    out_records.sort(key=lambda r: r["id"])

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# v64.119 closure-release-final-prep-prep-handoff-package\n\n")
        for r in out_records:
            f.write(f"## {r['id']}\n")
            f.write(f"- upstream_id: {r['upstream_id']}\n")
            f.write(f"- generated_at_utc: {r['generated_at_utc']}\n")
            f.write(f"- trace: {r['trace']}\n")
            f.write(f"\n")

if __name__ == "__main__":
    main()
