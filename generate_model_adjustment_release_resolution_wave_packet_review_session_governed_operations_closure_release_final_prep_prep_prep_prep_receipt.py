# v64.152-controlled-release-resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-receipt
# Generator for controlled receipt projection from handoff

import json
import hashlib
from pathlib import Path

PARENT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_handoff.json"
CHILD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_receipt.json"
CHILD_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_receipt.md"

REQUIRED_FIELDS = [
    "handoff_id", "source_register_id", "register_id", "map_id", "record_type", "status", "name", "title", "slug"
]

RECEIPT_FIELDS = [
    "receipt_id", "receipt_position", "source_handoff_id", "source_handoff_position", "source_handoff_artifact", "receipt_locator_key"
]

PASS_THROUGH_FIELDS = [
    "handoff_id", "source_register_id", "register_id", "map_id", "record_type", "status", "name", "title", "slug"
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
    seen_handoff_ids = set()
    for i, rec in enumerate(parent_records):
        if "handoff_id" not in rec:
            raise Exception(f"No usable source_handoff_id in parent record {i+1}")
        if rec["handoff_id"] in seen_handoff_ids:
            raise Exception(f"Duplicate source_handoff_id: {rec['handoff_id']}")
        seen_handoff_ids.add(rec["handoff_id"])
        receipt = {
            "receipt_id": f"closure-release-final-prep-prep-prep-prep-receipt-{i+1:04d}",
            "receipt_position": i+1,
            "source_handoff_id": rec["handoff_id"],
            "source_handoff_position": rec["handoff_position"],
            "source_handoff_artifact": PARENT_PATH,
            "receipt_locator_key": rec.get("handoff_locator_key", f"closure-release-final-prep-prep-prep-prep-handoff-{i+1:04d}")
        }
        # Pass through allowed fields if present
        for field in PASS_THROUGH_FIELDS:
            if field in rec:
                receipt[field] = rec[field]
        out["records"].append(receipt)
    out["record_count"] = len(out["records"])
    with open(CHILD_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    # Write Markdown summary
    with open(CHILD_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Receipt Projection\n\n")
        f.write(f"Parent: {PARENT_PATH}\n\n")
        f.write(f"Records: {out['record_count']}\n\n")
        for r in out["records"]:
            f.write(f"- {r['receipt_id']} (from {r['source_handoff_id']})\n")
    print("Generation complete.")

if __name__ == "__main__":
    main()
