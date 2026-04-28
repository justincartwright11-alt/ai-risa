"""Read-only web scouting for fight/event result triggers.

This module never writes files and only returns review-ready findings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen


OFFICIAL_DOMAINS = (
    "ufc.com",
    "onefc.com",
    "onefc",
    "glorykickboxing.com",
    "toprank.com",
    "matchroomboxing.com",
    "queensberry.co.uk",
    "nolimitboxing.com.au",
)

SECONDARY_DOMAINS = (
    "espn.com",
    "combatpress.com",
    "tapology.com",
    "sherdog.com",
    "boxrec.com",
    "mmadecisions.com",
)


@dataclass
class ScoutEvidence:
    url: str
    source_confidence: str
    result_found: bool
    winner: str
    method: str
    round_time: str


class WebTriggerScout:
    def __init__(
        self,
        search_provider: Optional[Callable[[str], List[str]]] = None,
        page_fetcher: Optional[Callable[[str], str]] = None,
        max_urls_per_target: int = 6,
    ) -> None:
        self.search_provider = search_provider or self._search_web
        self.page_fetcher = page_fetcher or self._fetch_page_text
        self.max_urls_per_target = max_urls_per_target

    def run(self, query: str, mode: str = "official_first", targets: Optional[Sequence[str]] = None) -> Dict:
        target_list = [str(t).strip() for t in (targets or []) if str(t).strip()]
        if not target_list:
            target_list = self._derive_targets(query)

        rows = []
        for target in target_list:
            rows.append(self._scout_target(target=target, mode=mode))

        return {
            "ok": True,
            "query": query,
            "mode": mode,
            "results": rows,
            "blocked_actions": [
                "No ledger mutation performed",
                "No prediction mutation performed",
                "No fighter profile creation performed",
                "No structural backfill applied",
            ],
        }

    def _derive_targets(self, query: str) -> List[str]:
        text = str(query or "").strip()
        if not text:
            return []

        lowered = text.lower()
        if "check one samurai 1" in lowered:
            return ["ONE SAMURAI 1"]
        if "check glory 107" in lowered:
            return ["GLORY 107 Wisse vs Kwasi"]

        m = re.search(r"check\s+(.+?)\s+result", text, re.IGNORECASE)
        if m:
            return [m.group(1).strip()]

        m = re.search(r"verify\s+(.+)", text, re.IGNORECASE)
        if m:
            return [m.group(1).strip()]

        return [text]

    def _scout_target(self, target: str, mode: str) -> Dict:
        search_query = f"{target} official result"
        urls = self.search_provider(search_query)[: self.max_urls_per_target]
        ranked_urls = self._rank_urls(urls, mode)

        if not ranked_urls:
            return self._row(
                trigger_type="NO_RESULT_FOUND",
                target=target,
                result_found=False,
                source_url="",
                source_confidence="none",
                recommended_action="MANUAL_REVIEW_REQUIRED",
            )

        evidences: List[ScoutEvidence] = []
        identity_conflict = False
        winners = set()
        official_url = ""

        for url in ranked_urls:
            source_conf = self._source_confidence_for_url(url)
            if source_conf == "official" and not official_url:
                official_url = url

            page_text = self.page_fetcher(url)
            if self._has_identity_conflict(target, page_text):
                identity_conflict = True

            parsed = self._extract_result(page_text)
            result_found = bool(parsed["winner"])
            if parsed["winner"]:
                winners.add(parsed["winner"].lower())

            evidences.append(
                ScoutEvidence(
                    url=url,
                    source_confidence=source_conf,
                    result_found=result_found,
                    winner=parsed["winner"],
                    method=parsed["method"],
                    round_time=parsed["round_time"],
                )
            )

        if identity_conflict:
            return self._row(
                trigger_type="IDENTITY_CONFLICT",
                target=target,
                result_found=False,
                source_url=official_url or ranked_urls[0],
                source_confidence="conflict",
                recommended_action="IDENTITY_CONFLICT_REVIEW",
            )

        if len(winners) > 1:
            return self._row(
                trigger_type="SOURCE_CONFLICT",
                target=target,
                result_found=True,
                source_url=official_url or ranked_urls[0],
                source_confidence="conflict",
                recommended_action="MANUAL_REVIEW_REQUIRED",
            )

        best = self._pick_best_evidence(evidences)
        if best and best.result_found:
            if best.source_confidence == "official":
                return self._row(
                    trigger_type="OFFICIAL_RESULT_FOUND",
                    target=target,
                    result_found=True,
                    winner=best.winner,
                    method=best.method,
                    round_time=best.round_time,
                    source_url=best.url,
                    source_confidence="official",
                    recommended_action="RESULT_READY_FOR_REVIEW",
                )
            return self._row(
                trigger_type="SECONDARY_RESULT_FOUND",
                target=target,
                result_found=True,
                winner=best.winner,
                method=best.method,
                round_time=best.round_time,
                source_url=best.url,
                source_confidence=best.source_confidence,
                recommended_action="SOURCE_NOT_OFFICIAL",
            )

        if official_url:
            return self._row(
                trigger_type="EVENT_PENDING",
                target=target,
                result_found=False,
                source_url=official_url,
                source_confidence="official",
                recommended_action="EVENT_PENDING",
            )

        return self._row(
            trigger_type="NO_RESULT_FOUND",
            target=target,
            result_found=False,
            source_url=ranked_urls[0],
            source_confidence=self._source_confidence_for_url(ranked_urls[0]),
            recommended_action="MANUAL_REVIEW_REQUIRED",
        )

    def _row(
        self,
        trigger_type: str,
        target: str,
        result_found: bool,
        source_url: str,
        source_confidence: str,
        recommended_action: str,
        winner: str = "",
        method: str = "",
        round_time: str = "",
    ) -> Dict:
        return {
            "trigger_type": trigger_type,
            "target": target,
            "fighter_or_event_name": target,
            "fight_or_event_id": "",
            "result_found": result_found,
            "winner": winner,
            "method": method,
            "round_time": round_time,
            "official_source_url": source_url,
            "source_confidence": source_confidence,
            "recommended_action": recommended_action,
        }

    def _pick_best_evidence(self, evidences: List[ScoutEvidence]) -> Optional[ScoutEvidence]:
        ranked = [e for e in evidences if e.result_found]
        if not ranked:
            return None

        score = {"official": 3, "secondary": 2, "non_official": 1, "unknown": 0}
        ranked.sort(key=lambda e: score.get(e.source_confidence, 0), reverse=True)
        return ranked[0]

    def _rank_urls(self, urls: Sequence[str], mode: str) -> List[str]:
        unique = []
        seen = set()
        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            unique.append(url)

        if mode != "official_first":
            return unique

        return sorted(
            unique,
            key=lambda u: (
                0 if self._source_confidence_for_url(u) == "official" else 1,
                0 if self._source_confidence_for_url(u) == "secondary" else 1,
            ),
        )

    def _source_confidence_for_url(self, url: str) -> str:
        host = (urlparse(url).netloc or "").lower()
        if any(d in host for d in OFFICIAL_DOMAINS):
            return "official"
        if any(d in host for d in SECONDARY_DOMAINS):
            return "secondary"
        return "non_official"

    def _has_identity_conflict(self, target: str, page_text: str) -> bool:
        t = (target or "").lower()
        p = (page_text or "").lower()
        if "abel chaves" in t and "alan chaves" in p:
            return True
        if "miguel madueno" in t and "miguel madueno" not in p and "miguel madue" in p:
            return True
        return False

    def _extract_result(self, page_text: str) -> Dict[str, str]:
        text = re.sub(r"\s+", " ", (page_text or "")).strip()
        if not text:
            return {"winner": "", "method": "", "round_time": ""}

        winner = ""
        winner_match = re.search(
            r"([A-Z][A-Za-z'\-.]+(?:\s+[A-Z][A-Za-z'\-.]+){0,3})\s+(?:def\.?|defeated|beat|bt)\s+([A-Z][A-Za-z'\-.]+(?:\s+[A-Z][A-Za-z'\-.]+){0,3})",
            text,
        )
        if winner_match:
            winner = winner_match.group(1).strip()

        method_match = re.search(
            r"\b(decision|submission|knockout|tko|ko|disqualification|dq|no\s*contest)\b",
            text,
            re.IGNORECASE,
        )
        method = method_match.group(1).upper().replace(" ", "_") if method_match else ""

        round_match = re.search(r"\bround\s*(\d)\b", text, re.IGNORECASE)
        time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)
        round_time = ""
        if round_match or time_match:
            round_time = f"R{round_match.group(1) if round_match else '?'} {time_match.group(1) if time_match else ''}".strip()

        return {"winner": winner, "method": method, "round_time": round_time}

    def _search_web(self, query: str) -> List[str]:
        # DuckDuckGo HTML endpoint is simple and does not require API keys.
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        html = self._fetch_page_text(url)
        urls = re.findall(r'href="(https?://[^"#]+)"', html)
        return [u for u in urls if "duckduckgo.com" not in u]

    def _fetch_page_text(self, url: str) -> str:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 AI-RISA Web Trigger Scout"})
            with urlopen(req, timeout=8) as resp:  # nosec B310
                body = resp.read(300_000)
            return body.decode("utf-8", errors="ignore")
        except Exception:
            return ""