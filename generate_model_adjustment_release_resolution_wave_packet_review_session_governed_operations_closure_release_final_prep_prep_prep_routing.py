# v64.129 closure-release-final-prep-prep-prep-routing generator
# Pure downstream projection from closure-release-final-prep-prep-prep-locator
# Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_locator.json
# Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_routing.json, .md

import json

INPUT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_locator.json"
OUTPUT_JSON_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_routing.json"
OUTPUT_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_routing.md"

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"  # locked for determinism
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-routing-"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        upstream = json.load(f)

    out_records = []
    for idx, rec in enumerate(upstream):
        new_id = f"{ID_PREFIX}{idx+1:04d}"
        out = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", []),
            # Pure projection: copy all fields, no new logic
            "closure_release_final_prep_prep_prep_locator": rec,
        }
        out_records.append(out)

    # Deterministic ordering by new_id
    out_records.sort(key=lambda r: r["id"])

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# v64.129 closure-release-final-prep-prep-prep-routing\n\n")
        for r in out_records:
            f.write(f"## {r['id']}\n")
            f.write(f"- upstream_id: {r['upstream_id']}\n")
            f.write(f"- generated_at_utc: {r['generated_at_utc']}\n")
            f.write(f"- trace: {r['trace']}\n")
            f.write(f"\n")

if __name__ == "__main__":
    main()
