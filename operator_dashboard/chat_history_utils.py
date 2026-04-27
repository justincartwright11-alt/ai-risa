import json
import os
from datetime import datetime, timezone

CHAT_HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'chat_history.json')
MAX_HISTORY = 200

# Message format:
# {"role": "user"|"assistant"|"system", "content": str, "timestamp": ISO str, "action": str, "normalized_event": str|None}

def load_chat_history():
    try:
        if not os.path.exists(CHAT_HISTORY_PATH):
            return []
        with open(CHAT_HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            # Validate structure
            cleaned = []
            for msg in data[-MAX_HISTORY:]:
                if not isinstance(msg, dict):
                    continue
                if 'role' in msg and 'content' in msg and 'timestamp' in msg:
                    cleaned.append(msg)
            return cleaned[-MAX_HISTORY:]
    except Exception:
        return []

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history[-MAX_HISTORY:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_chat_history():
    try:
        with open(CHAT_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def append_chat_message(role, content, action=None, normalized_event=None, details=None, error=None):
    history = load_chat_history()
    msg = {
        'role': role,
        'content': content,
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'action': action or '',
        'normalized_event': normalized_event,
        'details': details or '',
        'error': error or None
    }
    history.append(msg)
    save_chat_history(history)
    return msg
