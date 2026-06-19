"""
button3_improved_source_yield_engine.py

Read-only framework for Button 3 auto result source discovery and classification.
Provides multi-signal matching and 5 simple result state classification.

GOVERNANCE: No mutations, no writes, no learning, no calibration, no queue writes.
"""

import re
import unicodedata
from datetime import datetime

# ─── State Constants ───────────────────────────────────────────────────────────

RESULT_SUMMARY_STATES = [
    "Results Found",
    "Needs Source",
    "Conflict",
    "No Result Yet",
    "Ready to Compare",
]

# Trusted source host patterns — tier A (official promotions)
TIER_A_SOURCE_PATTERNS = [
    r"ufc\.com/event/",
    r"ufcstats\.com/event-details/",
    r"onefc\.com/events/",
    r"onefc\.com/.*/fight-results",
    r"matchroom\.com/events/",
    r"pfl\.com/event/",
    r"pfl\.com/.*/fight-results",
    r"queensberrypromotions\.com/events/",
    r"toprank\.com/fights/",
    r"toprank\.com/events/",
]

# Trusted source host patterns — tier B (sports news)
TIER_B_SOURCE_PATTERNS = [
    r"espn\.com/",
    r"foxsports\.com/",
    r"reuters\.com/",
]

# Trusted source host patterns — tier C (community databases)
TIER_C_SOURCE_PATTERNS = [
    r"sherdog\.com/",
    r"tapology\.com/",
    r"boxrec\.com/",
    r"flashscore\.com/",
    r"mmadecisions\.com/",
]

ALL_TRUSTED_PATTERNS = TIER_A_SOURCE_PATTERNS + TIER_B_SOURCE_PATTERNS + TIER_C_SOURCE_PATTERNS


# ─── String Utilities ──────────────────────────────────────────────────────────

def _normalize_token(text):
    """Normalize unicode, strip accents, lowercase, strip extra whitespace."""
    if not text:
        return ""
    # Normalize unicode (NFD decomposition to strip combining chars)
    nfkd = unicodedata.normalize("NFD", str(text))
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


def _extract_fighters_from_fight_name(fight_name):
    """
    Extract fighter A and fighter B from a fight name like 'Jones vs Gane'.
    Returns (fighter_a, fighter_b) or (None, None) if parse fails.
    """
    if not fight_name:
        return None, None
    for sep in [" vs ", " VS ", " Vs ", " vs. ", " VS. "]:
        if sep in fight_name:
            parts = fight_name.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return None, None


def _fighter_names_match(name_a, name_b):
    """
    Returns True if two fighter names are considered a match.
    Handles exact, normalized, reversed, and partial matches.
    """
    if not name_a or not name_b:
        return False
    norm_a = _normalize_token(name_a)
    norm_b = _normalize_token(name_b)
    if norm_a == norm_b:
        return True
    # Check if last names match (at least 4 chars)
    parts_a = norm_a.split()
    parts_b = norm_b.split()
    if parts_a and parts_b:
        last_a = parts_a[-1]
        last_b = parts_b[-1]
        if len(last_a) >= 4 and last_a == last_b:
            return True
    # Partial: one name contains the other (minimum length 4)
    if len(norm_a) >= 4 and len(norm_b) >= 4:
        if norm_a in norm_b or norm_b in norm_a:
            return True
    return False


def _event_names_match(event_a, event_b):
    """
    Returns a similarity score (0.0-1.0) between two event names.
    """
    if not event_a or not event_b:
        return 0.0
    norm_a = _normalize_token(event_a)
    norm_b = _normalize_token(event_b)
    if norm_a == norm_b:
        return 1.0
    # Simple token overlap
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return overlap / union if union > 0 else 0.0


def _date_proximity_score(date_a, date_b, tolerance_days=14):
    """
    Returns a score (0.0-1.0) based on date proximity.
    Score of 1.0 if same day, decreasing linearly to 0.0 at tolerance_days.
    """
    if not date_a or not date_b:
        return 0.5  # neutral if no date info
    try:
        if isinstance(date_a, str):
            date_a = datetime.fromisoformat(date_a[:10])
        if isinstance(date_b, str):
            date_b = datetime.fromisoformat(date_b[:10])
        diff = abs((date_a - date_b).days)
        if diff == 0:
            return 1.0
        if diff >= tolerance_days:
            return 0.0
        return 1.0 - (diff / tolerance_days)
    except Exception:
        return 0.5


def _get_promotion_from_row(row):
    """Extract the promotion name from a waiting row dict."""
    return (
        row.get("promotion")
        or row.get("organization")
        or row.get("event_promotion")
        or ""
    )


# ─── Candidate Scoring ─────────────────────────────────────────────────────────

def _score_candidate_match(row, candidate):
    """
    Score a candidate result against a waiting row.
    Returns a score in [0.0, 1.0].
    """
    score = 0.0
    weight_total = 0.0

    # Fighter name matching (weight: 0.5)
    fighter_a, fighter_b = _extract_fighters_from_fight_name(row.get("fight_name", ""))
    cand_fa = candidate.get("fighter_a", "")
    cand_fb = candidate.get("fighter_b", "")

    fighter_weight = 0.5
    if fighter_a and fighter_b:
        match_ab = (
            _fighter_names_match(fighter_a, cand_fa)
            and _fighter_names_match(fighter_b, cand_fb)
        )
        match_ba = (
            _fighter_names_match(fighter_a, cand_fb)
            and _fighter_names_match(fighter_b, cand_fa)
        )
        if match_ab or match_ba:
            score += fighter_weight
    elif fighter_a:
        if _fighter_names_match(fighter_a, cand_fa) or _fighter_names_match(fighter_a, cand_fb):
            score += fighter_weight * 0.5
    weight_total += fighter_weight

    # Event name matching (weight: 0.2)
    event_weight = 0.2
    event_sim = _event_names_match(row.get("event_name", ""), candidate.get("event_name", ""))
    score += event_weight * event_sim
    weight_total += event_weight

    # Date proximity (weight: 0.2)
    date_weight = 0.2
    date_score = _date_proximity_score(row.get("event_date"), candidate.get("event_date"))
    score += date_weight * date_score
    weight_total += date_weight

    # Promotion match (weight: 0.1)
    promo_weight = 0.1
    row_promo = _normalize_token(_get_promotion_from_row(row))
    cand_promo = _normalize_token(candidate.get("promotion", ""))
    if row_promo and cand_promo and row_promo in cand_promo:
        score += promo_weight
    weight_total += promo_weight

    return score / weight_total if weight_total > 0 else 0.0


# ─── State Classification ──────────────────────────────────────────────────────

def classify_result_state(row, candidates):
    """
    Classify a waiting row into one of the 5 result states based on candidates.

    Args:
        row: dict with fight_name, event_name, event_date, etc.
        candidates: list of candidate result dicts

    Returns:
        One of RESULT_SUMMARY_STATES
    """
    if not candidates:
        return "Needs Source"

    # Score all candidates
    MATCH_THRESHOLD = 0.6
    CONFLICT_THRESHOLD = 0.6

    matched = [c for c in candidates if _score_candidate_match(row, c) >= MATCH_THRESHOLD]

    if not matched:
        return "No Result Yet"

    # Check for conflict: multiple candidates with different declared winners
    winners = set()
    for c in matched:
        w = _normalize_token(c.get("declared_winner", ""))
        if w:
            winners.add(w)

    if len(winners) > 1:
        return "Conflict"

    # Has a declared result ready for comparison
    if any(c.get("declared_winner") for c in matched):
        return "Ready to Compare"

    return "Results Found"


# ─── Source Search Tasks ───────────────────────────────────────────────────────

def build_source_search_tasks(row):
    """
    Build a list of source search tasks for a waiting row.
    Each task is a dict with: query, source_patterns, tier

    Args:
        row: dict with fight_name, event_name, event_date, promotion, etc.

    Returns:
        list of task dicts
    """
    tasks = []
    fight_name = row.get("fight_name", "")
    event_name = row.get("event_name", "")
    promotion = _get_promotion_from_row(row)
    fighter_a, fighter_b = _extract_fighters_from_fight_name(fight_name)

    # Tier A tasks — official promotion pages
    if promotion or event_name:
        query_parts = []
        if event_name:
            query_parts.append(event_name)
        if fighter_a and fighter_b:
            query_parts.append(f"{fighter_a} vs {fighter_b}")
        if promotion:
            query_parts.append(promotion)
        query_parts.append("fight results")
        tasks.append({
            "query": " ".join(query_parts),
            "source_patterns": TIER_A_SOURCE_PATTERNS,
            "tier": "A",
            "row_key": row.get("selected_key", ""),
        })

    # Tier B tasks — sports news
    if fighter_a and fighter_b:
        tasks.append({
            "query": f"{fighter_a} vs {fighter_b} result winner",
            "source_patterns": TIER_B_SOURCE_PATTERNS,
            "tier": "B",
            "row_key": row.get("selected_key", ""),
        })

    # Tier C tasks — community databases
    if fighter_a and fighter_b:
        tasks.append({
            "query": f"{fighter_a} {fighter_b} fight record",
            "source_patterns": TIER_C_SOURCE_PATTERNS,
            "tier": "C",
            "row_key": row.get("selected_key", ""),
        })

    return tasks
