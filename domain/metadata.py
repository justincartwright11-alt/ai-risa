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
    return []

def normalize_bout_candidate(bout, idx):
    """
    Normalize a bout candidate to the stable handler contract shape.
    Handles dicts with fighters, red/blue/a/b corners, etc.
    """
    notes = []
    fighter_a = fighter_b = None
    if isinstance(bout, dict):
        # Fighters as list
        if "fighters" in bout and isinstance(bout["fighters"], list) and len(bout["fighters"]) == 2:
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
