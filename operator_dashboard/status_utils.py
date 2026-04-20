import os
from operator_dashboard.action_ledger_utils import safe_read_ledger, summarize_ledger
from operator_dashboard.chat_history_utils import load_chat_history
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
QUEUE_FILE = os.path.join(PROJECT_ROOT, 'event_coverage_queue.csv')
LIVE_LOG = os.path.join(PROJECT_ROOT, 'docs', 'live_release_window_log.md')
MANIFEST = os.path.join(PROJECT_ROOT, 'docs', 'runtime_release_manifest.md')
GO_NO_GO = os.path.join(PROJECT_ROOT, 'docs', 'operator_release_go_no_go_note.md')

OPERATOR_FILES = [
    ('queue_file_present', QUEUE_FILE),
    ('live_log_present', LIVE_LOG),
    ('manifest_present', MANIFEST),
    ('go_no_go_note_present', GO_NO_GO)
]

def safe_exists(path):
    try:
        return os.path.exists(path)
    except Exception:
        return False

def get_status():
    now = datetime.utcnow().isoformat() + 'Z'
    # Chat history
    try:
        chat_history = load_chat_history()
        chat_history_available = True
        total_chat_messages = len(chat_history)
    except Exception:
        chat_history = []
        chat_history_available = False
        total_chat_messages = 0
    # Ledger
    try:
        ledger_entries = safe_read_ledger()
        action_ledger_available = True
        total_logged_actions = len(ledger_entries)
    except Exception:
        ledger_entries = []
        action_ledger_available = False
        total_logged_actions = 0
    # Ledger summary
    summary = summarize_ledger() if action_ledger_available else {}
    # Operator files
    file_status = {k: safe_exists(p) for k, p in OPERATOR_FILES}
    # Errors
    errors = summary.get('errors', []) if summary else []
    return {
        'ok': True,
        'app_name': 'AI-RISA Local Operator Dashboard',
        'timestamp': now,
        'chat_history_available': chat_history_available,
        'action_ledger_available': action_ledger_available,
        'last_action': summary.get('last_action', ''),
        'last_normalized_event': summary.get('last_normalized_event', ''),
        'last_outcome_status': summary.get('last_outcome_status', ''),
        'last_success_timestamp': summary.get('last_success_timestamp', ''),
        'last_failure_timestamp': summary.get('last_failure_timestamp', ''),
        'total_logged_actions': total_logged_actions,
        'total_chat_messages': total_chat_messages,
        **file_status,
        'errors': errors
    }
