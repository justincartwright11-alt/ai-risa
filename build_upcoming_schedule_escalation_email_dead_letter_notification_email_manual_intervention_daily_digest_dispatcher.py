"""
v73.3-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-daily-digest-dispatcher
Deterministic daily digest dispatcher. Pure delivery slice.
"""

import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Paths ===
DIGEST_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_digest.json"
DISPATCH_JSON_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch.json"
DISPATCH_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch.md"

# === 2. Load Digest ===
def load_json(path: str) -> Any:
    if not Path(path).exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# === 3. Dispatch Record Builder ===
def build_dispatch_record(digest: Dict[str, Any], dispatch_target: str = "operator_email") -> Dict[str, Any]:
    today = date.today().isoformat()
    artifact_id = hashlib.sha256((digest['generated_at'] + dispatch_target).encode()).hexdigest()[:16]
    summary_totals = digest.get("totals_by_state", {})
    # Decide dispatch state and suppression
    if not summary_totals or sum(summary_totals.values()) == 0:
        dispatch_state = "suppressed"
        suppression_reason = "empty_digest"
    else:
        dispatch_state = "ready"
        suppression_reason = None
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "digest_dispatch_id": artifact_id,
        "digest_date": today,
        "dispatch_state": dispatch_state,
        "dispatch_target": dispatch_target,
        "digest_artifact_id": artifact_id,
        "summary_totals": summary_totals,
        "suppression_reason": suppression_reason,
        "created_at": now,
        "updated_at": now
    }

# === 4. Write Outputs ===
def write_json(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Manual-Intervention Daily Digest Dispatch\n\n")
        for r in records:
            f.write(f"- **Dispatch ID:** {r['digest_dispatch_id']}\n")
            f.write(f"  - Date: {r['digest_date']} | Target: {r['dispatch_target']}\n")
            f.write(f"  - State: {r['dispatch_state']} | Suppression: {r.get('suppression_reason')}\n")
            f.write(f"  - Totals: {r['summary_totals']}\n")
            f.write(f"  - Created: {r['created_at']} | Updated: {r['updated_at']}\n\n")

# === 5. Entrypoint ===
def main():
    digest = load_json(DIGEST_PATH)
    if not digest:
        records = []
    else:
        # For this slice, always one dispatch per digest per target
        records = [build_dispatch_record(digest)]
    write_json(DISPATCH_JSON_PATH, records)
    write_markdown(DISPATCH_MD_PATH, records)

if __name__ == "__main__":
    main()
