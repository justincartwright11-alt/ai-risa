"""
generate_model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_ledger.py

v64.139 closure-release-final-prep-prep-prep-prep-ledger generator

- Reads: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_record.json
- Writes: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_ledger.json
          ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_ledger.md
- Pure downstream projection: one ledger record per record, exact-once, deterministic, no new logic
- Deterministic ID, ordering, and traceability
- Markdown is a pure projection of JSON
- No new policy/approval/prioritization/execution-outcome logic
- Use explicit locked interpreter for all runs
"""
import json
import hashlib
from datetime import datetime

INPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_record.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_ledger.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_ledger.md"

FROZEN_GENERATED_AT_UTC = "2026-04-05T00:00:00Z"

LEDGER_FAMILY = "closure-release-final-prep-prep-prep-prep-ledger"
RECORD_FAMILY = "closure-release-final-prep-prep-prep-prep-record"


def deterministic_id(parent_id: str) -> str:
    # Deterministic, unique, traceable
    return hashlib.sha256((parent_id + LEDGER_FAMILY).encode("utf-8")).hexdigest()

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)

    ledger_records = []
    for rec in records:
        ledger_id = deterministic_id(rec["id"])
        ledger_record = {
            "id": ledger_id,
            "family": LEDGER_FAMILY,
            "parent_id": rec["id"],
            "parent_family": RECORD_FAMILY,
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", []),
            "data": rec.get("data", {}),
        }
        ledger_records.append(ledger_record)

    # Deterministic ordering by id
    ledger_records.sort(key=lambda r: r["id"])

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(ledger_records, f, indent=2, ensure_ascii=False)

    # Markdown projection
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# {LEDGER_FAMILY} (v64.139)\n\n")
        for rec in ledger_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  parent_id: {rec['parent_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
