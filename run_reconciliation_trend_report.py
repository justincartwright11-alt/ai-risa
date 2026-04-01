#!/usr/bin/env python3
"""
AI-RISA Reconciliation Trend Report
Produces rolling accuracy and error trends, version breakdowns, and family performance for model feedback.
"""
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Defaults
RECONCILIATION_CSV = Path(r'C:\Users\jusin\ai_risa_data\exports\reconciliation_export.csv')
OUTPUT_PATH = Path(r'C:\Users\jusin\ai_risa_data\reports\reconciliation_trend_report.csv')
ROLLING_WINDOW = 5  # days


def load_reconciliation(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Reconciliation CSV not found: {csv_path}")
    return pd.read_csv(csv_path)


def compute_trends(df, date_col='reconciliation_timestamp'):
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    # Rolling window by date
    df['date'] = df[date_col].dt.date
    daily = df.groupby('date').agg({
        'winner_correct': 'mean',
        'method_correct': 'mean',
        'round_error': 'mean',
        'prediction_family_id': 'count',
    }).rename(columns={
        'winner_correct': 'winner_accuracy',
        'method_correct': 'method_accuracy',
        'round_error': 'mean_round_error',
        'prediction_family_id': 'reconciliation_count',
    })
    daily['rolling_winner_accuracy'] = daily['winner_accuracy'].rolling(ROLLING_WINDOW, min_periods=1).mean()
    daily['rolling_method_accuracy'] = daily['method_accuracy'].rolling(ROLLING_WINDOW, min_periods=1).mean()
    daily['rolling_round_error'] = daily['mean_round_error'].rolling(ROLLING_WINDOW, min_periods=1).mean()
    return daily


def version_breakdown(df):
    by_model = df.groupby('model_version')['winner_correct'].mean().sort_values()
    by_calib = df.groupby('calibration_version')['winner_correct'].mean().sort_values()
    return by_model, by_calib


def family_performance(df):
    fam = df.groupby('prediction_family_id')['winner_correct'].agg(['mean', 'count'])
    under = fam.sort_values('mean').head(5)
    over = fam.sort_values('mean', ascending=False).head(5)
    return under, over


def main():
    from pathlib import Path
    import sys
    input_csv = Path(r"C:\Users\jusin\ai_risa_data\exports\reconciliation_export.csv")
    output_csv = Path(r"C:\Users\jusin\ai_risa_data\reports\reconciliation_trend_report.csv")

    print("AI-RISA Reconciliation Trend Report")
    print("===================================")
    print(f"Input CSV: {input_csv}")
    print(f"Input exists: {input_csv.exists()}")

    if not input_csv.exists():
        print("FAIL: reconciliation_export.csv is missing")
        sys.exit(1)


    import json
    try:
        df = pd.read_csv(input_csv)
        print(f"Loaded DataFrame shape: {df.shape}")
        print(f"Loaded row count: {len(df)}")
        # Minimal patch: load canonical fight record history as read-only
        with open(r"C:\ai_risa_data\reports\canonical_past_fight_records.json", "r", encoding="utf-8") as f:
            canonical_history = json.load(f)
        canonical_history_df = pd.DataFrame(canonical_history)
        print(f"Loaded canonical history records: {len(canonical_history_df)}")

        # --- Diagnostic comparison layer: reconciliation vs canonical history ---
        import numpy as np
        # Helper: normalize fighter keys
        def normalize_fighter_key(row):
            a = str(row.get('fighter_a_id', '')).lower().strip()
            b = str(row.get('fighter_b_id', '')).lower().strip()
            return '::'.join(sorted([a, b]))

        # Add normalized keys to both DataFrames
        df['norm_fighter_key'] = df.apply(normalize_fighter_key, axis=1)
        canonical_history_df['norm_fighter_key'] = canonical_history_df.apply(normalize_fighter_key, axis=1)

        # 1. Exact matchup_id match
        match1 = pd.merge(df, canonical_history_df, on='matchup_id', suffixes=('_recon', '_hist'), how='left', indicator=True)
        match1_found = match1[match1['_merge'] == 'both']
        unmatched1 = match1[match1['_merge'] == 'left_only']

        # 2. Normalized fighter key match (for unmatched only)

        unmatched1 = unmatched1.drop(columns=[c for c in unmatched1.columns if c.endswith('_hist') or c == '_merge'], errors='ignore')
        # Recompute norm_fighter_key for unmatched1
        unmatched1['norm_fighter_key'] = unmatched1.apply(normalize_fighter_key, axis=1)
        match2 = pd.merge(unmatched1, canonical_history_df, on='norm_fighter_key', suffixes=('_recon', '_hist'), how='left', indicator=True)
        match2_found = match2[match2['_merge'] == 'both']
        unmatched2 = match2[match2['_merge'] == 'left_only']

        # 3. Event + fighter pair fallback (for remaining unmatched)
        def event_fighter_key(row):
            event = str(row.get('event', '') or row.get('event_recon', '') or row.get('event_hist', '')).lower().strip()
            a = str(row.get('fighter_a_id', '') or row.get('fighter_a_id_recon', '') or row.get('fighter_a_id_hist', '')).lower().strip()
            b = str(row.get('fighter_b_id', '') or row.get('fighter_b_id_recon', '') or row.get('fighter_b_id_hist', '')).lower().strip()
            return f"{event}::{a}::{b}"
        df['event_fighter_key'] = df.apply(event_fighter_key, axis=1)
        canonical_history_df['event_fighter_key'] = canonical_history_df.apply(event_fighter_key, axis=1)

        # Drop _merge and columns ending with _recon/_hist to avoid indicator/column conflicts
        cols_to_drop = [c for c in unmatched2.columns if c.endswith('_recon') or c.endswith('_hist') or c == '_merge']
        # Keep event_fighter_key if present, else will be recomputed
        cols_to_drop = [c for c in cols_to_drop if c != 'event_fighter_key']
        unmatched2 = unmatched2.drop(columns=cols_to_drop, errors='ignore')
        # Recompute event_fighter_key for unmatched2
        unmatched2['event_fighter_key'] = unmatched2.apply(event_fighter_key, axis=1)
        match3 = pd.merge(unmatched2, canonical_history_df, on='event_fighter_key', suffixes=('_recon', '_hist'), how='left', indicator=True)
        match3_found = match3[match3['_merge'] == 'both']
        unmatched3 = match3[match3['_merge'] == 'left_only']

        # Combine all matches
        match_report = pd.concat([
            match1_found.assign(match_type='matchup_id'),
            match2_found.assign(match_type='norm_fighter_key'),
            match3_found.assign(match_type='event_fighter_key')
        ], ignore_index=True)

        # Find duplicate and conflicting matches
        dupes = match_report.duplicated(subset=['matchup_id'], keep=False)
        conflicts = match_report[dupes]

        # Output paths
        out_dir = Path(r'C:/ai_risa_data/reports')
        match_report_path = out_dir / 'reconciliation_history_match_report.csv'
        unmatched_path = out_dir / 'reconciliation_history_unmatched.csv'
        conflicts_path = out_dir / 'reconciliation_history_conflicts.csv'
        summary_path = out_dir / 'reconciliation_history_match_summary.json'

        # Write outputs
        match_report.to_csv(match_report_path, index=False)
        unmatched3.to_csv(unmatched_path, index=False)
        conflicts.to_csv(conflicts_path, index=False)
        summary = {
            'total_reconciliation_rows': int(len(df)),
            'matched_rows': int(len(match_report)),
            'unmatched_rows': int(len(unmatched3)),
            'conflict_rows': int(len(conflicts)),
            'match_rate': float(len(match_report)) / max(1, len(df)),
        }
        import json as _json
        with open(summary_path, 'w', encoding='utf-8') as f:
            _json.dump(summary, f, indent=2)
        print(f"Diagnostic comparison complete. Outputs:")
        print(f"  Matched: {match_report_path}")
        print(f"  Unmatched: {unmatched_path}")
        print(f"  Conflicts: {conflicts_path}")
        print(f"  Summary: {summary_path}")
        print(f"  Matched rows: {len(match_report)} | Unmatched: {len(unmatched3)} | Conflicts: {len(conflicts)}")
    except Exception as e:
        print(f"FAIL: error loading input CSV: {type(e).__name__}: {e}")
        raise

    if df.empty:
        print("FAIL: reconciliation_export.csv exists but is empty")
        sys.exit(1)

    # Use the correct timestamp column for trend analysis
    daily = compute_trends(df, date_col='reconciled_timestamp')
    by_model, by_calib = version_breakdown(df)
    under, over = family_performance(df)

    # Save main trend table
    daily.to_csv(output_csv)
    print(f"Output CSV written: {output_csv}")
    print(f"Output exists: {output_csv.exists()}")

    # Print summary
    print("\nRolling accuracy (last 5 days):")
    print(daily[['rolling_winner_accuracy', 'rolling_method_accuracy', 'rolling_round_error']].tail())
    print("\nWinner accuracy by model version:")
    print(by_model)
    print("\nWinner accuracy by calibration version:")
    print(by_calib)
    print("\nTop underperforming families:")
    print(under)
    print("\nTop improving families:")
    print(over)

if __name__ == "__main__":
    main()
