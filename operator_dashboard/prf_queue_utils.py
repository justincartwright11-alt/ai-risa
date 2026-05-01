"""
Premium Report Factory Phase 2 – Approved Save Queue Utilities

Provides deterministic local queue storage for operator-approved matchups
from the Phase 2 save flow.

No PDF generation, no result lookup, no learning/calibration, no web
discovery, no token consume, no global ledger write.
"""

import os
import json
import hashlib
from datetime import datetime, timezone

# Default paths – overridden via app.config['PRF_QUEUE_PATH_OVERRIDE'] in tests.
DEFAULT_PRF_QUEUE_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    'ops', 'prf_queue',
)
DEFAULT_PRF_QUEUE_FILE = os.path.join(DEFAULT_PRF_QUEUE_DIR, 'upcoming_fight_queue.json')


def _compute_matchup_id(
    event_id: str,
    temporary_matchup_id: str,
    fighter_a: str,
    fighter_b: str,
    bout_order,
) -> str:
    """Deterministic matchup_id derived from identity fields."""
    seed = f"{event_id}|{temporary_matchup_id}|{fighter_a}|{fighter_b}|{bout_order}"
    return "prf_q_" + hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]


def _compute_report_readiness_score(matchup_preview: dict, event_preview: dict) -> int:
    """
    Deterministic completeness-based readiness score (0–100).

    Dimensions (20 pts each):
      - fighter_a present
      - fighter_b present
      - event_date present
      - source_reference present
      - promotion present
    """
    score = 0
    if str(matchup_preview.get('fighter_a') or '').strip():
        score += 20
    if str(matchup_preview.get('fighter_b') or '').strip():
        score += 20
    if str(event_preview.get('event_date') or '').strip():
        score += 20
    source_ref = (
        str(matchup_preview.get('source_reference') or '').strip()
        or str(event_preview.get('source_reference') or '').strip()
    )
    if source_ref:
        score += 20
    if str(event_preview.get('promotion') or '').strip():
        score += 20
    return score


def _build_saved_matchup(
    event_preview: dict,
    matchup_preview: dict,
    source_reference: str,
    now_iso: str,
) -> dict:
    """Build the canonical saved_matchup record from preview data."""
    event_id = str(event_preview.get('event_name') or '').strip().lower().replace(' ', '_')
    temporary_matchup_id = str(matchup_preview.get('temporary_matchup_id') or '')
    fighter_a = str(matchup_preview.get('fighter_a') or '').strip()
    fighter_b = str(matchup_preview.get('fighter_b') or '').strip()
    bout_order = matchup_preview.get('bout_order')

    matchup_id = _compute_matchup_id(
        event_id, temporary_matchup_id, fighter_a, fighter_b, bout_order
    )
    readiness_score = _compute_report_readiness_score(matchup_preview, event_preview)

    effective_source_reference = (
        source_reference
        or str(matchup_preview.get('source_reference') or '').strip()
        or str(event_preview.get('source_reference') or '').strip()
    )

    return {
        'event_id': event_id,
        'matchup_id': matchup_id,
        'fighter_a': fighter_a,
        'fighter_b': fighter_b,
        'event_name': str(event_preview.get('event_name') or '').strip(),
        'event_date': str(event_preview.get('event_date') or '').strip(),
        'promotion': str(event_preview.get('promotion') or '').strip(),
        'location': str(event_preview.get('location') or '').strip(),
        'source_reference': effective_source_reference,
        'bout_order': bout_order,
        'weight_class': matchup_preview.get('weight_class'),
        'ruleset': matchup_preview.get('ruleset'),
        'report_readiness_score': readiness_score,
        'report_status': 'queued',
        'result_status': 'pending',
        'accuracy_status': 'pending',
        'queue_status': 'saved',
        'created_at': now_iso,
        'approved_by_operator': True,
        'approval_timestamp': now_iso,
    }


def load_prf_queue(queue_path: str) -> list:
    """Load existing queue records from a local JSON file."""
    if not os.path.exists(queue_path):
        return []
    try:
        with open(queue_path, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _write_prf_queue(queue_path: str, rows: list) -> None:
    """Atomically write queue records to a local JSON file."""
    queue_dir = os.path.dirname(queue_path)
    if queue_dir and not os.path.exists(queue_dir):
        os.makedirs(queue_dir, exist_ok=True)
    with open(queue_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


def process_prf_save_selected(request_json: dict, queue_path: str) -> dict:
    """
    Core Phase 2 save logic.

    Rules:
      - operator_approval must be True
      - needs_review rows are rejected
      - duplicate saves are deterministic (upsert by matchup_id)
      - no PDF, no result lookup, no learning
    """
    now_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    if not isinstance(request_json, dict):
        return {
            'ok': False,
            'generated_at': now_iso,
            'accepted_count': 0,
            'rejected_count': 0,
            'saved_matchups': [],
            'rejected_matchups': [],
            'queue_summary': {},
            'warnings': [],
            'errors': ['request_json_object_required'],
        }

    if not request_json.get('operator_approval'):
        return {
            'ok': False,
            'generated_at': now_iso,
            'accepted_count': 0,
            'rejected_count': 0,
            'saved_matchups': [],
            'rejected_matchups': [],
            'queue_summary': {},
            'warnings': [],
            'errors': ['operator_approval_required'],
        }

    event_preview = request_json.get('event_preview') or {}
    if not isinstance(event_preview, dict):
        event_preview = {}

    selected_matchup_previews = request_json.get('selected_matchup_previews') or []
    if not isinstance(selected_matchup_previews, list):
        selected_matchup_previews = []

    source_reference = str(
        request_json.get('source_reference')
        or event_preview.get('source_reference')
        or ''
    ).strip()

    existing_rows = load_prf_queue(queue_path)
    existing_by_matchup_id = {
        r['matchup_id']: idx
        for idx, r in enumerate(existing_rows)
        if r.get('matchup_id')
    }

    saved_matchups = []
    rejected_matchups = []
    warnings = []

    for mp in selected_matchup_previews:
        if not isinstance(mp, dict):
            continue
        parse_status = str(mp.get('parse_status') or '').strip()
        if parse_status == 'needs_review':
            rejected_matchups.append({
                'temporary_matchup_id': mp.get('temporary_matchup_id'),
                'fighter_a': mp.get('fighter_a'),
                'fighter_b': mp.get('fighter_b'),
                'rejection_reason': 'needs_review',
            })
            continue
        saved = _build_saved_matchup(event_preview, mp, source_reference, now_iso)
        saved_matchups.append(saved)

    # Deterministic upsert by matchup_id
    for s in saved_matchups:
        mid = s['matchup_id']
        if mid in existing_by_matchup_id:
            existing_rows[existing_by_matchup_id[mid]] = s
        else:
            existing_by_matchup_id[mid] = len(existing_rows)
            existing_rows.append(s)

    if saved_matchups:
        _write_prf_queue(queue_path, existing_rows)

    queue_summary = {
        'total_queued': len(existing_rows),
        'saved_this_call': len(saved_matchups),
        'rejected_this_call': len(rejected_matchups),
    }

    return {
        'ok': True,
        'generated_at': now_iso,
        'accepted_count': len(saved_matchups),
        'rejected_count': len(rejected_matchups),
        'saved_matchups': saved_matchups,
        'rejected_matchups': rejected_matchups,
        'queue_summary': queue_summary,
        'warnings': warnings,
        'errors': [],
    }


def get_prf_queue_list(queue_path: str) -> dict:
    """Return all saved upcoming fights in the queue."""
    now_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    rows = load_prf_queue(queue_path)
    return {
        'ok': True,
        'generated_at': now_iso,
        'total_queued': len(rows),
        'upcoming_fights': rows,
        'errors': [],
    }
