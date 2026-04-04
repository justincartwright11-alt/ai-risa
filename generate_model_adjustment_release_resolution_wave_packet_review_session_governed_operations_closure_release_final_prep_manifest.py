# v64.90 closure-release-final-prep-manifest generator
# Pure downstream projection from v64.89 index
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_index.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_manifest.json, .md

import json
from pathlib import Path

INPUT_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_index.json")
OUTPUT_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_manifest.json")
OUTPUT_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_manifest.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # locked for determinism
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-manifest-"

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
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": record.get("trace", {}),
            "data": record.get("data", {}),
            "handoff_status": record.get("handoff_status", "pending")
        })

    # Write JSON
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown
    with OUTPUT_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# v64.90 Closure Release Final Prep Manifest\n\n")
        f.write(f"Generated at: {FROZEN_GENERATED_AT_UTC}\n\n")
        for rec in out:
            f.write(f"## Record: {rec['id']}\n")
            f.write(f"- Upstream ID: {rec['upstream_id']}\n")
            f.write(f"- Handoff Status: {rec['handoff_status']}\n")
            f.write(f"- Trace: {json.dumps(rec['trace'])}\n")
            f.write(f"- Data: {json.dumps(rec['data'])}\n\n")

if __name__ == "__main__":
    main()
