import json
import os
import re
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

AUTO_INTAKE_LOG_PATH = os.path.join(os.path.dirname(__file__), "auto_intake_log.jsonl")

BOXING_DIVISIONS = [
    "minimumweight",
    "light flyweight",
    "flyweight",
    "super flyweight",
    "bantamweight",
    "super bantamweight",
    "featherweight",
    "super featherweight",
    "lightweight",
    "super lightweight",
    "light welterweight",
    "welterweight",
    "super welterweight",
    "light middleweight",
    "middleweight",
    "super middleweight",
    "light heavyweight",
    "cruiserweight",
    "heavyweight",
]

STANCE_OPTIONS = ["orthodox", "southpaw", "switch"]

STYLE_OPTIONS = [
    "pressure fighter",
    "pressure boxer",
    "counter puncher",
    "counter striker",
    "boxer-puncher",
    "power puncher",
    "technical boxer",
    "technical kickboxer",
    "wrestler",
    "grappler",
    "kickboxer",
    "muay thai striker",
    "striker",
    "boxer",
]

SOURCE_PRIORITY = {
    "boxing": {
        "official": [
            "nolimitboxing.com.au",
            "toprank.com",
            "matchroomboxing.com",
            "premierboxingchampions.com",
            "queensberry.co.uk",
        ],
        "authority": [
            "box.live",
            "boxingscene.com",
            "fightmag.com",
            "espn.com",
            "sportingnews.com",
        ],
    },
    "mma": {
        "official": ["ufc.com", "onefc.com", "pflmma.com"],
        "authority": ["tapology.com", "sherdog.com", "espn.com"],
    },
    "kickboxing": {
        "official": ["glorykickboxing.com", "onefc.com"],
        "authority": ["beyondkick.com", "tapology.com"],
    },
    "muay thai": {
        "official": ["onefc.com", "rajadamnern.com"],
        "authority": ["beyondkick.com", "muaythaiauthority.com"],
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slugify(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"\b(jr|sr)\.\b", r"\1", text)
    text = re.sub(r"\b(ii|iii|iv|v)\.\b", r"\1", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _normalize_person_name(value: str) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    text = re.sub(r"\b(Jr|Sr)\.\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(II|III|IV|V)\.\b", r"\1", text, flags=re.IGNORECASE)
    return text.strip()


def _person_name_variants(name: str) -> List[str]:
    normalized = _normalize_person_name(name)
    variants = []
    suffix_pattern = re.compile(r"\s+(Jr\.?|Sr\.?|II|III|IV|V)$", re.IGNORECASE)
    suffixless = suffix_pattern.sub("", normalized).strip()
    for candidate in [name, normalized, normalized.replace(".", ""), suffixless, suffixless.replace(".", "")]:
        candidate = re.sub(r"\s+", " ", (candidate or "").strip())
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def _write_log(payload: Dict) -> None:
    try:
        os.makedirs(os.path.dirname(AUTO_INTAKE_LOG_PATH), exist_ok=True)
        row = dict(payload)
        row.setdefault("timestamp", _utc_now())
        with open(AUTO_INTAKE_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    except Exception:
        pass


def _get_json(url: str, timeout: int = 8) -> Optional[Dict]:
    req = Request(url, headers={"User-Agent": "AI-RISA/1.0 (operator auto-intake)"})
    with urlopen(req, timeout=timeout) as resp:  # nosec B310
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if isinstance(data, dict):
        return data
    return None


def _get_text(url: str, timeout: int = 8) -> str:
    req = Request(url, headers={"User-Agent": "AI-RISA/1.0 (operator auto-intake)"})
    with urlopen(req, timeout=timeout) as resp:  # nosec B310
        return resp.read().decode("utf-8", errors="replace")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<script.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"<style.*?</style>", " ", clean, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = unescape(clean)
    return re.sub(r"\s+", " ", clean).strip()


def _normalize_division(value: str) -> str:
    text = (value or "").strip().lower().replace("-", " ")
    if text == "light middleweight":
        return "super welterweight"
    if text == "light welterweight":
        return "super lightweight"
    return text


def _extract_keyword(blob: str, options: List[str]) -> str:
    text = (blob or "").lower()
    for item in options:
        if re.search(r"\b" + re.escape(item.lower()) + r"\b", text):
            return item
    return ""


def _extract_division(blob: str) -> str:
    return _normalize_division(_extract_keyword(blob, BOXING_DIVISIONS))


def _extract_stance(blob: str) -> str:
    return _extract_keyword(blob, STANCE_OPTIONS)


def _extract_labeled_field(blob: str, label: str, stop_labels: List[str]) -> str:
    text = re.sub(r"\s+", " ", blob or "")
    if not text:
        return ""
    stop_pattern = "|".join(re.escape(item) for item in stop_labels)
    pattern = rf"{re.escape(label)}\s+(.+?)(?=\s+(?:{stop_pattern})\b|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    value = match.group(1).strip(" :-|")
    return re.sub(r"\s+", " ", value)


def _extract_style(blob: str, sport: str) -> str:
    text = (blob or "").lower()
    style = _extract_keyword(text, STYLE_OPTIONS)
    if style:
        return style.title()
    if sport == "boxing":
        return "Boxer"
    if sport == "mma":
        return "Striker"
    if sport == "kickboxing":
        return "Kickboxer"
    if sport == "muay thai":
        return "Muay Thai Striker"
    return ""


def _normalize_sport(raw: str) -> str:
    text = (raw or "").lower()
    if "boxing" in text or "boxer" in text:
        return "boxing"
    if "mma" in text or "mixed martial" in text or "ufc" in text:
        return "mma"
    if "kickboxing" in text:
        return "kickboxing"
    if "muay" in text:
        return "muay thai"
    return "boxing"


def _wikipedia_title(query: str) -> Optional[str]:
    encoded = quote(query)
    search_url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch"
        f"&search={encoded}&limit=1&namespace=0&format=json"
    )
    req = Request(search_url, headers={"User-Agent": "AI-RISA/1.0 (operator auto-intake)"})
    with urlopen(req, timeout=8) as resp:  # nosec B310
        raw = resp.read().decode("utf-8", errors="replace")
    payload = json.loads(raw)
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return None
    title = str(payload[1][0]).strip()
    return title or None


def _search_wikipedia(name: str, sport_hint: str = "") -> Optional[Dict]:
    sport_hint = (sport_hint or "").strip().lower()
    queries = [name]
    if sport_hint == "boxing":
        queries = [f"{name} boxer", f"{name} (boxer)", name]
    elif sport_hint:
        queries = [f"{name} {sport_hint}", name]

    best = None
    for query in queries:
        title = _wikipedia_title(query)
        if not title:
            continue

        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
        summary = _get_json(summary_url)
        if not summary:
            continue

        extract = str(summary.get("extract") or "").strip()
        description = str(summary.get("description") or "").strip()
        source_url = (
            summary.get("content_urls", {})
            .get("desktop", {})
            .get("page")
            or f"https://en.wikipedia.org/wiki/{quote(title)}"
        )

        page_url = f"https://en.wikipedia.org/wiki/{quote(title)}"
        page_text = extract
        try:
            page_text = _strip_html(_get_text(page_url))
        except Exception:
            pass

        infobox_blob = f"{description} {extract} {page_text}"
        labeled_weight = _extract_labeled_field(page_text, "Weight", ["Boxing career", "Mixed martial arts career", "Kickboxing career", "Reach", "Stance", "Team"])
        labeled_stance = _extract_labeled_field(page_text, "Stance", ["Boxing record", "Mixed martial arts record", "Years active", "Team", "Trainer"])
        division = _normalize_division(labeled_weight) or _extract_division(infobox_blob)
        stance = labeled_stance.lower() or _extract_stance(infobox_blob)
        sport = _normalize_sport(infobox_blob)

        candidate = {
            "source": "wikipedia",
            "tier": "fallback",
            "title": title,
            "description": description,
            "extract": extract,
            "weight_class": division,
            "stance": stance,
            "sport": sport,
            "notes": page_text[:1200],
            "url": source_url,
        }
        if division or stance or (sport_hint and sport == sport_hint):
            return candidate
        if best is None:
            best = candidate
    return best


def _search_sportsdb(name: str) -> Optional[Dict]:
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={quote(name)}"
    payload = _get_json(url)
    if not payload:
        return None
    players = payload.get("player")
    if not isinstance(players, list) or not players:
        return None

    best = players[0] if isinstance(players[0], dict) else None
    if not best:
        return None

    return {
        "source": "thesportsdb",
        "tier": "fallback",
        "name": str(best.get("strPlayer") or "").strip(),
        "sport": str(best.get("strSport") or "").strip(),
        "style": str(best.get("strPosition") or "").strip(),
        "description": str(best.get("strDescriptionEN") or "").strip(),
        "weight_class": _normalize_division(str(best.get("strWeight") or "").strip()),
        "nationality": str(best.get("strNationality") or "").strip(),
        "birth_date": str(best.get("dateBorn") or "").strip(),
        "url": str(best.get("strWebsite") or "").strip(),
    }


def _duckduckgo_search(query: str, max_results: int = 5) -> List[Dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    html = _get_text(url, timeout=10)
    blocks = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>|<div[^>]+class="result__snippet"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
    results = []
    for idx, (href, title_html) in enumerate(blocks[:max_results]):
        final_href = href
        if "uddg=" in href:
            parsed = parse_qs(urlparse(href).query)
            final_href = unquote(parsed.get("uddg", [href])[0])
        title = _strip_html(title_html)
        snippet_parts = snippets[idx] if idx < len(snippets) else ("", "")
        snippet = _strip_html(" ".join([part for part in snippet_parts if part]))
        results.append({"url": final_href, "title": title, "snippet": snippet})
    return results


def _domain_matches(url: str, domain: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host == domain or host.endswith("." + domain)


def _search_ranked_sources(name: str, sport: str) -> List[Dict]:
    sport_key = sport if sport in SOURCE_PRIORITY else "boxing"
    config = SOURCE_PRIORITY.get(sport_key, SOURCE_PRIORITY["boxing"])
    found = []
    seen = set()
    name_variants = _person_name_variants(name)

    for tier in ["official", "authority"]:
        for domain in config[tier]:
            results = []
            for variant in name_variants:
                query_candidates = [
                    f'site:{domain} "{variant}"',
                    f'site:{domain} "{variant}" boxing',
                    f'site:{domain} {variant} boxing',
                ]
                for query in query_candidates:
                    try:
                        results = _duckduckgo_search(query, max_results=3)
                    except Exception as exc:
                        _write_log({"action": "fighter_auto_intake_search", "fighter": _slugify(name), "tier": tier, "domain": domain, "status": "error", "error": str(exc)})
                        results = []
                    if results:
                        break
                if results:
                    break

            chosen = None
            for item in results:
                if _domain_matches(item.get("url", ""), domain):
                    chosen = item
                    break
            if not chosen:
                continue

            url = chosen.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)

            try:
                page_text = _strip_html(_get_text(url, timeout=10))[:4000]
            except Exception:
                page_text = chosen.get("snippet", "")

            found.append(
                {
                    "source": domain,
                    "tier": tier,
                    "url": url,
                    "title": chosen.get("title", ""),
                    "snippet": chosen.get("snippet", ""),
                    "text": page_text,
                }
            )
            _write_log({"action": "fighter_auto_intake_search", "fighter": _slugify(name), "tier": tier, "domain": domain, "status": "selected", "url": url})
            if len(found) >= 2:
                return found
    return found


def _build_profile_facts(name_raw: str, wiki: Optional[Dict], sportsdb: Optional[Dict], ranked_sources: List[Dict]) -> Dict:
    ranked_blob = " ".join(
        [
            " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("snippet") or ""),
                    str(item.get("text") or ""),
                ]
            )
            for item in ranked_sources
        ]
    )
    wiki_blob = " ".join(
        [
            str((wiki or {}).get("title") or ""),
            str((wiki or {}).get("description") or ""),
            str((wiki or {}).get("extract") or ""),
            str((wiki or {}).get("notes") or ""),
            str((wiki or {}).get("weight_class") or ""),
            str((wiki or {}).get("stance") or ""),
        ]
    )
    sports_blob = " ".join(
        [
            str((sportsdb or {}).get("description") or ""),
            str((sportsdb or {}).get("style") or ""),
            str((sportsdb or {}).get("sport") or ""),
            str((sportsdb or {}).get("weight_class") or ""),
        ]
    )
    blob = f"{ranked_blob} {wiki_blob} {sports_blob}".strip()

    sport = _normalize_sport(
        " ".join(
            [
                str((wiki or {}).get("sport") or ""),
                str((sportsdb or {}).get("sport") or ""),
                ranked_blob,
                wiki_blob,
            ]
        )
    )
    style = ""
    sports_style = str((sportsdb or {}).get("style") or "").strip()
    if sports_style and sports_style.lower() not in {"centre-forward", "forward", "midfielder"}:
        style = sports_style
    if not style:
        style = _extract_style(blob, sport)

    stance = str((wiki or {}).get("stance") or "").strip().lower() or _extract_stance(blob)
    division = _normalize_division(str((wiki or {}).get("weight_class") or "").strip())
    if not division:
        division = _normalize_division(str((sportsdb or {}).get("weight_class") or "").strip())
    if not division:
        division = _extract_division(blob)

    full_name = str((sportsdb or {}).get("name") or (wiki or {}).get("title") or _normalize_person_name(name_raw)).strip()
    notes = str((wiki or {}).get("extract") or "").strip()
    if not notes and ranked_sources:
        notes = str(ranked_sources[0].get("snippet") or ranked_sources[0].get("text") or "").strip()
    if len(notes) > 300:
        notes = notes[:300].rsplit(" ", 1)[0] + "..."

    recent_activity = ""
    recent_candidates = re.findall(r"([^.]{0,180}(?:title|bout|fight|defend|defeated|scheduled|faces|faced|opponent|unification)[^.]{0,180})", blob, re.IGNORECASE)
    if recent_candidates:
        recent_activity = recent_candidates[0].strip()
    elif notes:
        recent_activity = notes.split(".")[0].strip()

    team = ""
    team_match = re.search(r"\b(?:team|camp)\s+([A-Z][A-Za-z0-9'\- ]{2,})", blob)
    if team_match:
        team = team_match.group(1).strip()

    sources = []
    for item in ranked_sources:
        sources.append({"source": item.get("source", ""), "tier": item.get("tier", "authority"), "url": item.get("url", "")})
    if wiki:
        sources.append({"source": "wikipedia", "tier": "fallback", "url": wiki.get("url", "")})
    if sportsdb:
        sources.append({"source": "thesportsdb", "tier": "fallback", "url": sportsdb.get("url", "")})

    return {
        "full_name": full_name,
        "sport": sport,
        "division": division,
        "stance": stance,
        "style": style,
        "recent_activity": recent_activity,
        "team": team,
        "notes": notes,
        "sources": sources,
    }


def _score_confidence(facts: Dict) -> Tuple[str, str]:
    sources = facts.get("sources") or []
    source_count = len(sources)
    tier_set = {str(item.get("tier") or "") for item in sources}
    reputable_count = sum(1 for item in sources if str(item.get("tier") or "") in {"official", "authority"})
    has_division = bool(facts.get("division"))
    has_stance = bool(facts.get("stance"))
    has_style = bool(facts.get("style"))
    sport = str(facts.get("sport") or "").lower()
    has_recent_activity = bool(facts.get("recent_activity"))

    if has_division and has_stance and source_count >= 2:
        if "official" in tier_set or "authority" in tier_set or source_count >= 2:
            return "high", "ranked combat-source evidence with division and stance"
    if sport == "boxing" and has_division and source_count >= 2 and reputable_count >= 1:
        if (has_stance and has_style) or (has_stance and has_recent_activity) or (has_style and has_recent_activity and reputable_count >= 2):
            return "high", "boxing multi-source evidence strong enough to confirm profile basics"
    if has_division and (has_stance or has_style) and source_count >= 1:
        return "medium", "partial source evidence with division plus stance/style"
    return "low", "insufficient reliable evidence for division/stance/style"


def _can_accept_without_stance(facts: Dict, confidence: str) -> bool:
    """
    Keep strict confidence gates overall, but allow intake to proceed when a
    clearly identified fighter is missing only stance and all core context is strong.
    """
    if confidence != "medium":
        return False

    has_division = bool(str(facts.get("division") or "").strip())
    has_style = bool(str(facts.get("style") or "").strip())
    has_stance = bool(str(facts.get("stance") or "").strip())
    if not has_division or not has_style or has_stance:
        return False

    full_name = str(facts.get("full_name") or "").strip()
    has_identity = len([t for t in re.split(r"\s+", full_name) if t]) >= 2
    if not has_identity:
        return False

    sport = str(facts.get("sport") or "").strip().lower()
    known_sports = {"boxing", "mma", "mixed martial arts", "kickboxing", "muay thai"}
    if sport not in known_sports:
        return False

    sources = facts.get("sources") or []
    if len(sources) < 2:
        return False

    # Require at least one source with a concrete URL to avoid weak/noisy acceptance.
    has_concrete_source = any(str(item.get("url") or "").strip() for item in sources)
    has_recent_context = bool(str(facts.get("recent_activity") or "").strip())
    return has_concrete_source and (has_style or has_recent_context)


def _enrichment_baseline(style: str, stance: str) -> Dict:
    style_l = (style or "").lower()
    base = {
        "cardio_endurance": 0.63,
        "recovery_quality": 0.62,
        "output_decay": 0.56,
        "late_fight_fade": 0.60,
        "attrition_sensitivity": 0.58,
        "durability": 0.70,
        "knockdown_susceptibility": 0.54,
        "defensive_breakdown_tendency": 0.58,
        "panic_collapse_sensitivity": 0.56,
    }
    if "pressure" in style_l or "power" in style_l:
        base["output_decay"] = 0.59
        base["late_fight_fade"] = 0.63
        base["durability"] = 0.72
    if "grappler" in style_l or "wrestler" in style_l:
        base["cardio_endurance"] = 0.66
        base["recovery_quality"] = 0.64
        base["output_decay"] = 0.54
    if "counter" in style_l or "technical" in style_l:
        base["output_decay"] = 0.52
        base["defensive_breakdown_tendency"] = 0.54
    if (stance or "").lower() == "southpaw":
        base["defensive_breakdown_tendency"] = max(0.50, base["defensive_breakdown_tendency"] - 0.02)
    return base


def _canonical_profile_path(project_root: str, slug: str) -> str:
    return os.path.join(project_root, "fighters", f"fighter_{slug}.json")


def _legacy_profile_path(project_root: str, slug: str) -> str:
    return os.path.join(project_root, "fighters", f"{slug}.json")


def _load_json(path: str, fallback):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception:
        pass
    return fallback


def _save_json(path: str, payload: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _cleanup_duplicate_profile_files(project_root: str, slug: str) -> None:
    canonical = _canonical_profile_path(project_root, slug)
    legacy = _legacy_profile_path(project_root, slug)
    if os.path.exists(canonical) and os.path.exists(legacy):
        try:
            os.remove(legacy)
            _write_log({"action": "fighter_auto_intake_cleanup", "fighter": slug, "removed": legacy})
        except Exception:
            pass


def _read_existing_profile(project_root: str, slug: str) -> Dict:
    for path in (_canonical_profile_path(project_root, slug), _legacy_profile_path(project_root, slug)):
        payload = _load_json(path, None)
        if isinstance(payload, dict):
            return payload
    return {}


def _needs_profile_refresh(existing_profile: Dict, sport_hint: str) -> bool:
    if not existing_profile:
        return True
    style = str(existing_profile.get("style") or "").strip().lower()
    stance = str(existing_profile.get("stance") or "").strip().lower()
    division = str(existing_profile.get("weight_class") or "").strip().lower()
    sport = str(existing_profile.get("sport") or "").strip().lower()
    source_summary = existing_profile.get("source_summary")

    invalid_style = style in {"", "centre-forward", "forward", "midfielder", "unknown"}
    missing_core = not division or not stance
    wrong_sport = sport_hint == "boxing" and sport not in {"", "boxing"}
    weak_sources = not source_summary
    return invalid_style or missing_core or wrong_sport or weak_sources


def _profile_exists(project_root: str, slug: str) -> bool:
    canonical = _canonical_profile_path(project_root, slug)
    legacy = _legacy_profile_path(project_root, slug)
    return os.path.exists(canonical) or os.path.exists(legacy)


def _build_profile_payload(slug: str, facts: Dict, confidence: str, reason: str) -> Dict:
    return {
        "fighter_id": f"fighter_{slug}",
        "name": facts.get("full_name") or slug.replace("_", " ").title(),
        "sport": facts.get("sport") or "boxing",
        "weight_class": facts.get("division") or "",
        "stance": str(facts.get("stance") or "Unknown").lower(),
        "style": facts.get("style") or "",
        "team": facts.get("team") or "",
        "notes": facts.get("notes") or "",
        "source": "auto_web_research",
        "source_confidence": confidence,
        "source_confidence_reason": reason,
        "source_summary": [
            {
                "source": item.get("source", ""),
                "tier": item.get("tier", "fallback"),
                "url": item.get("url", ""),
            }
            for item in facts.get("sources", [])
        ],
        "source_urls": [item.get("url", "") for item in facts.get("sources", []) if item.get("url")],
        "recent_activity": facts.get("recent_activity") or "",
    }


def _update_enrichment(project_root: str, slug: str, facts: Dict, confidence: str, force: bool = False) -> bool:
    enrichment_path = os.path.join(project_root, "fighters", "manual_profile_enrichment.json")
    payload = _load_json(enrichment_path, {})
    if not isinstance(payload, dict):
        payload = {}

    if not force and slug in payload and isinstance(payload[slug], dict):
        return False

    draft = _enrichment_baseline(facts.get("style", ""), facts.get("stance", ""))
    draft["style"] = facts.get("style") or "Generalist"
    draft["stance"] = facts.get("stance") or "Unknown"
    draft["source"] = "auto_intake"
    draft["source_confidence"] = confidence
    draft["source_summary"] = [
        {
            "source": item.get("source", ""),
            "tier": item.get("tier", "fallback"),
        }
        for item in facts.get("sources", [])
    ]
    if facts.get("notes"):
        draft["notes"] = facts["notes"]

    payload[slug] = draft
    _save_json(enrichment_path, payload)
    return True


def auto_intake_missing_fighters(missing_requests: List[Dict], project_root: str) -> Dict:
    outcomes = []
    for item in missing_requests:
        slug = _slugify(item.get("slug") or item.get("name") or "")
        name = _normalize_person_name(str(item.get("name") or slug.replace("_", " ").title()).strip())
        sport_hint = str(item.get("sport") or "boxing").strip().lower() or "boxing"
        if not slug:
            continue

        _cleanup_duplicate_profile_files(project_root, slug)

        existing_profile = _read_existing_profile(project_root, slug)
        refresh_existing = _needs_profile_refresh(existing_profile, sport_hint)

        if _profile_exists(project_root, slug) and not refresh_existing:
            wrote_enrichment = _update_enrichment(project_root, slug, {"style": existing_profile.get("style") or "Generalist", "stance": existing_profile.get("stance") or ""}, str(existing_profile.get("source_confidence") or "medium"))
            outcomes.append(
                {
                    "slug": slug,
                    "name": name,
                    "status": "existing",
                    "confidence": "high",
                    "reason": "profile already exists locally",
                    "profile_written": False,
                    "enrichment_written": wrote_enrichment,
                    "sources": [],
                    "source_summary": "local profile cache",
                }
            )
            _write_log({"action": "fighter_auto_intake", "fighter": slug, "status": "existing"})
            continue

        ranked_sources = []
        wiki = None
        sportsdb = None

        try:
            ranked_sources = _search_ranked_sources(name, sport_hint)
        except Exception as exc:
            _write_log({"action": "fighter_auto_intake_source", "fighter": slug, "source": "ranked_search", "status": "error", "error": str(exc)})

        try:
            wiki = _search_wikipedia(name, sport_hint=sport_hint)
        except Exception as exc:
            _write_log({"action": "fighter_auto_intake_source", "fighter": slug, "source": "wikipedia", "status": "error", "error": str(exc)})

        try:
            sportsdb = _search_sportsdb(name)
        except Exception as exc:
            _write_log({"action": "fighter_auto_intake_source", "fighter": slug, "source": "thesportsdb", "status": "error", "error": str(exc)})

        facts = _build_profile_facts(name, wiki, sportsdb, ranked_sources)
        confidence, reason = _score_confidence(facts)
        missing_fields = [field for field in ["division", "stance", "style"] if not facts.get(field)]
        allow_without_stance = _can_accept_without_stance(facts, confidence)
        if allow_without_stance and missing_fields == ["stance"]:
            reason = f"{reason}; accepted with fallback stance=Unknown (identity/sport/style evidence strong)"

        is_sufficient = confidence == "high" or (allow_without_stance and missing_fields == ["stance"])

        profile_written = False
        enrichment_written = False
        if is_sufficient:
            if not facts.get("stance"):
                facts = dict(facts)
                facts["stance"] = "Unknown"
            profile = _build_profile_payload(slug, facts, confidence, reason)
            canonical_path = _canonical_profile_path(project_root, slug)
            _save_json(canonical_path, profile)
            _cleanup_duplicate_profile_files(project_root, slug)
            profile_written = True
            enrichment_written = _update_enrichment(project_root, slug, facts, confidence, force=refresh_existing)

        source_summary = ", ".join(
            [
                f"{item.get('tier', 'fallback')}:{item.get('source', 'unknown')}"
                for item in facts.get("sources", [])
            ]
        ) or "no reliable sources"

        outcome = {
            "slug": slug,
            "name": name,
            "status": "created" if profile_written else "blocked",
            "confidence": confidence,
            "reason": reason,
            "profile_written": profile_written,
            "enrichment_written": enrichment_written,
            "sources": facts.get("sources", []),
            "source_summary": source_summary,
            "missing_fields": missing_fields,
        }
        outcomes.append(outcome)

        _write_log(
            {
                "action": "fighter_auto_intake",
                "fighter": slug,
                "status": outcome["status"],
                "confidence": confidence,
                "reason": reason,
                "sources": [s.get("source") for s in outcome["sources"]],
                "source_summary": source_summary,
                "profile_written": profile_written,
                "enrichment_written": enrichment_written,
            }
        )

    blocked = [o for o in outcomes if o.get("status") == "blocked"]
    created = [o for o in outcomes if o.get("status") == "created"]
    return {
        "ok": len(blocked) == 0,
        "created": created,
        "blocked": blocked,
        "outcomes": outcomes,
    }
