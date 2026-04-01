#!/usr/bin/env python3
"""
AI-RISA Model Feedback Queue Generator
=====================================
Turns reconciliation and trend outputs into a ranked review queue for model feedback and improvement.
"""
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- INPUTS ---
RECONCILIATION_LEDGER = Path(r'C:/Users/jusin/ai_risa_data/ledger/reconciliation_ledger.jsonl')
TREND_REPORT = Path(r'C:/Users/jusin/ai_risa_data/reports/reconciliation_trend_report.csv')
CALIB_PATCH = Path(r'C:/Users/jusin/ai_risa_data/learning/calibration_patch_v1.json')

# --- OUTPUTS ---
QUEUE_CSV = Path(r'C:/Users/jusin/ai_risa_data/reports/model_feedback_queue.csv')
QUEUE_JSON = Path(r'C:/Users/jusin/ai_risa_data/reports/model_feedback_queue.json')

# --- LOAD DATA ---
def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def file_exists(path):
    exists = Path(path).exists()
    print(f"[CHECK] {path}: {'FOUND' if exists else 'MISSING'}")
    return exists

missing = False
for src in [RECONCILIATION_LEDGER, TREND_REPORT, CALIB_PATCH]:
    if not file_exists(src):
        missing = True
if missing:
    print("[FAIL] One or more required source files are missing.")
    exit(1)

recon_ledger = load_jsonl(RECONCILIATION_LEDGER)
trend_df = pd.read_csv(TREND_REPORT)
with open(CALIB_PATCH, 'r', encoding='utf-8') as f:
    calib_patch = json.load(f)

# --- BUILD QUEUE ---
queue = []

# 1. Underperforming prediction families
if 'underperforming_family_id' in trend_df.columns:
    underperf = trend_df[['underperforming_family_id', 'underperforming_family_accuracy']].dropna()
    for _, row in underperf.iterrows():
        queue.append({
            'priority': 1,
            'type': 'underperforming_family',
            'family_id': row['underperforming_family_id'],
            'accuracy': row['underperforming_family_accuracy'],
            'reason': 'Underperforming prediction family'
        })

# 2. Winner-calibration drift
if 'winner_calibration_drift' in trend_df.columns:
    drift = trend_df[['winner_calibration_drift']].dropna()
    for _, row in drift.iterrows():
        queue.append({
            'priority': 2,
            'type': 'winner_calibration_drift',
            'drift': row['winner_calibration_drift'],
            'reason': 'Winner calibration drift detected'
        })

# 3. Method drift
if 'method_drift' in trend_df.columns:
    drift = trend_df[['method_drift']].dropna()
    for _, row in drift.iterrows():
        queue.append({
            'priority': 3,
            'type': 'method_drift',
            'drift': row['method_drift'],
            'reason': 'Method drift detected'
        })

# 4. Round projection drift
if 'round_projection_drift' in trend_df.columns:
    drift = trend_df[['round_projection_drift']].dropna()
    for _, row in drift.iterrows():
        queue.append({
            'priority': 4,
            'type': 'round_projection_drift',
            'drift': row['round_projection_drift'],
            'reason': 'Round projection drift detected'
        })

# 5. Model/calibration version regressions
if 'version_regression' in trend_df.columns:
    regress = trend_df[['version_regression']].dropna()
    for _, row in regress.iterrows():
        queue.append({
            'priority': 5,
            'type': 'version_regression',
            'regression': row['version_regression'],
            'reason': 'Model/calibration version regression'
        })

# 6. Calibration patch recommended actions
if isinstance(calib_patch, dict) and 'recommended_actions' in calib_patch:
    for action in calib_patch['recommended_actions']:
        queue.append({
            'priority': 6,
            'type': 'calibration_patch_action',
            'action': action,
            'reason': 'Calibration patch recommended action'
        })

# --- SORT QUEUE ---
queue = sorted(queue, key=lambda x: x['priority'])

# --- WRITE OUTPUTS ---
pd.DataFrame(queue).to_csv(QUEUE_CSV, index=False)
with open(QUEUE_JSON, 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2)

# --- PRINT SUMMARY ---
print(f"[OK] Model feedback queue written to: {QUEUE_CSV}")
print(f"[OK] Model feedback queue written to: {QUEUE_JSON}")
print("\nTop review targets:")
for item in queue[:10]:
    print(f"- {item['type']}: {item.get('family_id', item.get('drift', item.get('action', item.get('regression', ''))))} ({item['reason']})")
if not queue:
    print("No high-priority review targets found.")
