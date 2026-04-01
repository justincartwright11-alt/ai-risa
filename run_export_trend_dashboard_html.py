import os
import sys
import json
import pandas as pd
from datetime import datetime

# --- CONFIG ---
LEDGER_HEALTH_PATH = r'C:/Users/jusin/ai_risa_data/ledger/ledger_health_snapshot.json'
RECON_CSV_PATH = r'C:/Users/jusin/ai_risa_data/exports/reconciliation_export.csv'
TREND_CSV_PATH = r'C:/Users/jusin/ai_risa_data/reports/reconciliation_trend_report.csv'
CALIB_PATCH_PATH = r'C:/Users/jusin/ai_risa_data/learning/calibration_patch_v1.json'
REPORTS_DIR = r'C:/Users/jusin/ai_risa_data/reports'
LATEST_HTML = os.path.join(REPORTS_DIR, 'trend_dashboard_latest.html')

# --- UTILS ---
def file_exists(path):
    exists = os.path.exists(path)
    print(f"[CHECK] {path}: {'FOUND' if exists else 'MISSING'}")
    return exists

def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)

# --- CHECK INPUTS ---
missing = False
for src in [LEDGER_HEALTH_PATH, RECON_CSV_PATH, TREND_CSV_PATH, CALIB_PATCH_PATH]:
    if not file_exists(src):
        missing = True
if missing:
    fail("One or more required source files are missing.")

# --- LOAD DATA ---
with open(LEDGER_HEALTH_PATH, 'r', encoding='utf-8') as f:
    ledger_health = json.load(f)
recon_df = pd.read_csv(RECON_CSV_PATH)
trend_df = pd.read_csv(TREND_CSV_PATH)
with open(CALIB_PATCH_PATH, 'r', encoding='utf-8') as f:
    calib_patch = json.load(f)

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
date_str = datetime.now().strftime('%Y-%m-%d')
dated_dir = os.path.join(REPORTS_DIR, date_str)
dated_html = os.path.join(dated_dir, f'trend_dashboard_{date_str}.html')
os.makedirs(dated_dir, exist_ok=True)

# --- HTML HELPERS ---
def html_table(df, title=None):
    if df.empty:
        return f'<h3>{title}</h3><p><em>No data available.</em></p>' if title else '<p><em>No data available.</em></p>'
    return (f'<h3>{title}</h3>' if title else '') + df.to_html(index=False, border=1, classes='dataframe', escape=False)

def html_section(title, content):
    return f'<section><h2>{title}</h2>{content}</section>'

# --- BUILD HTML ---
html = f"""
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>AI-RISA Trend Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2em; background: #f9f9f9; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .dataframe {{ border-collapse: collapse; width: 100%; margin-bottom: 2em; }}
        .dataframe th, .dataframe td {{ border: 1px solid #bbb; padding: 6px 10px; }}
        .dataframe th {{ background: #e3eaf2; }}
        section {{ margin-bottom: 2em; padding: 1em; background: #fff; border-radius: 8px; box-shadow: 0 1px 4px #ccc; }}
        .timestamp {{ color: #888; font-size: 0.95em; margin-bottom: 1em; }}
    </style>
</head>
<body>
    <h1>AI-RISA Trend Dashboard</h1>
    <div class='timestamp'>Generated: {timestamp}</div>
"""

# Ledger Health Summary
ledger_health_table = pd.DataFrame([ledger_health]) if isinstance(ledger_health, dict) else pd.DataFrame(ledger_health)
html += html_section('Ledger Health Summary', html_table(ledger_health_table))

# Rolling Winner/Method Accuracy Summary
if 'rolling_accuracy' in trend_df.columns:
    rolling_acc = trend_df[['rolling_accuracy']].drop_duplicates()
    html += html_section('Rolling Winner/Method Accuracy', html_table(rolling_acc))
else:
    html += html_section('Rolling Winner/Method Accuracy', '<p><em>Not available in trend report.</em></p>')

# Round Error Summary
round_err_cols = [c for c in trend_df.columns if 'round_error' in c]
if round_err_cols:
    round_err = trend_df[round_err_cols].drop_duplicates()
    html += html_section('Round Error Summary', html_table(round_err))
else:
    html += html_section('Round Error Summary', '<p><em>Not available in trend report.</em></p>')

# Model/Calibration Version Breakdowns
ver_cols = [c for c in trend_df.columns if 'version' in c]
if ver_cols:
    ver_df = trend_df[ver_cols].drop_duplicates()
    html += html_section('Model/Calibration Version Breakdowns', html_table(ver_df))
else:
    html += html_section('Model/Calibration Version Breakdowns', '<p><em>Not available in trend report.</em></p>')

# Underperforming Families Table
under_cols = [c for c in trend_df.columns if 'underperform' in c]
if under_cols:
    under_df = trend_df[under_cols].drop_duplicates()
    html += html_section('Underperforming Families', html_table(under_df))
else:
    html += html_section('Underperforming Families', '<p><em>Not available in trend report.</em></p>')

# Improving Families Table
improv_cols = [c for c in trend_df.columns if 'improv' in c]
if improv_cols:
    improv_df = trend_df[improv_cols].drop_duplicates()
    html += html_section('Improving Families', html_table(improv_df))
else:
    html += html_section('Improving Families', '<p><em>Not available in trend report.</em></p>')

# Calibration Patch Recommended Actions
if isinstance(calib_patch, dict) and 'recommended_actions' in calib_patch:
    patch_df = pd.DataFrame(calib_patch['recommended_actions'])
    html += html_section('Calibration Patch Recommended Actions', html_table(patch_df))
else:
    html += html_section('Calibration Patch Recommended Actions', '<p><em>No recommended actions found.</em></p>')

html += """
</body>
</html>
"""

# --- WRITE OUTPUTS ---
with open(LATEST_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
with open(dated_html, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] HTML report written to: {LATEST_HTML}")
print(f"[OK] HTML report written to: {dated_html}")
print("[SUCCESS] Trend dashboard HTML export complete.")
