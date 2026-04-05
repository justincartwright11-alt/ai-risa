# v64.153-controlled-release-resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-attestation
# Generator for controlled attestation projection from receipt

import json
import hashlib
from pathlib import Path

PARENT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_receipt.json"
CHILD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_attestation.json"
CHILD_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_attestation.md"

PASS_THROUGH_FIELDS = [
    "receipt_id", "source_handoff_id", "handoff_id", "source_register_id", "register_id", "map_id", "record_type", "status", "name", "title", "slug"
]

REQUIRED_FIELDS = [
    "attestation_id", "attestation_position", "source_receipt_id", "source_receipt_position", "source_receipt_artifact", "attestation_locator_key"
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    parent = json.load(open(PARENT_PATH, "r", encoding="utf-8"))
    parent_records = parent["records"]
    out = {
        "parent_artifact": PARENT_PATH,
        "record_count": len(parent_records),
        "records": []
    }
    seen_receipt_ids = set()
    for i, rec in enumerate(parent_records):
        if "receipt_id" not in rec:
            raise Exception(f"No usable source_receipt_id in parent record {i+1}")
        if rec["receipt_id"] in seen_receipt_ids:
            raise Exception(f"Duplicate source_receipt_id: {rec['receipt_id']}")
        seen_receipt_ids.add(rec["receipt_id"])
        attestation = {
            "attestation_id": f"closure-release-final-prep-prep-prep-prep-attestation-{i+1:04d}",
            "attestation_position": i+1,
            "source_receipt_id": rec["receipt_id"],
            "source_receipt_position": rec["receipt_position"],
            "source_receipt_artifact": PARENT_PATH,
            "attestation_locator_key": rec.get("receipt_locator_key", f"closure-release-final-prep-prep-prep-prep-attestation-{i+1:04d}")
        }
        # Pass through allowed fields if present
        for field in PASS_THROUGH_FIELDS:
            if field in rec:
                attestation[field] = rec[field]
        out["records"].append(attestation)
    out["record_count"] = len(out["records"])
    with open(CHILD_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    # Write Markdown summary
    with open(CHILD_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# closure-release-final-prep-prep-prep-prep-attestation\n\n")
        f.write(f"* parent_artifact: {PARENT_PATH}\n")
        f.write(f"* record_count: {out['record_count']}\n\n")
        f.write("| attestation_id | attestation_position | source_receipt_id | attestation_locator_key |\n")
        f.write("| -------------- | -------------------: | ----------------- | ----------------------- |\n")
        for r in out["records"]:
            f.write(f"| {r['attestation_id']} | {r['attestation_position']} | {r['source_receipt_id']} | {r['attestation_locator_key']} |\n")
    print("Generation complete.")

if __name__ == "__main__":
    main()
