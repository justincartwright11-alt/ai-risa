# stoppage_bias_audit.py
"""
Audit stoppage misses in the accuracy ledger.
Outputs:
- false stoppages: predicted stoppage, actual decision
- missed stoppages: predicted decision, actual stoppage
- summary counts, affected fights, common feature patterns
"""
import os
import json
from collections import Counter

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "accuracy_ledger.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "ops", "accuracy", "stoppage_bias_audit_report.md")

with open(LEDGER_PATH, encoding="utf-8") as f:
    ledger = json.load(f)

false_stoppages = []
missed_stoppages = []
for row in ledger:
    if not row.get("resolved_result"):
        continue
    pred = row.get("predicted_method_normalized", "unknown")
    actual = row.get("actual_method_normalized", "unknown")
    if pred == "stoppage" and actual == "decision":
        false_stoppages.append(row)
    elif pred == "decision" and actual == "stoppage":
        missed_stoppages.append(row)

def summarize(rows):
    if not rows:
        return "None"
    lines = []
    for r in rows:
        lines.append(f"- {r['fight_id']} | winner: {r['predicted_winner']} vs {r['actual_winner']} | conf: {r.get('confidence','?')} | stop_prop: {r.get('stoppage_propensity','?')} | round_tend: {r.get('round_finish_tendency','?')}")
    return "\n".join(lines)

def feature_counter(rows, field):
    return Counter(r.get(field, "UNKNOWN") for r in rows)

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("# Stoppage Bias Audit Report\n\n")
    f.write(f"Total false stoppages: {len(false_stoppages)}\n")
    f.write(f"Total missed stoppages: {len(missed_stoppages)}\n\n")
    f.write("## False Stoppages (predicted stoppage, actual decision):\n")
    f.write(summarize(false_stoppages) + "\n\n")
    f.write("## Missed Stoppages (predicted decision, actual stoppage):\n")
    f.write(summarize(missed_stoppages) + "\n\n")
    f.write("## Common Feature Patterns:\n")
    f.write("False stoppages by confidence: " + str(feature_counter(false_stoppages, "confidence")) + "\n")
    f.write("Missed stoppages by confidence: " + str(feature_counter(missed_stoppages, "confidence")) + "\n")
    f.write("False stoppages by stoppage_propensity: " + str(feature_counter(false_stoppages, "stoppage_propensity")) + "\n")
    f.write("Missed stoppages by stoppage_propensity: " + str(feature_counter(missed_stoppages, "stoppage_propensity")) + "\n")
    f.write("False stoppages by round_finish_tendency: " + str(feature_counter(false_stoppages, "round_finish_tendency")) + "\n")
    f.write("Missed stoppages by round_finish_tendency: " + str(feature_counter(missed_stoppages, "round_finish_tendency")) + "\n")
    f.write("\nRecommended next step: Tune threshold for stoppage assignment based on these feature patterns.\n")
print(f"Wrote {REPORT_PATH}")
