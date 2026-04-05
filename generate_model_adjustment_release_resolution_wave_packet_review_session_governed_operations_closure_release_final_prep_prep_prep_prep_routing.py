"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.py

v64.147 closure-release-final-prep-prep-prep-prep-routing generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.md
- Pure downstream projection: one routing record per locator record, exact-once, deterministic, no new logic
- Deterministic ID: resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-routing-0001, 0002, ...
- Deterministic ordering and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_locator.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_routing.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

ROUTING_FAMILY = "closure-release-final-prep-prep-prep-prep-routing"
LOCATOR_FAMILY = "closure-release-final-prep-prep-prep-prep-locator"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-routing-"

def make_id(idx: int) -> str:
    return f"{ID_PREFIX}{idx:04d}"

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        locator_records = json.load(f)

    routing_records = []
    for idx, locator in enumerate(sorted(locator_records, key=lambda r: r["id"])):
        routing_id = make_id(idx + 1)
        routing_record = {
            "id": routing_id,
            "family": ROUTING_FAMILY,
            "parent_id": locator["id"],
            "parent_family": LOCATOR_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": locator.get("trace", []),
            "data": locator.get("data", {}),
        }
        routing_records.append(routing_record)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(routing_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {ROUTING_FAMILY} (v64.147)\n\n")
        for rec in routing_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
