import json
import os
import re


_PLACEHOLDER_FIGHTER_TOKENS = {
    "tbd",
    "tba",
    "unknown",
}


def _slugify_event_name(name):
    if not isinstance(name, str):
        return ""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_")


def _extract_bouts_from_event_json(event_payload):
    if not isinstance(event_payload, dict):
        return []
    bout_keys = ["bouts", "fights", "card", "matchups"]
    for key in bout_keys:
        if isinstance(event_payload.get(key), list):
            return event_payload.get(key)
    for key in ["event", "details", "payload"]:
        container = event_payload.get(key)
        if isinstance(container, dict):
            for bkey in bout_keys:
                if isinstance(container.get(bkey), list):
                    return container.get(bkey)
    return []


def _is_placeholder_fighter_name(value):
    if not isinstance(value, str):
        return False
    return value.strip().lower() in _PLACEHOLDER_FIGHTER_TOKENS


def _resolve_event_source_path(task):
    # Highest-precedence: explicit source path in queue/task payload.
    source_path = task.get("source_path")
    if isinstance(source_path, str) and source_path.strip():
        candidate = source_path.strip()
        if os.path.exists(candidate):
            return candidate

    # Deterministic fallback: derive from event_name + event_date.
    event_name = task.get("event_name")
    event_date = task.get("event_date")
    slug = _slugify_event_name(event_name)
    if not slug:
        return None

    events_dir = "events"
    if not os.path.isdir(events_dir):
        return None

    date_token = ""
    if isinstance(event_date, str):
        date_token = event_date.strip().replace("-", "_")

    exact_name = f"{slug}_{date_token}.json" if date_token else f"{slug}.json"
    exact_path = os.path.join(events_dir, exact_name)
    if os.path.exists(exact_path):
        return exact_path

    # Safe fallback search limited to events/ directory.
    candidates = []
    for filename in os.listdir(events_dir):
        if not filename.lower().endswith(".json"):
            continue
        base = filename[:-5].lower()
        if slug in base and (not date_token or date_token in base):
            candidates.append(os.path.join(events_dir, filename))
    if len(candidates) == 1:
        return candidates[0]
    return None


def extract_bouts_from_payload(task):
    """
    Extract bouts from a variety of likely keys and nested containers in the event payload.
    Returns a flat list of bout candidates (dicts or values).
    """
    # Common keys for bouts
    bout_keys = ["bouts", "fights", "card", "matchups"]
    # Try direct keys
    for key in bout_keys:
        if isinstance(task.get(key), list):
            return task.get(key)
    # Try nested event containers
    for key in ["event", "details", "payload"]:
        container = task.get(key)
        if isinstance(container, dict):
            for bkey in bout_keys:
                if isinstance(container.get(bkey), list):
                    return container.get(bkey)
    # Fallback: look for any list value in the payload
    for v in task.values():
        if isinstance(v, list):
            return v
    source_path = _resolve_event_source_path(task)
    if source_path:
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                event_payload = json.load(f)
            bouts = _extract_bouts_from_event_json(event_payload)
            if isinstance(bouts, list):
                return bouts
        except Exception:
            return []
    return []

def normalize_bout_candidate(bout, idx):
    """
    Normalize a bout candidate to the stable handler contract shape.
    Handles dicts with fighters, red/blue/a/b corners, etc.
    """
    notes = []
    fighter_a = fighter_b = None
    if isinstance(bout, dict):
        # Canonical event JSON shape
        if "fighter_a" in bout and "fighter_b" in bout:
            fighter_a = norm_str(bout.get("fighter_a"))
            fighter_b = norm_str(bout.get("fighter_b"))
        # Alternate keyed shape used by some pipelines
        elif "fighter_1" in bout and "fighter_2" in bout:
            fighter_a = norm_str(bout.get("fighter_1"))
            fighter_b = norm_str(bout.get("fighter_2"))
        # Fighters as list
        elif "fighters" in bout and isinstance(bout["fighters"], list) and len(bout["fighters"]) == 2:
            fighter_a = norm_str(bout["fighters"][0])
            fighter_b = norm_str(bout["fighters"][1])
        # Red/Blue corners
        elif "red" in bout and "blue" in bout:
            fighter_a = norm_str(bout["red"])
            fighter_b = norm_str(bout["blue"])
        # A/B corners
        elif "a" in bout and "b" in bout:
            fighter_a = norm_str(bout["a"])
            fighter_b = norm_str(bout["b"])
        else:
            notes.append("fighters_invalid")
        weight_class = norm_str(bout.get("weight_class") or bout.get("division"))
        scheduled_rounds = norm_str(bout.get("scheduled_rounds") or bout.get("rounds"))
        is_title_fight = bout.get("is_title_fight")
        if isinstance(is_title_fight, str):
            is_title_fight = is_title_fight.strip().lower()
            if is_title_fight in ("yes", "true", "1"): is_title_fight = True
            elif is_title_fight in ("no", "false", "0"): is_title_fight = False
            else: is_title_fight = None
    else:
        notes.append("not_a_dict")
        weight_class = scheduled_rounds = is_title_fight = None
    if _is_placeholder_fighter_name(fighter_a):
        fighter_a = None
    if _is_placeholder_fighter_name(fighter_b):
        fighter_b = None
    if not fighter_a or not fighter_b:
        notes.append("fighters_invalid")
    return {
        "bout_index": idx,
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "weight_class": weight_class,
        "scheduled_rounds": scheduled_rounds,
        "is_title_fight": is_title_fight,
        "normalization_notes": notes
    }
from .normalization import norm_str, norm_dict

def normalize_event_metadata(task):
    fields = ["event_name", "event_date", "event_type", "promotion", "venue", "location"]
    meta = {}
    for k in fields:
        meta[k] = norm_str(task.get(k, None))
    return meta

def normalize_fighter_payload(task, plan):
    fighter_id = plan.get("identifier") or task.get("fighter_id")
    snap = norm_dict(task)
    return fighter_id, snap

def normalize_batch_entry(entry, idx):
    notes = []
    event_name = norm_str(entry.get("event_name")) if isinstance(entry, dict) else None
    event_date = norm_str(entry.get("event_date")) if isinstance(entry, dict) else None
    promotion = norm_str(entry.get("promotion")) if isinstance(entry, dict) else None
    entry_status = "accepted" if event_name else "skipped"
    if not isinstance(entry, dict):
        notes.append("not_a_dict")
    elif not event_name:
        notes.append("missing_event_name")
    return {
        "entry_index": idx,
        "event_name": event_name,
        "event_date": event_date,
        "promotion": promotion,
        "entry_status": entry_status,
        "normalization_notes": notes
    }
