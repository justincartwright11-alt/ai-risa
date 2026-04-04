# v64.57 closure-release-final-routing generator
# Pure downstream projection from closure-release-final-locator
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_locator.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_routing.json, .md

import json
import hashlib
from pathlib import Path
from datetime import datetime

INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_locator.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_routing.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_routing.md")

LOCKED_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # update if spec changes


def deterministic_id(record, idx):
    # Deterministic ID: hash of upstream id + index + family marker
    upstream_id = record["id"]
    base = f"routing|{upstream_id}|{idx}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def main():
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        upstream = json.load(f)

    # Deterministic ordering by upstream id
    upstream_sorted = sorted(upstream, key=lambda r: r["id"])
    out = []
    for idx, record in enumerate(upstream_sorted):
        new_id = deterministic_id(record, idx)
        out.append({
            "id": new_id,
            "upstream_id": record["id"],
            "generated_at_utc": LOCKED_GENERATED_AT_UTC,
            # Pure projection: copy all traceable fields
            "trace": record.get("trace", {}),
        })

    # Write JSON
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown
    with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# v64.57 closure-release-final-routing\n\n")
        f.write(f"Generated at: {LOCKED_GENERATED_AT_UTC}\n\n")
        f.write("| id | upstream_id |\n")
        f.write("| --- | --- |\n")
        for rec in out:
            f.write(f"| {rec['id']} | {rec['upstream_id']} |\n")

if __name__ == "__main__":
    main()
