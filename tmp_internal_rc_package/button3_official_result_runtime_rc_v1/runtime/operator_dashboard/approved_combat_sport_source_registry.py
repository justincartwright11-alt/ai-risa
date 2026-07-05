"""Governed approved combat-sport source registry for Button 1 discovery.

This module is preview-safe and side-effect free. It classifies approved
combat-sport sources, their tiers, and their governance impact without
scraping, saving, or mutating any dashboard state.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


ALLOWED_SPORT_VALUES = {
    "boxing",
    "mma",
    "kickboxing",
    "muay_thai",
    "multi_sport_alert",
}


@dataclass(frozen=True)
class SourceGovernance:
    """Normalized governance result for a source URL."""

    source_id: Optional[str]
    source_name: Optional[str]
    source_url: Optional[str]
    sport: Optional[str]
    modality: Optional[str]
    tier: Optional[str]
    domain: Optional[str]
    approved_for_event_card_discovery: bool
    approved_for_matchup_provenance: bool
    approved_for_results_verification: bool
    requires_secondary_confirmation: bool
    queue_save_eligible: bool
    official_source: bool
    alert_only: bool
    rejected: bool
    denial_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "sport": self.sport,
            "modality": self.modality,
            "tier": self.tier,
            "domain": self.domain,
            "approved_for_event_card_discovery": self.approved_for_event_card_discovery,
            "approved_for_matchup_provenance": self.approved_for_matchup_provenance,
            "approved_for_results_verification": self.approved_for_results_verification,
            "requires_secondary_confirmation": self.requires_secondary_confirmation,
            "queue_save_eligible": self.queue_save_eligible,
            "official_source": self.official_source,
            "alert_only": self.alert_only,
            "rejected": self.rejected,
            "denial_reason": self.denial_reason,
        }


APPROVED_COMBAT_SPORT_SOURCE_REGISTRY: List[Dict[str, Any]] = [
    {
        "source_id": "ufc_official_event_pages",
        "source_name": "UFC official event pages",
        "sport": "mma",
        "modality": "mma",
        "tier": "A",
        "domain": "ufc.com",
        "allowed_url_patterns": [r"^https?://(www\.)?ufc\.com/(event|events?)/.*", r"^https?://(www\.)?ufc\.com/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary UFC event provenance and discovery source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "ufc_stats_structured_records",
        "source_name": "UFC Stats",
        "sport": "mma",
        "modality": "mma",
        "tier": "A",
        "domain": "ufcstats.com",
        "allowed_url_patterns": [r"^https?://(www\.)?ufcstats\.com/event-details/.*", r"^https?://(www\.)?ufcstats\.com/.*"],
        "use_case": ["results_verification", "event_card_discovery", "matchup_provenance"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Official UFC structured statistics and event-detail verification.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "one_championship_official",
        "source_name": "ONE Championship official",
        "sport": "multi_sport_alert",
        "modality": "multi_sport_alert",
        "tier": "A",
        "domain": "onefc.com",
        "allowed_url_patterns": [r"^https?://(www\.)?onefc\.com/events/.*", r"^https?://(www\.)?onefc\.com/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Hybrid MMA / striking promotion. Classified as multi-sport alert for registry coverage.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "glory_official_event_pages",
        "source_name": "GLORY official event pages",
        "sport": "kickboxing",
        "modality": "kickboxing",
        "tier": "A",
        "domain": "glorykickboxing.com",
        "allowed_url_patterns": [r"^https?://(www\.)?glorykickboxing\.com/.*", r"^https?://(www\.)?glory\.com/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary kickboxing event source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "matchroom_official_boxing",
        "source_name": "Matchroom official event pages",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "A",
        "domain": "matchroomboxing.com",
        "allowed_url_patterns": [r"^https?://(www\.)?matchroomboxing\.com/.*", r"^https?://(www\.)?matchroom\.com/boxing/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary boxing promoter source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "queensberry_official_boxing",
        "source_name": "Queensberry official event pages",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "A",
        "domain": "queensberry.co.uk",
        "allowed_url_patterns": [r"^https?://(www\.)?queensberry\.co\.uk/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary boxing promoter source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "top_rank_official_boxing",
        "source_name": "Top Rank official event pages",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "A",
        "domain": "toprank.com",
        "allowed_url_patterns": [r"^https?://(www\.)?toprank\.com/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary boxing promoter source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "no_limit_official_boxing",
        "source_name": "No Limit Boxing official event pages",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "A",
        "domain": "nolimitboxing.com",
        "allowed_url_patterns": [r"^https?://(www\.)?nolimitboxing\.com/.*"],
        "use_case": ["event_card_discovery", "matchup_provenance", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": True,
        "requires_secondary_confirmation": False,
        "notes": "Primary boxing promoter source.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "boxrec_structured_boxing",
        "source_name": "BoxRec",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "B",
        "domain": "boxrec.com",
        "allowed_url_patterns": [r"^https?://(www\.)?boxrec\.com/.*"],
        "use_case": ["records", "ranking", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": False,
        "requires_secondary_confirmation": False,
        "notes": "Structured boxing records database.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "fight_matrix_structured_mma",
        "source_name": "Fight Matrix",
        "sport": "mma",
        "modality": "mma",
        "tier": "B",
        "domain": "fightmatrix.com",
        "allowed_url_patterns": [r"^https?://(www\.)?fightmatrix\.com/.*"],
        "use_case": ["records", "ranking", "results_verification"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": False,
        "requires_secondary_confirmation": False,
        "notes": "Structured MMA ranking and records database.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "muay_thai_records_structured",
        "source_name": "Muay Thai Records",
        "sport": "muay_thai",
        "modality": "muay_thai",
        "tier": "B",
        "domain": "muaythairecords.com",
        "allowed_url_patterns": [r"^https?://(www\.)?muaythairecords\.com/.*"],
        "use_case": ["records", "ranking", "results_verification", "event_card_discovery"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": True,
        "allowed_for_results_verification": True,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Structured Muay Thai records source with secondary confirmation required before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "boxing_scene_calendar",
        "source_name": "BoxingScene",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "C",
        "domain": "boxingscene.com",
        "allowed_url_patterns": [r"^https?://(www\.)?boxingscene\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery calendar only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "bad_left_hook_calendar",
        "source_name": "Bad Left Hook",
        "sport": "boxing",
        "modality": "boxing",
        "tier": "C",
        "domain": "badlefthook.com",
        "allowed_url_patterns": [r"^https?://(www\.)?badlefthook\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery calendar only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "tapology_mma_calendar",
        "source_name": "Tapology",
        "sport": "mma",
        "modality": "mma",
        "tier": "C",
        "domain": "tapology.com",
        "allowed_url_patterns": [r"^https?://(www\.)?tapology\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery source only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "sherdog_mma_calendar",
        "source_name": "Sherdog",
        "sport": "mma",
        "modality": "mma",
        "tier": "C",
        "domain": "sherdog.com",
        "allowed_url_patterns": [r"^https?://(www\.)?sherdog\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery source only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "combat_press_kickboxing_calendar",
        "source_name": "Combat Press",
        "sport": "kickboxing",
        "modality": "kickboxing",
        "tier": "C",
        "domain": "combatpress.com",
        "allowed_url_patterns": [r"^https?://(www\.)?combatpress\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery source only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "ausmuaythai_calendar",
        "source_name": "AusMuayThai",
        "sport": "muay_thai",
        "modality": "muay_thai",
        "tier": "C",
        "domain": "ausmuaythai.com",
        "allowed_url_patterns": [r"^https?://(www\.)?ausmuaythai\.com/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery source only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "muaythai_victoria_calendar",
        "source_name": "Muaythai Victoria",
        "sport": "muay_thai",
        "modality": "muay_thai",
        "tier": "C",
        "domain": "muaythaivictoria.com.au",
        "allowed_url_patterns": [r"^https?://(www\.)?muaythaivictoria\.com\.au/.*"],
        "use_case": ["discovery", "calendar"],
        "allowed_for_event_card_discovery": True,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Discovery source only; requires confirmation before queue-save.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "flashscore_alert_only",
        "source_name": "Flashscore",
        "sport": "multi_sport_alert",
        "modality": "multi_sport_alert",
        "tier": "D",
        "domain": "flashscore.com",
        "allowed_url_patterns": [r"^https?://(www\.)?flashscore\.com/.*"],
        "use_case": ["alert", "speed"],
        "allowed_for_event_card_discovery": False,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Alert-only source. Never enough by itself for queue-save or provenance.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
    {
        "source_id": "venum_news_alert_only",
        "source_name": "Venum News",
        "sport": "multi_sport_alert",
        "modality": "multi_sport_alert",
        "tier": "D",
        "domain": "venum.com",
        "allowed_url_patterns": [r"^https?://(www\.)?venum\.com/.*"],
        "use_case": ["alert", "speed"],
        "allowed_for_event_card_discovery": False,
        "allowed_for_matchup_provenance": False,
        "allowed_for_results_verification": False,
        "official_source": False,
        "requires_secondary_confirmation": True,
        "notes": "Alert-only broad combat-sport hub. Never enough by itself for queue-save or provenance.",
        "prohibited_uses": ["queue_write_without_operator", "delivery", "learning", "calibration"],
    },
]


_COMPILED_PATTERNS: List[tuple[Dict[str, Any], List[re.Pattern[str]]]] = []
for entry in APPROVED_COMBAT_SPORT_SOURCE_REGISTRY:
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in entry["allowed_url_patterns"]]
    _COMPILED_PATTERNS.append((entry, compiled_patterns))


def get_approved_combat_sport_sources() -> List[Dict[str, Any]]:
    """Return a defensive copy of the approved combat-sport source registry."""

    return copy.deepcopy(APPROVED_COMBAT_SPORT_SOURCE_REGISTRY)


def _normalize_url(url: Optional[str]) -> str:
    return url.strip() if isinstance(url, str) else ""


def _sport_matches(entry_sport: Optional[str], requested_sport: Optional[str]) -> bool:
    if not requested_sport:
        return True
    if not entry_sport:
        return False
    requested = requested_sport.strip().lower()
    entry = entry_sport.strip().lower()
    if requested not in ALLOWED_SPORT_VALUES:
        return False
    if entry == requested:
        return True
    if entry == "multi_sport_alert":
        return requested in {"boxing", "mma", "kickboxing", "muay_thai", "multi_sport_alert"}
    return False


def _matches_allowed_patterns(url: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    for pattern in patterns:
        if pattern.search(url):
            return True
    return False


def _match_registry_entry(url: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the raw registry entry for a matching URL, if any."""

    normalized_url = _normalize_url(url)
    if not normalized_url:
        return None

    for entry, patterns in _COMPILED_PATTERNS:
        if not _matches_allowed_patterns(normalized_url, patterns):
            continue
        result = copy.deepcopy(entry)
        result["matched_url"] = normalized_url
        return result
    return None


def classify_source_url(url: Optional[str]) -> Optional[Dict[str, Any]]:
    """Classify a source URL against the approved registry.

    Returns a registry record with derived governance metadata when matched,
    otherwise ``None``.
    """

    result = _match_registry_entry(url)
    if result is None:
        return None
    result["source_governance"] = get_source_governance(result["matched_url"])
    return result


def is_approved_event_card_source(url: Optional[str], sport: Optional[str] = None) -> bool:
    """Return whether a URL is approved for event-card discovery provenance."""

    classification = classify_source_url(url)
    if not classification:
        return False
    if not _sport_matches(classification.get("sport"), sport):
        return False
    return bool(classification.get("allowed_for_event_card_discovery"))


def requires_secondary_confirmation(url: Optional[str]) -> bool:
    """Return whether the matched source must be confirmed before queue-save."""

    classification = classify_source_url(url)
    if not classification:
        return True
    tier = str(classification.get("tier") or "").upper()
    if tier in {"C", "D"}:
        return True
    return bool(classification.get("requires_secondary_confirmation"))


def get_source_governance(url: Optional[str]) -> Dict[str, Any]:
    """Return governed source handling metadata for a URL."""

    normalized_url = _normalize_url(url)
    if not normalized_url:
        return SourceGovernance(
            source_id=None,
            source_name=None,
            source_url=None,
            sport=None,
            modality=None,
            tier=None,
            domain=None,
            approved_for_event_card_discovery=False,
            approved_for_matchup_provenance=False,
            approved_for_results_verification=False,
            requires_secondary_confirmation=True,
            queue_save_eligible=False,
            official_source=False,
            alert_only=False,
            rejected=True,
            denial_reason="missing_url",
        ).to_dict()

    classification = _match_registry_entry(normalized_url)
    if not classification:
        return SourceGovernance(
            source_id=None,
            source_name=None,
            source_url=normalized_url,
            sport=None,
            modality=None,
            tier=None,
            domain=_extract_domain(normalized_url) or None,
            approved_for_event_card_discovery=False,
            approved_for_matchup_provenance=False,
            approved_for_results_verification=False,
            requires_secondary_confirmation=True,
            queue_save_eligible=False,
            official_source=False,
            alert_only=False,
            rejected=True,
            denial_reason="unapproved_source_url",
        ).to_dict()

    tier = str(classification.get("tier") or "").upper()
    approved_for_event_card_discovery = bool(classification.get("allowed_for_event_card_discovery")) and tier in {"A", "B", "C"}
    approved_for_matchup_provenance = bool(classification.get("allowed_for_matchup_provenance")) and tier in {"A", "B"}
    approved_for_results_verification = bool(classification.get("allowed_for_results_verification")) and tier in {"A", "B", "C"}
    secondary_confirmation = bool(classification.get("requires_secondary_confirmation")) or tier in {"C", "D"}
    queue_save_eligible = approved_for_event_card_discovery and approved_for_matchup_provenance and not secondary_confirmation and tier in {"A", "B"}
    alert_only = tier == "D"

    denial_reason = None
    if alert_only:
        denial_reason = "alert_only_source"
    elif secondary_confirmation and tier in {"B", "C"}:
        denial_reason = "needs_secondary_confirmation"

    return SourceGovernance(
        source_id=classification.get("source_id"),
        source_name=classification.get("source_name"),
        source_url=normalized_url,
        sport=classification.get("sport"),
        modality=classification.get("modality"),
        tier=tier or None,
        domain=classification.get("domain"),
        approved_for_event_card_discovery=approved_for_event_card_discovery,
        approved_for_matchup_provenance=approved_for_matchup_provenance,
        approved_for_results_verification=approved_for_results_verification,
        requires_secondary_confirmation=secondary_confirmation,
        queue_save_eligible=queue_save_eligible,
        official_source=bool(classification.get("official_source")),
        alert_only=alert_only,
        rejected=not approved_for_event_card_discovery,
        denial_reason=denial_reason,
    ).to_dict()


__all__ = [
    "APPROVED_COMBAT_SPORT_SOURCE_REGISTRY",
    "get_approved_combat_sport_sources",
    "classify_source_url",
    "is_approved_event_card_source",
    "requires_secondary_confirmation",
    "get_source_governance",
]
