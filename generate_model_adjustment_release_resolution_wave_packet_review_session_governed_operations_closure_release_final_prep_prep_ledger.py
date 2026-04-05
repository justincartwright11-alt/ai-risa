
# v64.103 closure-release-final-prep-prep-ledger generator
# Pure downstream projection from closure-release-final-prep-prep-record
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.json, .md

import json
from pathlib import Path

PREP_RECORD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_record.json")
LEDGER_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.json")
LEDGER_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_ledger.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-ledger-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def main():
    with PREP_RECORD_PATH.open("r", encoding="utf-8") as f:
        prep_records = json.load(f)

    # Deterministic ordering by upstream id
    prep_records = sorted(prep_records, key=lambda r: r["id"])

    ledger_records = []
    for idx, rec in enumerate(prep_records):
        new_id = deterministic_id(idx)
        ledger_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        ledger_records.append(ledger_record)

    # Write JSON
    with LEDGER_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(ledger_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with LEDGER_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-prep-ledger\n\n")
        for rec in ledger_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
