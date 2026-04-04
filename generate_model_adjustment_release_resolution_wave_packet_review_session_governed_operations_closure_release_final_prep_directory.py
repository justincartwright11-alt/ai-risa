# v64.73 closure-release-final-prep-directory generator
# Pure downstream projection from closure-release-final-prep-manifest
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_manifest.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_directory.json, .md

import json
from pathlib import Path

INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_manifest.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_directory.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_directory.md")

LOCKED_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # update if spec changes
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-directory-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

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
            # Pure projection: copy all traceable fields
            "trace": record.get("trace", {}),
        })

    # Write JSON
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown
    with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# v64.73 closure-release-final-prep-directory\n\n")
        f.write(f"Generated at: {LOCKED_GENERATED_AT_UTC}\n\n")
        f.write("| id | upstream_id |\n")
        f.write("| --- | --- |\n")
        for rec in out:
            f.write(f"| {rec['id']} | {rec['upstream_id']} |\n")

if __name__ == "__main__":
    main()
