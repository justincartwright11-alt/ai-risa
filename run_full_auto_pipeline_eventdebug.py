# Derivative debug version of the pipeline for event-driven report generation
# Adds debug prints to trace file resolution and existence for the main event

import argparse
import os
import sys
import json
from docx import Document
from run_full_auto_pipeline_recovered_embed import resolve_bout_identity, is_true_tba_bout, build_fight_report

def debug_print(msg, *args):
    print(f"[DEBUG] {msg}", *args)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True, choices=['fighter', 'matchup', 'event'])
    parser.add_argument('--fighter', help='Fighter name for single dossier')
    parser.add_argument('--fighter-a', help='Fighter A for matchup')
    parser.add_argument('--fighter-b', help='Fighter B for matchup')
    parser.add_argument('--event', help='Event slug for event mode (e.g., boxing_wollongong_2026_04_05)')
    parser.add_argument('--report', help='Report type (Full Prim Report, Fighter/Trainer, Promoter, Broadcast, Premium Fan)')
    parser.add_argument('--format', help='Export format (DOCX or PDF)')
    args = parser.parse_args()
    mode = str(args.mode or '').strip().lower()
    report = str(args.report or '').strip().lower().replace('_', ' ')
    fmt = str(args.format or '').strip().lower()
    debug_print('Dispatch args', {'mode': mode, 'report': report, 'format': fmt})

    report_names = {'full prim report', 'full prim', 'full_prim'}
    if mode == 'event' and report.replace('_', ' ') in report_names:
        event_summary = None
        event_summary_path = f"C:/ai_risa_data/events/{args.event}.json"
        debug_print('Event summary path', event_summary_path)
        if os.path.exists(event_summary_path):
            with open(event_summary_path, 'r', encoding='utf-8') as f:
                event_summary = json.load(f)
        else:
            debug_print('Event summary file does not exist!')
        event_summary = event_summary or {}
        debug_print('Event summary keys', list(event_summary.keys()))
        bout_entries = (
            event_summary.get('results')
            or event_summary.get('fights')
            or event_summary.get('bouts')
            or event_summary.get('card')
            or []
        )
        if isinstance(bout_entries, dict):
            bout_entries = list(bout_entries.values())
        debug_print('Bout entries count', len(bout_entries))
        for i, bout in enumerate(bout_entries):
            debug_print(f'Bout {i} raw', bout)
            fighters = bout.get('fighters') or []
            left = fighters[0] if len(fighters) > 0 else ''
            right = fighters[1] if len(fighters) > 1 else ''
            fight_name = f"{left} vs. {right}" if left and right else left or right or 'Unknown Bout'
            debug_print(f'Bout {i} fight_name', fight_name)
            pred_path = bout.get('prediction_file')
            pred = {}
            if pred_path:
                debug_print(f'Bout {i} prediction file path', pred_path)
                if os.path.exists(pred_path):
                    with open(pred_path, 'r', encoding='utf-8') as pf:
                        pred = json.load(pf)
                    debug_print(f'Bout {i} prediction file loaded')
                else:
                    debug_print(f'Bout {i} prediction file missing!')
            else:
                debug_print(f'Bout {i} no prediction file path in bout')
            fighter_a_profile = None
            fighter_b_profile = None
            fighter_a_profile_path = f"C:/ai_risa_data/fighters/{left.lower().replace(' ', '_')}.json"
            fighter_b_profile_path = f"C:/ai_risa_data/fighters/{right.lower().replace(' ', '_')}.json"
            debug_print(f'Bout {i} fighter_a_profile_path', fighter_a_profile_path)
            debug_print(f'Bout {i} fighter_b_profile_path', fighter_b_profile_path)
            if os.path.exists(fighter_a_profile_path):
                with open(fighter_a_profile_path, 'r', encoding='utf-8') as f:
                    fighter_a_profile = json.load(f)
                debug_print(f'Bout {i} fighter_a_profile loaded')
            else:
                debug_print(f'Bout {i} fighter_a_profile missing!')
            if os.path.exists(fighter_b_profile_path):
                with open(fighter_b_profile_path, 'r', encoding='utf-8') as f:
                    fighter_b_profile = json.load(f)
                debug_print(f'Bout {i} fighter_b_profile loaded')
            else:
                debug_print(f'Bout {i} fighter_b_profile missing!')
            matchup_data = bout
            fighter_a_name, fighter_b_name, bout_title = resolve_bout_identity(matchup_data, fight_name, pred, fighter_a_profile, fighter_b_profile)
            debug_print(f'Bout {i} resolved names', {'fighter_a_name': fighter_a_name, 'fighter_b_name': fighter_b_name, 'bout_title': bout_title})
            if is_true_tba_bout(fighter_a_name, fighter_b_name):
                debug_print(f'Bout {i} is TBA, skipping')
                continue
            # Try to build fight report
            fight_report = build_fight_report(
                prediction=pred,
                fighter_a_profile=fighter_a_profile,
                fighter_b_profile=fighter_b_profile,
                matchup_data=matchup_data,
                event_summary=event_summary,
                event_fight_name=fight_name,
            )
            if fight_report:
                debug_print(f'Bout {i} fight_report built', fight_report)
            else:
                debug_print(f'Bout {i} fight_report is None!')
    else:
        debug_print(f'Unknown mode or report type. mode={mode!r}, report={report!r}, format={fmt!r}')
        sys.exit(1)

if __name__ == "__main__":
    main()
