from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from time import monotonic
from typing import Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


TIER_A0_HOSTS = {
    "ufc.com",
    "www.ufc.com",
    "onefc.com",
    "www.onefc.com",
    "onechampionship.com",
    "www.onechampionship.com",
    "glorykickboxing.com",
    "www.glorykickboxing.com",
    "toprank.com",
    "www.toprank.com",
    "matchroomboxing.com",
    "www.matchroomboxing.com",
    "queensberry.co.uk",
    "www.queensberry.co.uk",
    "nolimitboxing.com.au",
    "www.nolimitboxing.com.au",
}

TIER_A1_HOSTS = {
    "results.ufc.com",
    "m.ufc.com",
    "news.ufc.com",
    "watch.onefc.com",
}

TIER_B_HOSTS = {
    "espn.com",
    "www.espn.com",
    "tapology.com",
    "www.tapology.com",
    "sherdog.com",
    "www.sherdog.com",
    "boxrec.com",
    "www.boxrec.com",
    "mmadecisions.com",
    "www.mmadecisions.com",
}

SHORTENER_HOSTS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "ow.ly",
    "buff.ly",
    "lnk.to",
    "linktr.ee",
    "goo.gl",
}

OPAQUE_REDIRECT_HOSTS = {
    "l.facebook.com",
    "lm.facebook.com",
    "out.reddit.com",
}

DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
WINNER_RE = re.compile(
    r"([A-Z][A-Za-z'\-.]+(?:\s+[A-Z][A-Za-z'\-.]+){0,3})\s+(?:def\.?|defeated|beat|bt)\s+([A-Z][A-Za-z'\-.]+(?:\s+[A-Z][A-Za-z'\-.]+){0,3})"
)
METHOD_RE = re.compile(r"\b(decision|submission|knockout|tko|ko|disqualification|dq|no\s*contest)\b", re.IGNORECASE)
ROUND_RE = re.compile(r"\bround\s*(\d)\b", re.IGNORECASE)
TIME_RE = re.compile(r"\b(\d{1,2}:\d{2})\b")


class OfficialSourceLookupProvider:
    def __init__(
        self,
        search_provider: Optional[Callable[[str], List[str]]] = None,
        fetch_provider: Optional[Callable[[str, int], Dict[str, str]]] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.search_provider = search_provider or self._search_urls
        self.fetch_provider = fetch_provider or self._fetch_url
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def run_preview_lookup(
        self,
        selected_key: str,
        selected_row: Dict,
        timeout_budget_seconds: int = 20,
        per_source_timeout_seconds: int = 6,
        auto_retry_count: int = 0,
    ) -> Dict:
        fight_name = str(selected_row.get("fight_name") or "").strip()
        query = f"{fight_name} official result".strip()

        result = {
            "provider_attempted": False,
            "external_lookup_performed": False,
            "source_citation": None,
            "manual_review_required": True,
            "reason_code": "no_acceptable_official_source_found",
            "attempted_sources": [],
            "timeout_budget_seconds": int(timeout_budget_seconds),
            "per_source_timeout_seconds": int(per_source_timeout_seconds),
            "auto_retry_count": int(auto_retry_count),
        }

        started = monotonic()
        urls = self.search_provider(query)
        ranked_urls = self._rank_urls(urls)

        if not ranked_urls:
            result["provider_attempted"] = True
            if urls:
                result["reason_code"] = "source_url_not_allowed"
            return result

        evidences = []
        for url in ranked_urls:
            if monotonic() - started > timeout_budget_seconds:
                result["provider_attempted"] = True
                result["reason_code"] = "timeout_budget_exceeded"
                return result

            source_tier = self._classify_host(url)
            result["attempted_sources"].append(url)
            if source_tier == "denied":
                result["provider_attempted"] = True
                result["reason_code"] = "source_url_not_allowed"
                continue

            result["provider_attempted"] = True
            try:
                fetched = self.fetch_provider(url, per_source_timeout_seconds)
            except TimeoutError:
                result["reason_code"] = "timeout_budget_exceeded"
                return result
            except Exception:
                continue

            result["external_lookup_performed"] = True
            final_url = str(fetched.get("final_url") or url)
            final_tier = self._classify_host(final_url)
            if final_tier == "denied":
                result["reason_code"] = "publisher_host_mismatch"
                continue

            citation = self._extract_citation(selected_key, selected_row, fetched, final_url, final_tier)
            validation = self._validate_citation(citation)
            citation["confidence_score"] = validation["confidence_score"]

            if validation["reason_code"] == "identity_conflict":
                result["source_citation"] = citation
                result["reason_code"] = "identity_conflict"
                return result
            if validation["reason_code"] == "stale_source_date":
                result["source_citation"] = citation
                result["reason_code"] = "stale_source_date"
                return result
            if validation["reason_code"] == "citation_incomplete":
                result["source_citation"] = citation
                result["reason_code"] = "citation_incomplete"
                return result

            evidences.append({
                "citation": citation,
                "validation": validation,
            })

        return self._finalize_evidence(result, evidences)

    def _finalize_evidence(self, result: Dict, evidences: List[Dict]) -> Dict:
        if not evidences:
            if result["reason_code"] not in {
                "timeout_budget_exceeded",
                "publisher_host_mismatch",
                "identity_conflict",
                "stale_source_date",
                "citation_incomplete",
            }:
                result["reason_code"] = "no_acceptable_official_source_found"
            return result

        top_tier_rank = {"tier_a0": 3, "tier_a1": 2, "tier_b": 1}
        evidences.sort(key=lambda e: top_tier_rank.get(e["citation"].get("source_confidence"), 0), reverse=True)
        best = evidences[0]
        best_tier = best["citation"].get("source_confidence")

        same_tier = [e for e in evidences if e["citation"].get("source_confidence") == best_tier]
        winners_same_tier = {
            str(e["citation"].get("extracted_winner") or "").strip().lower()
            for e in same_tier
            if str(e["citation"].get("extracted_winner") or "").strip()
        }
        if len(winners_same_tier) > 1:
            result["source_citation"] = {
                **best["citation"],
                "source_confidence": "conflict",
            }
            result["reason_code"] = "source_conflict_same_tier"
            return result

        winners_all = {
            str(e["citation"].get("extracted_winner") or "").strip().lower()
            for e in evidences
            if str(e["citation"].get("extracted_winner") or "").strip()
        }
        if len(winners_all) > 1:
            result["source_citation"] = {
                **best["citation"],
                "source_confidence": "conflict",
            }
            result["reason_code"] = "source_conflict"
            return result

        result["source_citation"] = best["citation"]

        if best_tier == "tier_b":
            result["reason_code"] = "tier_b_without_corroboration"
            return result

        if best["validation"].get("confidence_score", 0.0) < 0.70:
            result["reason_code"] = "confidence_below_threshold"
            return result

        result["manual_review_required"] = False
        result["reason_code"] = "accepted_preview"
        return result

    def _rank_urls(self, urls: List[str]) -> List[str]:
        unique = []
        seen = set()
        for url in urls or []:
            token = str(url or "").strip()
            if not token or token in seen:
                continue
            seen.add(token)
            unique.append(token)

        def rank(url: str) -> int:
            tier = self._classify_host(url)
            return {"tier_a0": 3, "tier_a1": 2, "tier_b": 1}.get(tier, 0)

        ranked = sorted(unique, key=rank, reverse=True)
        # 3 tier-A + optional 2 tier-B max
        tier_a = [u for u in ranked if self._classify_host(u) in {"tier_a0", "tier_a1"}][:3]
        tier_b = [u for u in ranked if self._classify_host(u) == "tier_b"][:2]
        return tier_a + tier_b

    def _classify_host(self, url: str) -> str:
        try:
            parsed = urlparse(str(url or "").strip())
        except Exception:
            return "denied"

        host = (parsed.netloc or "").strip().lower()
        if ":" in host:
            host = host.split(":", 1)[0]

        if parsed.scheme.lower() != "https" or not host:
            return "denied"
        if host in SHORTENER_HOSTS:
            return "denied"
        if host in OPAQUE_REDIRECT_HOSTS:
            return "denied"
        if host in TIER_A0_HOSTS:
            return "tier_a0"
        if host in TIER_A1_HOSTS:
            return "tier_a1"
        if host in TIER_B_HOSTS:
            return "tier_b"
        return "denied"

    def _extract_citation(
        self,
        selected_key: str,
        selected_row: Dict,
        fetched: Dict[str, str],
        final_url: str,
        source_confidence: str,
    ) -> Dict:
        html_text = str(fetched.get("html") or "")
        plain_text = self._strip_html(html_text)
        title = str(fetched.get("title") or self._extract_title(html_text) or "").strip()
        source_date = str(fetched.get("source_date") or self._extract_date(html_text, plain_text) or "").strip()
        winner, method, round_time = self._extract_result_fields(plain_text)
        publisher_host = (urlparse(final_url).netloc or "").lower().split(":", 1)[0]

        citation = {
            "source_url": final_url,
            "source_title": title,
            "source_date": source_date,
            "publisher_host": publisher_host,
            "source_confidence": source_confidence,
            "confidence_score": self._confidence_score(source_confidence),
            "citation_fingerprint": self._build_fingerprint(
                selected_key,
                final_url,
                title,
                source_date,
                winner,
                method,
                round_time,
            ),
            "extracted_winner": winner,
            "method": method or None,
            "round_time": round_time or None,
            "identity_matches_selected_row": self._identity_matches(selected_row, plain_text),
        }
        return citation

    def _validate_citation(self, citation: Dict) -> Dict:
        required_fields = ["source_url", "source_title", "source_date", "publisher_host", "extracted_winner"]
        missing = [f for f in required_fields if not str(citation.get(f) or "").strip()]
        if missing:
            return {"reason_code": "citation_incomplete", "confidence_score": citation.get("confidence_score", 0.0)}

        tier = citation.get("source_confidence")
        if tier not in {"tier_a0", "tier_a1", "tier_b"}:
            return {"reason_code": "source_url_not_allowed", "confidence_score": 0.0}

        parsed_host = (urlparse(str(citation.get("source_url") or "")).netloc or "").lower().split(":", 1)[0]
        if parsed_host != str(citation.get("publisher_host") or "").lower():
            return {"reason_code": "publisher_host_mismatch", "confidence_score": citation.get("confidence_score", 0.0)}

        if not citation.get("identity_matches_selected_row"):
            return {"reason_code": "identity_conflict", "confidence_score": citation.get("confidence_score", 0.0)}

        if self._is_stale_date(str(citation.get("source_date") or "")):
            return {"reason_code": "stale_source_date", "confidence_score": citation.get("confidence_score", 0.0)}

        return {"reason_code": "accepted_preview", "confidence_score": citation.get("confidence_score", 0.0)}

    def _confidence_score(self, source_confidence: str) -> float:
        return {
            "tier_a0": 0.85,
            "tier_a1": 0.72,
            "tier_b": 0.55,
            "conflict": 0.0,
            "none": 0.0,
        }.get(str(source_confidence or ""), 0.0)

    def _build_fingerprint(
        self,
        selected_key: str,
        source_url: str,
        source_title: str,
        source_date: str,
        winner: str,
        method: str,
        round_time: str,
    ) -> str:
        token = "|".join([
            str(selected_key or "").strip(),
            str(source_url or "").strip(),
            str(source_title or "").strip(),
            str(source_date or "").strip(),
            str(winner or "").strip(),
            str(method or "").strip(),
            str(round_time or "").strip(),
        ])
        return hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]

    def _identity_matches(self, selected_row: Dict, page_text: str) -> bool:
        fight_name = str(selected_row.get("fight_name") or "").strip()
        if not fight_name:
            return False

        low_page = str(page_text or "").lower()
        if " vs " in fight_name.lower():
            left, right = [p.strip().lower() for p in fight_name.lower().split(" vs ", 1)]
            return bool(left and right and left in low_page and right in low_page)
        return fight_name.lower() in low_page

    def _is_stale_date(self, date_text: str) -> bool:
        try:
            date_obj = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
        except Exception:
            m = DATE_RE.search(str(date_text or ""))
            if not m:
                return True
            date_obj = datetime.fromisoformat(m.group(1) + "T00:00:00+00:00")

        now_utc = self.now_provider()
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        delta_days = abs((now_utc - date_obj.astimezone(timezone.utc)).days)
        return delta_days > 30

    def _extract_result_fields(self, text: str) -> tuple:
        winner = ""
        winner_match = WINNER_RE.search(str(text or ""))
        if winner_match:
            winner = winner_match.group(1).strip()

        method_match = METHOD_RE.search(str(text or ""))
        method = method_match.group(1).upper().replace(" ", "_") if method_match else ""

        round_match = ROUND_RE.search(str(text or ""))
        time_match = TIME_RE.search(str(text or ""))
        round_time = ""
        if round_match or time_match:
            round_time = f"R{round_match.group(1) if round_match else '?'} {time_match.group(1) if time_match else ''}".strip()

        return winner, method, round_time

    def _extract_title(self, html: str) -> str:
        m = re.search(r"<title>(.*?)</title>", str(html or ""), flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return ""
        return re.sub(r"\s+", " ", m.group(1)).strip()

    def _extract_date(self, html: str, text: str) -> str:
        meta_patterns = [
            r'property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
            r'name=["\']date["\']\s+content=["\']([^"\']+)["\']',
            r'name=["\']publishdate["\']\s+content=["\']([^"\']+)["\']',
            r'itemprop=["\']datePublished["\']\s+content=["\']([^"\']+)["\']',
        ]
        for pattern in meta_patterns:
            m = re.search(pattern, str(html or ""), flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()

        text_match = DATE_RE.search(str(text or ""))
        return text_match.group(1) if text_match else ""

    def _strip_html(self, html: str) -> str:
        text = re.sub(r"<script[\\s\\S]*?</script>", " ", str(html or ""), flags=re.IGNORECASE)
        text = re.sub(r"<style[\\s\\S]*?</style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _search_urls(self, query: str) -> List[str]:
        q = str(query or "").strip()
        if not q:
            return []
        # Standard HTML search endpoint with no retries.
        endpoint = f"https://duckduckgo.com/html/?q={q.replace(' ', '+')}"
        fetched = self._fetch_url(endpoint, 6)
        html = str(fetched.get("html") or "")
        urls = re.findall(r'href="(https?://[^"#]+)"', html)
        return [u for u in urls if "duckduckgo.com" not in u]

    def _fetch_url(self, url: str, timeout_seconds: int) -> Dict[str, str]:
        parsed = urlparse(str(url or "").strip())
        host = (parsed.netloc or "").lower()
        if host in OPAQUE_REDIRECT_HOSTS:
            query = parse_qs(parsed.query)
            redirect_target = (query.get("u") or query.get("url") or [""])[0]
            if redirect_target:
                url = redirect_target

        req = Request(str(url), headers={"User-Agent": "Mozilla/5.0 AI-RISA Official Source Provider"})
        with urlopen(req, timeout=int(timeout_seconds)) as resp:  # nosec B310
            html = resp.read(350_000).decode("utf-8", errors="ignore")
            final_url = str(resp.geturl() or url)

        return {
            "final_url": final_url,
            "title": self._extract_title(html),
            "source_date": self._extract_date(html, self._strip_html(html)),
            "html": html,
        }
