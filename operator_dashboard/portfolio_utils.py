# --- Normalization helpers for scoring ---
REVIEW_PRIORITY_MAP = {
    'immediate_review': 3,
    'high': 2,
    'medium': 1,
    'low': 0,
    'none': 0,
    3: 3, 2: 2, 1: 1, 0: 0
}
ESCALATION_LEVEL_MAP = {
    'critical': 3,
    'high': 2,
    'medium': 1,
    'low': 0,
    'none': 0,
    3: 3, 2: 2, 1: 1, 0: 0
}
DIGEST_PRESSURE_MAP = {
    'critical': 10,
    'high': 8,
    'medium': 5,
    'low': 2,
    'none': 0,
}

def normalize_review_priority(val):
    if isinstance(val, int):
        return val
    return REVIEW_PRIORITY_MAP.get(str(val).lower(), 0)

def normalize_escalation_level(val):
    if isinstance(val, int):
        return val
    return ESCALATION_LEVEL_MAP.get(str(val).lower(), 0)

def normalize_digest_pressure(val):
    if isinstance(val, int):
        return val
    return DIGEST_PRESSURE_MAP.get(str(val).lower(), 0)

def normalize_pressure_band(val):
    v = str(val).lower()
    return v if v in PRESSURE_BANDS else 'quiet'
"""
portfolio_utils.py

Read-only portfolio aggregation for Build 18.
Groups event casefiles by pressure band for operator scanning.
"""
import time
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.anomaly_utils import aggregate_event_anomalies
from operator_dashboard.watchlist_utils import aggregate_event_watchlist
from operator_dashboard.digest_utils import aggregate_event_digest
from operator_dashboard.escalation_utils import aggregate_event_escalation
from operator_dashboard.review_queue_utils import aggregate_event_review_queue
from operator_dashboard.briefing_utils import aggregate_event_briefing
from operator_dashboard.casefile_utils import aggregate_event_casefile
from operator_dashboard.timeline_utils import aggregate_event_timeline
from operator_dashboard.action_ledger_utils import get_ledger_object

PRESSURE_BANDS = ["critical", "high", "medium", "low", "quiet"]

# Helper to assign pressure band based on strongest available signals
def assign_pressure_band(row):
    # Escalation/review pressure dominate, then digest, then anomalies, then default
    esc = normalize_escalation_level(row.get("escalation_level", 0))
    rev = normalize_review_priority(row.get("review_priority", 0))
    dig = normalize_digest_pressure(row.get("digest_pressure", 0))
    if esc >= 3 or rev >= 3:
        return "critical"
    if esc == 2 or rev == 2 or dig >= 8:
        return "high"
    if esc == 1 or rev == 1 or dig >= 5:
        return "medium"
    if row.get("anomaly_count", 0) > 0 or dig > 0:
        return "low"
    return "quiet"

def aggregate_portfolio():
    queue = safe_read_queue()
    event_ids = [row["event_id"] for row in queue.get("rows", [])]
    portfolio = []
    errors = []
    now = int(time.time())
    for eid in event_ids:
        try:
            row = aggregate_event_portfolio(eid)
            if row.get("event_found"):
                portfolio.append(row)
        except Exception as ex:
            errors.append(f"{eid}: {ex}")
    # Group by pressure band
    bands = {b: [] for b in PRESSURE_BANDS}
    for row in portfolio:
        band = row.get("pressure_band", "quiet")
        bands.setdefault(band, []).append(row)
    # Deterministic ordering
    def sort_key(r):
        return (
            PRESSURE_BANDS.index(r.get("pressure_band", "quiet")),
            -r.get("portfolio_score", 0),
            -r.get("review_priority", 0),
            -r.get("escalation_level", 0),
            -r.get("last_relevant_timestamp", 0),
            r.get("event_id", "")
        )
    for b in bands:
        bands[b] = sorted(bands[b], key=sort_key)
    # Flatten for output
    flat = [row for b in PRESSURE_BANDS for row in bands[b]]
    return {
        "ok": True,
        "timestamp": now,
        "portfolio_count": len(flat),
        "pressure_bands": {b: len(bands[b]) for b in PRESSURE_BANDS},
        "portfolio": flat,
        "summary": f"{len(flat)} events grouped by pressure band.",
        "recommendation": "Scan critical/high bands first.",
        "errors": errors
    }

def aggregate_event_portfolio(event_id):
    now = int(time.time())
    # Compose from all safe layers
    casefile = aggregate_event_casefile(event_id)
    if not casefile.get("ok") or not casefile.get("event_found"):
        return {
            "ok": True,
            "timestamp": now,
            "event_found": False,
            "event_id": event_id,
            "pressure_band": "quiet",
            "portfolio_score": 0,
            "casefile_summary": "",
            "top_reasons": [],
            "review_priority": 0,
            "escalation_level": 0,
            "digest_pressure": 0,
            "anomaly_count": 0,
            "queue_status": "not_found",
            "recommendation": "No data for event.",
            "errors": casefile.get("errors", [])
        }
    # Pull from all layers
    review = aggregate_event_review_queue(event_id)
    escalation = aggregate_event_escalation(event_id)
    digest = aggregate_event_digest(event_id)
    anomalies = aggregate_event_anomalies(event_id)
    timeline = aggregate_event_timeline(event_id)
    ledger = get_ledger_object(event_id)
    # Compose row
    review_priority = normalize_review_priority(review.get("review_priority", 0))
    escalation_level = normalize_escalation_level(escalation.get("escalation_level", 0))
    digest_pressure = normalize_digest_pressure(digest.get("digest_pressure", 0))
    anomaly_count = anomalies.get("anomaly_count", 0)
    row = {
        "ok": True,
        "timestamp": now,
        "event_found": True,
        "event_id": event_id,
        "casefile_summary": casefile.get("casefile_summary", ""),
        "top_reasons": (review.get("top_reasons") or escalation.get("reasons") or []),
        "review_priority": review_priority,
        "escalation_level": escalation_level,
        "digest_pressure": digest_pressure,
        "anomaly_count": anomaly_count,
        "queue_status": casefile.get("queue_status", "unknown"),
        "last_relevant_timestamp": timeline.get("last_relevant_timestamp", 0),
        "recommendation": casefile.get("operator_recommendation", ""),
        "source_layers": [
            "queue", "anomalies", "watchlist", "digest", "escalation", "review_queue", "briefing", "casefile", "timeline", "ledger"
        ],
        "errors": sum([
            casefile.get("errors", []), review.get("errors", []), escalation.get("errors", []), digest.get("errors", []), anomalies.get("errors", []), timeline.get("errors", []), ledger.get("errors", [])
        ], [])
    }
    # Portfolio score: weighted sum (all numeric)
    row["portfolio_score"] = (
        10 * escalation_level +
        8 * review_priority +
        5 * digest_pressure +
        2 * anomaly_count
    )
    row["pressure_band"] = assign_pressure_band(row)
    return row


def get_contract_status():
    return {'ok': True}
