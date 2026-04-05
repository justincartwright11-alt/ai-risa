# v64.107 closure-release-final-prep-prep-index generator
# Pure downstream projection from closure-release-final-prep-prep-catalog
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_catalog.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_index.json, .md

import json
from pathlib import Path

CATALOG_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_catalog.json")
INDEX_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_index.json")
INDEX_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_index.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"
ID_PREFIX = "resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-index-"

def deterministic_id(idx):
    return f"{ID_PREFIX}{idx+1:04d}"

def main():
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        catalog_records = json.load(f)

    # Deterministic ordering by upstream id
    catalog_records = sorted(catalog_records, key=lambda r: r["id"])

    index_records = []
    for idx, rec in enumerate(catalog_records):
        new_id = deterministic_id(idx)
        index_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        index_records.append(index_record)

    # Write JSON
    with INDEX_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(index_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with INDEX_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-prep-index\n\n")
        for rec in index_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
