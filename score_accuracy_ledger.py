# score_accuracy_ledger.py
"""
Scores the AI-RISA accuracy ledger and generates a summary report.
"""
import os
import json
from collections import Counter, defaultdict
from datetime import datetime

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.json")
SCORECARD_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_scorecard.json")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_summary.md")

# Helper: classify method

def classify_method(method):
    m = (method or "").lower()
    if "decision" in m:
        return "decision"
    if any(x in m for x in ["ko", "tko", "stoppage"]):
        return "stoppage"
    return "other"

def load_ledger():
    with open(LEDGER_PATH, encoding="utf-8") as f:
        return json.load(f)

def score_ledger(rows):
    scored = {
        "total": 0,
        "scored": 0,
        "winner_hits": 0,
        "method_hits": 0,
        "round_hits": 0,
        "decision_total": 0,
        "decision_hits": 0,
        "stoppage_total": 0,
        "stoppage_hits": 0,
        "confidence_buckets": Counter(),
        "confidence_bucket_hits": Counter(),
        "by_event_date": defaultdict(lambda: {"total": 0, "winner_hits": 0}),
        "miss_patterns": Counter(),
    }
    for row in rows:
        scored["total"] += 1
        if row.get("actual_winner", "UNKNOWN") == "UNKNOWN":
            continue
        scored["scored"] += 1
        if row.get("hit_winner"):
            scored["winner_hits"] += 1
        if row.get("hit_method"):
            scored["method_hits"] += 1
        if row.get("round_error") == 0:
            scored["round_hits"] += 1
        method_type = classify_method(row.get("actual_method"))
        if method_type == "decision":
            scored["decision_total"] += 1
            if row.get("hit_method"):
                scored["decision_hits"] += 1
        elif method_type == "stoppage":
            scored["stoppage_total"] += 1
            if row.get("hit_method"):
                scored["stoppage_hits"] += 1
        bucket = row.get("confidence_bucket", "UNKNOWN")
        scored["confidence_buckets"][bucket] += 1
        if row.get("hit_winner"):
            scored["confidence_bucket_hits"][bucket] += 1
        # Rolling by event date
        date = row.get("event_date", "UNKNOWN")
        scored["by_event_date"][date]["total"] += 1
        if row.get("hit_winner"):
            scored["by_event_date"][date]["winner_hits"] += 1
        # Miss patterns
        if not row.get("hit_winner"):
            miss = f"PRED:{row.get('predicted_winner')} ACT:{row.get('actual_winner')}"
            scored["miss_patterns"][miss] += 1
    return scored

def write_scorecard(scored):
    with open(SCORECARD_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

def write_summary(scored):
    lines = []
    lines.append(f"# AI-RISA Accuracy Summary\n")
    lines.append(f"**Total predictions:** {scored['total']}")
    lines.append(f"**Fights with actual results:** {scored['scored']}")
    lines.append(f"**Winner hit rate:** {pct(scored['winner_hits'], scored['scored'])}")
    lines.append(f"**Method hit rate:** {pct(scored['method_hits'], scored['scored'])}")
    lines.append(f"**Exact round hit rate:** {pct(scored['round_hits'], scored['scored'])}")
    lines.append(f"**Decision accuracy:** {pct(scored['decision_hits'], scored['decision_total'])} ({scored['decision_hits']}/{scored['decision_total']})")
    lines.append(f"**Stoppage accuracy:** {pct(scored['stoppage_hits'], scored['stoppage_total'])} ({scored['stoppage_hits']}/{scored['stoppage_total']})")
    lines.append(f"\n## Confidence bucket breakdown:")
    for bucket in sorted(scored['confidence_buckets']):
        total = scored['confidence_buckets'][bucket]
        hits = scored['confidence_bucket_hits'].get(bucket, 0)
        lines.append(f"- {bucket}: {pct(hits, total)} ({hits}/{total})")
    lines.append(f"\n## Rolling winner accuracy by event date:")
    for date in sorted(scored['by_event_date']):
        d = scored['by_event_date'][date]
        lines.append(f"- {date}: {pct(d['winner_hits'], d['total'])} ({d['winner_hits']}/{d['total']})")
    lines.append(f"\n## Biggest miss patterns:")
    for miss, count in scored['miss_patterns'].most_common(5):
        lines.append(f"- {miss}: {count}")
    lines.append(f"\n## First calibration recommendation:")
    if scored['miss_patterns']:
        lines.append(f"- Focus on the most frequent miss pattern above.")
    else:
        lines.append(f"- No clear miss pattern detected.")
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def pct(n, d):
    if not d:
        return "0.0%"
    return f"{100.0 * n / d:.1f}%"

def main():
    ledger = load_ledger()
    scored = score_ledger(ledger)
    write_scorecard(scored)
    write_summary(scored)
    print(f"Wrote {SCORECARD_PATH} and {SUMMARY_PATH}")

if __name__ == "__main__":
    main()
