
# v64.101 closure-release-final-prep-handoff-package generator
# Pure downstream projection from closure-release-final-prep-package
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json, .md

import json
from pathlib import Path

PACKAGE_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json")
HANDOFF_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.json")
HANDOFF_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_handoff_package.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-handoff-package-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def main():
    with PACKAGE_PATH.open("r", encoding="utf-8") as f:
        package_records = json.load(f)

    # Deterministic ordering by upstream id
    package_records = sorted(package_records, key=lambda r: r["id"])

    handoff_records = []
    for idx, rec in enumerate(package_records):
        new_id = deterministic_id(idx)
        handoff_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        handoff_records.append(handoff_record)

    # Write JSON
    with HANDOFF_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(handoff_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with HANDOFF_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-handoff-package\n\n")
        for rec in handoff_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
