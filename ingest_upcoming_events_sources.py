def fetch_and_parse_lfa_events(session, diagnostics):
    """
    Robust LFA event extraction: index-first, month header, date, linked title, location.
    Returns (events, diagnostics). Diagnostics is a list.
    """
    LFA_BASE_URL = 'https://www.lfa.com'
    LFA_EVENTS_URL = 'https://www.lfa.com/events/'
    from bs4 import BeautifulSoup
    from dateutil import parser as date_parser
    from datetime import datetime, timezone
    import re
    def now_iso():
        return datetime.now(timezone.utc).isoformat()
    adapter_diag = {
        'source': 'lfa',
        'adapter_entry': now_iso(),
        'source_url': LFA_EVENTS_URL,
        'status': None,
        'detail': {},
    }
    try:
        resp = session.get(LFA_EVENTS_URL, timeout=15)
        body = resp.text
        adapter_diag['fetch_status_code'] = resp.status_code
        adapter_diag['fetch_length'] = len(body)
        if resp.status_code != 200 or len(body) < 2000:
            adapter_diag['status'] = 'fetch_failed'
            diagnostics.append(adapter_diag)
            print('[LFA FETCH] Fetch failed or body too small')
            return [], diagnostics
    except Exception as e:
        adapter_diag['status'] = 'fetch_failed'
        adapter_diag['exception'] = str(e)
        diagnostics.append(adapter_diag)
        print(f'[LFA FETCH] Exception: {e}')
        return [], diagnostics
    soup = BeautifulSoup(body, 'html.parser')
    retained_records = []
    current_month = None
    current_year = None
    elements = list(soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'li', 'div']))
    i = 0
    while i < len(elements):
        el = elements[i]
        # Detect month/year header (e.g., 'APRIL 2026')
        if el.name in ['h2', 'h3', 'h4', 'h5', 'h6'] and el.text.strip().upper().endswith('2026'):
            m = re.match(r'(\w+)\s+(\d{4})', el.text.strip(), re.I)
            if m:
                current_month = m.group(1).title()
                current_year = m.group(2)
        # Detect event heading (e.g., '### [LFA 230 – BARTLING vs. CLEVELAND](...)')
        if el.name in ['h3', 'h4', 'h5', 'h6']:
            a = el.find('a')
            if a and a.text.strip() and a.has_attr('href'):
                event_name = a.text.strip()
                detail_url = a['href']
                if detail_url.startswith('/'):
                    detail_url = LFA_BASE_URL + detail_url
                elif detail_url.startswith('http'):
                    detail_url = detail_url
                detail_url = detail_url.split('?')[0].split('#')[0].rstrip('/')
                # Look back for date (e.g., 'April 3')
                date_str = None
                for j in range(i-1, max(i-4, -1), -1):
                    prev = elements[j]
                    t = prev.text.strip()
                    if re.match(r'^[A-Za-z]+\s+\d{1,2}$', t):
                        date_str = t
                        break
                # Compose full date
                date_normalized = None
                date_raw = date_str
                if date_str and current_month and current_year:
                    try:
                        dt = date_parser.parse(f"{date_str} {current_year}")
                        date_normalized = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
                # Look ahead for location line (next non-empty text)
                venue = None
                city = None
                region = None
                country = None
                for k in range(i+1, min(i+4, len(elements))):
                    next_el = elements[k]
                    loc_line = next_el.text.strip()
                    if loc_line and not next_el.find('a') and not re.match(r'^[A-Za-z]+\s+\d{1,2}$', loc_line):
                        venue = loc_line
                        break
                if event_name and date_normalized and detail_url:
                    record = {
                        'promotion': 'LFA',
                        'event_name': event_name,
                        'event_name_source': 'index_linked_heading',
                        'date': date_normalized,
                        'date_source': 'index_visible',
                        'date_raw': date_raw,
                        'city': city,
                        'region': region,
                        'country': country,
                        'venue': venue,
                        'bouts': [],
                        'source_url': detail_url,
                        'source_type': 'official_events_index',
                        'source_confidence': 95,
                        'last_seen_at': now_iso(),
                    }
                    if len(retained_records) < 5:
                        print(f"[LFA RETAINED] event_name={event_name!r} date_raw={date_raw!r} date_normalized={date_normalized!r} detail_url={detail_url!r} venue={venue!r}")
                    retained_records.append(record)
        i += 1
    # Deduplicate by promotion+event_name+date
    deduped = {}
    for rec in retained_records:
        key = f"{rec.get('promotion','').strip().lower()}__{(rec.get('event_name') or '').strip().lower()}__{rec.get('date') or ''}"
        if key and key not in deduped:
            deduped[key] = rec
    unique_records = list(deduped.values())
    adapter_diag['detail']['attempted'] = len(retained_records)
    adapter_diag['detail']['records_built'] = len(unique_records)
    adapter_diag['final_records'] = len(unique_records)
    if unique_records:
        adapter_diag['status'] = 'ok'
    else:
        adapter_diag['status'] = 'no_valid_events'
    diagnostics.append(adapter_diag)
    print(f"[LFA ADAPTER] Final diagnostics: {adapter_diag}")
    return unique_records, diagnostics
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from datetime import datetime, timezone

def fetch_and_parse_ares_events(session, diagnostics):
    """
    Strict zipped-only ARES FC event extraction. No fallback. Diagnostics always appended.
    """
    ARES_EVENTS_URL = 'https://www.aresfighting.com/events/'
    diag = {
        'source': 'ares',
        'adapter_entry': datetime.now(timezone.utc).isoformat(),
        'source_url': ARES_EVENTS_URL,
        'status': None,
        'detail': {},
    }
    try:
        resp = session.get(ARES_EVENTS_URL, timeout=15)
        body = resp.text
        diag['fetch_status_code'] = resp.status_code
        diag['fetch_length'] = len(body)
        if resp.status_code != 200 or len(body) < 2000:
            diag['status'] = 'fetch_failed'
            diagnostics.append(diag)
            print('[ARES FETCH] Fetch failed or body too small')
            return [], diagnostics
    except Exception as e:
        diag['status'] = 'fetch_failed'
        diag['exception'] = str(e)
        diagnostics.append(diag)
        print(f'[ARES FETCH] Exception: {e}')
        return [], diagnostics
    soup = BeautifulSoup(body, 'html.parser')
    # 2. Extract fight-card anchors in DOM order
    anchors = [a for a in soup.find_all('a') if a.text and 'fight card' in a.text.lower()]
    # 3. Extract all DD/MM/YYYY dates in DOM order
    dates = []
    for el in soup.find_all(text=True):
        t = el.strip()
        if re.match(r'^\d{2}/\d{2}/\d{4}$', t):
            dates.append(t)
    # 4. Extract all ARES titles in DOM order
    titles_raw = []
    for el in soup.find_all(text=True):
        t = el.strip()
        if re.match(r'^ARES\s*\d+$', t, re.I) or re.match(r'^ARES\s+[A-Za-z]+', t, re.I):
            titles_raw.append(t)
    # 5. Collapse consecutive duplicate titles
    titles = []
    prev = None
    for t in titles_raw:
        if t != prev:
            titles.append(t)
        prev = t
    print(f"[ARES AUDIT] anchors={{}} dates={{}} collapsed_titles={{}}".format(len(anchors), len(dates), len(titles)))
    print(f"[ARES AUDIT] anchors={{}}".format(anchors))
    print(f"[ARES AUDIT] dates={{}}".format(dates))
    print(f"[ARES AUDIT] titles_raw={{}}".format(titles_raw))
    print(f"[ARES AUDIT] titles={{}}".format(titles))
    # 6. If counts align, strict zip only
    if len(anchors) == len(dates) == len(titles) and len(anchors) > 0:
        print(f"[ARES AUDIT] Using strict zipped correlation: {{}} events".format(len(anchors)))
        zipped = list(zip(titles, dates, anchors))
        seen_pairs = set()
        url_map = {}
        records = []
        for idx, (event_name, date_raw, anchor) in enumerate(zipped):
            href = anchor.get('href')
            source_url = urljoin(ARES_EVENTS_URL, href) if href else None
            try:
                date_normalized = date_parser.parse(date_raw, dayfirst=True).strftime('%Y-%m-%d')
            except Exception:
                date_normalized = None
            pair = (event_name, date_normalized)
            # Guard: abort if duplicate event_name+date for different URLs
            if pair in url_map and url_map[pair] != source_url:
                print(f"[ARES AUDIT] Duplicate event_name+date pair for different URLs: {{}} -> {{}} and {{}}. Aborting emit.".format(pair, url_map[pair], source_url))
                diag['status'] = 'duplicate_event_name_date_url'
                diag['detail']['duplicate_pair'] = {'pair': pair, 'urls': [url_map[pair], source_url]}
                diagnostics.append(diag)
                return []
            url_map[pair] = source_url
            if pair in seen_pairs:
                print(f"[ARES AUDIT] Duplicate event_name+date pair detected: {{}}. Aborting emit.".format(pair))
                diag['status'] = 'duplicate_event_name_date'
                diag['detail']['duplicate_pair'] = {'pair': pair}
                diagnostics.append(diag)
                return []
            seen_pairs.add(pair)
            record = {
                'promotion': 'ARES FC',
                'event_name': event_name,
                'date': date_normalized,
                'city': None,
                'region': None,
                'country': None,
                'venue': None,
                'bouts': [],
                'source_url': source_url,
                'source_type': 'official_events_index',
                'source_confidence': 95 if event_name and date_normalized else 50,
                'last_seen_at': datetime.now(timezone.utc).isoformat(),
                'date_raw': date_raw,
                'date_source': 'index_visible',
            }
            if idx < 3:
                print(f"[ARES RETAINED] event_name={{!r}} date_raw={{!r}} date_normalized={{!r}} detail_url={{!r}}".format(event_name, date_raw, date_normalized, source_url))
            records.append(record)
        diag['status'] = 'ok'
        diag['detail']['records_built'] = len(records)
        diagnostics.append(diag)
        return records, diagnostics
    else:
        print(f"[ARES AUDIT] Count mismatch: anchors={{}} dates={{}} titles={{}}. No records emitted.".format(len(anchors), len(dates), len(titles)))
        diag['status'] = 'count_mismatch'
        diag['detail']['anchors'] = len(anchors)
        diag['detail']['dates'] = len(dates)
        diag['detail']['titles'] = len(titles)
        diagnostics.append(diag)
        return [], diagnostics
        el = elements[i]
        # Detect month/year header (e.g., 'APRIL 2026')
        if el.name in ['h2', 'h3', 'h4', 'h5', 'h6'] and el.text.strip().upper().endswith('2026'):
            m = re.match(r'(\w+)\s+(\d{4})', el.text.strip(), re.I)
            if m:
                current_month = m.group(1).title()
                current_year = m.group(2)
        # Detect event heading (e.g., '### [LFA 230 – BARTLING vs. CLEVELAND](...)')
        if el.name in ['h3', 'h4', 'h5', 'h6']:
            a = el.find('a')
            if a and a.text.strip() and a.has_attr('href'):
                event_name = a.text.strip()
                detail_url = a['href']
                if detail_url.startswith('/'):
                    detail_url = LFA_BASE_URL + detail_url
                elif detail_url.startswith('http'):
                    detail_url = detail_url
                detail_url = detail_url.split('?')[0].split('#')[0].rstrip('/')
                # Look back for date (e.g., 'April 3')
                date_str = None
                for j in range(i-1, max(i-4, -1), -1):
                    prev = elements[j]
                    t = prev.text.strip()
                    if re.match(r'^[A-Za-z]+\s+\d{1,2}$', t):
                        date_str = t
                        break
                # Compose full date
                date_normalized = None
                date_raw = date_str
                if date_str and current_month and current_year:
                    try:
                        dt = date_parser.parse(f"{date_str} {current_year}")
                        date_normalized = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
                # Look ahead for location line (next non-empty text)
                venue = None
                city = None
                region = None
                country = None
                for k in range(i+1, min(i+4, len(elements))):
                    next_el = elements[k]
                    loc_line = next_el.text.strip()
                    if loc_line and not next_el.find('a') and not re.match(r'^[A-Za-z]+\s+\d{1,2}$', loc_line):
                        venue = loc_line
                        break
                if event_name and date_normalized and detail_url:
                    record = {
                        'promotion': 'LFA',
                        'event_name': event_name,
                        'event_name_source': 'index_linked_heading',
                        'date': date_normalized,
                        'date_source': 'index_visible',
                        'date_raw': date_raw,
                        'city': city,
                        'region': region,
                        'country': country,
                        'venue': venue,
                        'bouts': [],
                        'source_url': detail_url,
                        'source_type': 'official_events_index',
                        'source_confidence': 95,
                        'last_seen_at': now_iso(),
                    }
                    if len(retained_records) < 5:
                        print(f"[LFA RETAINED] event_name={event_name!r} date_raw={date_raw!r} date_normalized={date_normalized!r} detail_url={detail_url!r} venue={venue!r}")
                    retained_records.append(record)
        i += 1
    # Deduplicate by promotion+event_name+date
    deduped = {}
    for rec in retained_records:
        key = f"{rec.get('promotion','').strip().lower()}__{(rec.get('event_name') or '').strip().lower()}__{rec.get('date') or ''}"
        if key and key not in deduped:
            deduped[key] = rec
    unique_records = list(deduped.values())
    adapter_diag['detail']['attempted'] = len(retained_records)
    adapter_diag['detail']['records_built'] = len(unique_records)
    adapter_diag['final_records'] = len(unique_records)
    if unique_records:
        adapter_diag['status'] = 'ok'
    else:
        adapter_diag['status'] = 'no_valid_events'
    for rec in unique_records:
        rec_norm = normalize_event(rec)
        retained_records.append(rec_norm)
    print(f"[LFA ADAPTER] Final diagnostics: {adapter_diag}")
    return unique_records, [adapter_diag]


import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any
from pathlib import Path
import traceback
import requests
from bs4 import BeautifulSoup
import re
from dateutil import parser as date_parser

PHASE1_SOURCES = [
    'ufc',
    'pfl',
    'lfa',
    'ares',
    'boxingscene',
]

RAW_EVENT_FIELDS = [
    'promotion', 'event_name', 'date', 'city', 'region', 'country', 'venue', 'bouts',
    'source_url', 'source_type', 'source_confidence', 'last_seen_at'
]

# Anchor output paths to script directory
ROOT = Path(__file__).resolve().parent
INCOMING_DIR = ROOT / "incoming"
UPCOMING_EVENTS_PATH = INCOMING_DIR / "upcoming_events.json"
CONFLICTS_PATH = INCOMING_DIR / "upcoming_events_conflicts.json"
SUMMARY_PATH = INCOMING_DIR / "upcoming_events_ingest_summary.json"

# --- Utility functions ---
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure all required fields are present and normalized
    out = {k: event.get(k, None) for k in RAW_EVENT_FIELDS}
    out['bouts'] = event.get('bouts', [])
    out['last_seen_at'] = now_iso()
    return out

def event_slug(event: Dict[str, Any]) -> str:
    # Normalized slug for deduplication: promotion + event_name + date
    promo = (event.get('promotion') or '').strip().lower().replace(' ', '_')
    name = (event.get('event_name') or '').strip().lower().replace(' ', '_')
    date = (event.get('date') or '').strip()
    return f'{promo}__{name}__{date}'

def fuzzy_event_key(event: Dict[str, Any]) -> str:
    # Fallback: promotion + date + city
    promo = (event.get('promotion') or '').strip().lower().replace(' ', '_')
    date = (event.get('date') or '').strip()
    city = (event.get('city') or '').strip().lower().replace(' ', '_')
    return f'{promo}__{date}__{city}'

def deduplicate_events(events: List[Dict[str, Any]]):
    seen = {}
    conflicts = []
    for event in events:
        slug = event_slug(event)
        if slug in seen:
            prev = seen[slug]
            # Conflict: keep higher confidence, log both
            if event['source_confidence'] > prev['source_confidence']:
                conflicts.append({'kept': event, 'dropped': prev, 'reason': 'confidence',
                                  'promotion': event.get('promotion'),
                                  'event_name': event.get('event_name'),
                                  'date': event.get('date'),
                                  'source_url': event.get('source_url')})
                print(f"[DEDUP] Dropping (confidence) {prev.get('promotion')} | {prev.get('event_name')} | {prev.get('date')} | {prev.get('source_url')}")
                seen[slug] = event
            else:
                conflicts.append({'kept': prev, 'dropped': event, 'reason': 'confidence',
                                  'promotion': event.get('promotion'),
                                  'event_name': event.get('event_name'),
                                  'date': event.get('date'),
                                  'source_url': event.get('source_url')})
                print(f"[DEDUP] Dropping (confidence) {event.get('promotion')} | {event.get('event_name')} | {event.get('date')} | {event.get('source_url')}")
        else:
            seen[slug] = event
    # Fuzzy fallback for near-duplicates
    fuzzy_seen = {}
    for event in seen.values():
        fuzzy = fuzzy_event_key(event)
        if fuzzy in fuzzy_seen:
            conflicts.append({'kept': fuzzy_seen[fuzzy], 'dropped': event, 'reason': 'fuzzy',
                              'promotion': event.get('promotion'),
                              'event_name': event.get('event_name'),
                              'date': event.get('date'),
                              'source_url': event.get('source_url')})
            print(f"[DEDUP] Dropping (fuzzy) {event.get('promotion')} | {event.get('event_name')} | {event.get('date')} | {event.get('source_url')}")
        else:
            fuzzy_seen[fuzzy] = event
    return list(fuzzy_seen.values()), conflicts
def count_by_promotion(records):
    counts = {}
    for r in records:
        p = r.get("promotion", "UNKNOWN")
        counts[p] = counts.get(p, 0) + 1
    return counts

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'[WRITE] {path.resolve()}')


# --- UFC Adapter Implementation ---
UFC_EVENTS_URL = 'https://www.ufc.com/events'
UFC_BASE_URL = 'https://www.ufc.com'

# --- UFC index parser: minimal working version ---
def parse_ufc_events_index(html):
    """
    Robust UFC event index parser: index-first, dedupe, detail extraction, normalized output, diagnostics.
    """
    from bs4 import BeautifulSoup
    import re, json
    from datetime import datetime
    soup = BeautifulSoup(html, 'html.parser')
    # 1. Extract canonical /event/... URLs
    anchors = soup.find_all('a', href=True)
    urls = []
    for a in anchors:
        href = a['href']
        if href.startswith('/event/') and len(href) > 8:
            url = UFC_BASE_URL + href if href.startswith('/') else href
            urls.append(url.split('?')[0].split('#')[0].rstrip('/'))
    # Dedupe URLs
    candidate_urls = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            candidate_urls.append(url)
    print(f"[UFC INDEX] Found {len(candidate_urls)} candidate event URLs.")
    # 2. For each detail URL, extract event_name, date, venue, city, region, country
    records = []
    for i, url in enumerate(candidate_urls[:12]):  # Limit for speed
        try:
            import requests
            resp = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': UFC_EVENTS_URL,
            })
            detail_soup = BeautifulSoup(resp.text, 'html.parser')
            event_name = None
            date = None
            venue = city = region = country = None
            # 1. Prefer <title> for event_name
            if detail_soup.title and detail_soup.title.text.strip():
                event_name = detail_soup.title.text.strip()
            # Remove trailing branding
            if event_name:
                for suffix in [
                    ' | UFC', ' - UFC', '| Ultimate Fighting Championship',
                    ' |Ultimate Fighting Championship', ' - Ultimate Fighting Championship',
                    '| UFC.com', ' |UFC', ' -UFC', ' | UFC ', ' - UFC ',
                    ' | Ultimate Fighting Championship ', ' - Ultimate Fighting Championship '
                ]:
                    if event_name.endswith(suffix):
                        event_name = event_name[: -len(suffix)].strip()
                for promo in ['UFC', 'Ultimate Fighting Championship']:
                    if event_name.strip() == promo:
                        event_name = None
            # 2. Try meta[name=description] and og:description for date/location
            meta_desc = detail_soup.find('meta', attrs={'name': 'description'})
            og_desc = detail_soup.find('meta', property='og:description')
            desc_texts = []
            if meta_desc and meta_desc.has_attr('content'):
                desc_texts.append(meta_desc['content'])
            if og_desc and og_desc.has_attr('content'):
                desc_texts.append(og_desc['content'])
            # Look for date in "on <Month> <D>, <YYYY>" or "<Month> <D>, <YYYY>"
            for desc in desc_texts:
                m = re.search(r'on ([A-Za-z]+ \d{1,2}, \d{4})', desc)
                if not m:
                    m = re.search(r'([A-Za-z]+ \d{1,2}, \d{4})', desc)
                if m:
                    try:
                        dt = datetime.strptime(m.group(1), '%B %d, %Y')
                        date = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
                # Try to extract venue/city/country from description
                if 'Meta APEX' in desc:
                    venue = 'Meta APEX'
                if 'Las Vegas' in desc:
                    city = 'Las Vegas'
                if 'Nevada' in desc:
                    region = 'Nevada'
                if 'United States' in desc or 'Las Vegas' in desc:
                    country = 'United States'
            # 3. Fallback: visible text for date
            if not date:
                text = detail_soup.get_text(separator=' ', strip=True)
                m = re.search(r'([A-Za-z]+ \d{1,2}, \d{4})', text)
                if m:
                    try:
                        dt = datetime.strptime(m.group(1), '%B %d, %Y')
                        date = dt.strftime('%Y-%m-%d')
                    except Exception:
                        pass
            # 4. Only emit if event_name and normalized date
            if event_name and date and re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                record = {
                    'promotion': 'UFC',
                    'event_name': event_name,
                    'date': date,
                    'city': city,
                    'region': region,
                    'country': country,
                    'venue': venue,
                    'bouts': [],
                    'source_url': url,
                    'source_type': 'official_event_detail',
                    'source_confidence': 100,
                    'last_seen_at': datetime.now().isoformat(),
                }
                if len(records) < 3:
                    print(f"[UFC RETAINED] event_name={event_name!r} date={date!r} url={url!r}")
                records.append(record)
        except Exception as e:
            print(f"[UFC DETAIL] Exception for url={url!r}: {e}")
    print(f"[UFC DETAIL] attempted={len(candidate_urls[:12])} records_built={len(records)}")
    return records

# --- PFL Adapter Implementation ---
PFL_EVENTS_URL = 'https://pflmma.com/events'
PFL_BASE_URL = 'https://pflmma.com'

def fetch_pfl_events_index(session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://pflmma.com/',
    }
    try:
        resp = session.get(PFL_EVENTS_URL, headers=headers, timeout=15)
        print(f'[PFL FETCH] status_code={resp.status_code} url={resp.url} content-type={resp.headers.get("content-type")} length={len(resp.content)}')
        body = resp.text
        print('[PFL FETCH] First 1000 chars:')
        print(body[:1000])
        if resp.status_code != 200 or len(body) < 2000:
            print('[PFL FETCH] Fetch failed or body too small, treating as access problem.')
            return None, resp
        return body, resp
    except Exception as e:
        print(f'[PFL FETCH] Exception: {e}')
        return None, None

def parse_pfl_events_index(html):
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find_all('a', href=True)
    urls = []
    for a in anchors:
        href = a['href']
        # Only accept canonical event detail URLs: /event/<slug> or full URL
        if href.startswith('/event/') or href.startswith('https://pflmma.com/event/'):
            # Normalize to absolute URL, strip query/fragments and trailing slashes
            if href.startswith('/'):
                url = PFL_BASE_URL + href
            else:
                url = href
            url = url.split('?')[0].split('#')[0].rstrip('/')
            # Only accept URLs matching /event/<slug> (not /events/ or other)
            if '/event/' in url and not url.rstrip('/').endswith('/event'):
                urls.append(url)
    # Dedupe and filter to only event URLs
    candidate_urls = []
    seen = set()
    for url in urls:
        if url.startswith('https://pflmma.com/event/') and url not in seen:
            seen.add(url)
            candidate_urls.append(url)
    return candidate_urls

def parse_pfl_event_detail(html, url):
    import re
    from datetime import datetime
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser') if html else None
    event_name = None
    event_date = None
    venue = None
    city = None
    region = None
    country = None
    date_raw = None
    date_source = None
    debug = {
        'url': url,
        'has_event_name': False,
        'has_date': False,
        'has_location': False,
        'date_raw': None,
        'date_source': None,
        'contamination': False,
        'contam_reason': None,
        'fallback_used': False,
    }
    # --- Event Name Extraction ---
    # 1. Try event-specific H1 or hero heading
    if soup:
        h1 = soup.find('h1')
        if h1 and h1.text.strip() and 'PFL' in h1.text:
            event_name = h1.text.strip()
    # 2. Try page title if not generic
    if not event_name and soup:
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            if title_text and 'Fight Card' not in title_text and 'Professional Fighters League' not in title_text:
                event_name = title_text
    # 3. Try og:title meta if not generic
    if not event_name and soup:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.has_attr('content'):
            og_title_val = og_title['content'].strip()
            if og_title_val and 'Fight Card' not in og_title_val and 'Professional Fighters League' not in og_title_val:
                event_name = og_title_val
    # 4. Fallback: derive from URL slug
    if not event_name:
        import re
        m = re.search(r'/event/([\w-]+)$', url)
        if m:
            slug = m.group(1)
            event_name = 'PFL ' + ' '.join([w.capitalize() for w in slug.replace('pfl-', '').replace('-', ' ').split() if w])
            debug['fallback_used'] = True
    # --- Date Extraction ---
    # 1. Try event-specific visible text near header
    event_date = None
    date_raw = None
    date_source = None
    if soup:
        # Look for date in hero/heading region
        hero = soup.find(['section', 'div'], class_=re.compile(r'(hero|header|event|main)', re.I))
        if hero:
            text = hero.get_text(separator=' ', strip=True)
            m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            if m:
                date_raw = m.group(1)
                event_date = date_raw
                date_source = 'hero:iso'
            if not event_date:
                m = re.search(r'(\w+ \d{1,2}, \d{4})', text)
                if m:
                    date_raw = m.group(1)
                    try:
                        dt = datetime.strptime(date_raw, '%B %d, %Y')
                        event_date = dt.strftime('%Y-%m-%d')
                        date_source = 'hero:monthname'
                    except Exception:
                        pass
    # 2. Structured data (JSON-LD) only if unique per page
    if not event_date and soup:
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json as _json
                data = _json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') in ['SportsEvent', 'Event']:
                    # Only accept if name matches event_name or slug
                    json_name = data.get('name', '').strip()
                    if event_name and json_name and json_name.lower() in event_name.lower():
                        for key in ['startDate', 'doorTime', 'start_time']:
                            if data.get(key):
                                date_raw = data[key]
                                if isinstance(date_raw, str):
                                    if re.match(r'\d{4}-\d{2}-\d{2}', date_raw):
                                        event_date = date_raw[:10]
                                        date_source = f'jsonld:{key}'
                                    else:
                                        try:
                                            dt = datetime.strptime(date_raw, '%B %d, %Y')
                                            event_date = dt.strftime('%Y-%m-%d')
                                            date_source = f'jsonld:{key}'
                                        except Exception:
                                            pass
                    break
            except Exception:
                pass
    # 3. Meta tags (event-specific only)
    if not event_date and soup:
        for meta in soup.find_all('meta'):
            for attr in ['event:start_date', 'event_date', 'date', 'startDate', 'og:start_date', 'og:event_date']:
                if meta.get('name') == attr or meta.get('property') == attr:
                    content = meta.get('content', '')
                    m = re.search(r'(\w+ \d{1,2}, \d{4})', content)
                    if m:
                        date_raw = m.group(1)
                        try:
                            dt = datetime.strptime(date_raw, '%B %d, %Y')
                            event_date = dt.strftime('%Y-%m-%d')
                            date_source = f'meta:{attr}'
                        except Exception:
                            pass
                        break
            if event_date:
                break
    # 4. Visible body text (as last resort)
    if not event_date and soup:
        text = soup.get_text(separator=' ', strip=True)
        m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if m:
            date_raw = m.group(1)
            event_date = date_raw
            date_source = 'body:iso'
        if not event_date:
            m = re.search(r'(\w+ \d{1,2}, \d{4})', text)
            if m:
                date_raw = m.group(1)
                try:
                    dt = datetime.strptime(date_raw, '%B %d, %Y')
                    event_date = dt.strftime('%Y-%m-%d')
                    date_source = 'body:monthname'
                except Exception:
                    pass
    # Venue fallback
    if soup and not venue:
        venue_el = soup.select_one('.field--name-venue, .c-venue-details__item')
        if venue_el:
            venue = venue_el.text.strip()
    # Clean event_name: strip trailing brand suffixes
    if event_name:
        for suffix in [
            ' | PFL', ' - PFL', '| Professional Fighters League',
            ' |Professional Fighters League', ' - Professional Fighters League',
            '| PFL.com', ' |PFL', ' -PFL', ' | PFL ', ' - PFL ',
            ' | Professional Fighters League ', ' - Professional Fighters League '
        ]:
            if event_name.endswith(suffix):
                event_name = event_name[: -len(suffix)].strip()
        for promo in ['PFL', 'Professional Fighters League']:
            if event_name.endswith(promo):
                if event_name.strip() != promo:
                    event_name = event_name[: -len(promo)].strip(' -|')
    # Normalize and split venue string
    if venue and (city is None and country is None):
        v = re.sub(r'[\s\t\n\r]+', ' ', venue)
        v = re.sub(r'\s*,\s*', ',', v)
        v = re.sub(r',+', ',', v)
        v = v.strip(' ,')
        parts = [p.strip() for p in v.split(',') if p.strip()]
        if len(parts) == 3:
            venue, city, country = parts
        elif len(parts) == 2:
            venue, city = parts
            country = None
        elif len(parts) == 1:
            venue = parts[0]
            city = None
            country = None
    # Contamination guard: reject if event_name or date is generic or matches other unrelated events
    generic_names = {'pfl', 'professional fighters league', 'fight card'}
    if event_name and event_name.strip().lower() in generic_names:
        debug['contamination'] = True
        debug['contam_reason'] = 'generic event_name'
        return None, debug
    if not event_name or not event_date:
        debug['contamination'] = True
        debug['contam_reason'] = 'missing event_name or event_date'
        return None, debug
    # Debug flags
    debug['has_event_name'] = True
    debug['has_date'] = True
    if venue or city or region or country:
        debug['has_location'] = True
    debug['date_raw'] = date_raw
    debug['date_source'] = date_source
    record = {
        'promotion': 'PFL',
        'event_name': event_name,
        'date': event_date,
        'city': city,
        'region': region,
        'country': country,
        'venue': venue,
        'bouts': [],
        'source_url': url,
        'source_type': 'official_event_detail',
        'source_confidence': 100 if not debug['fallback_used'] else 50,
        'last_seen_at': now_iso(),
    }
    return record, debug

def fetch_and_parse_pfl_events(session, diagnostics):
    from datetime import datetime
    adapter_diag = {
        'source': 'pfl',
        'adapter_entry': datetime.now(timezone.utc).isoformat(),
        'source_url': PFL_EVENTS_URL,
        'status': None,
        'fetch': {},
        'parse': {},
        'detail': {},
    }
    print(f'[PFL ADAPTER] Starting PFL adapter at {adapter_diag["adapter_entry"]} for {PFL_EVENTS_URL}')
    import re
    html, resp = fetch_pfl_events_index(session)
    final_events = []
    ingest_summary = []
    # --- Fetch diagnostics ---
    if resp is not None:
        body = resp.text
        adapter_diag['fetch'] = {
            'status_code': resp.status_code,
            'url': resp.url,
            'content_type': resp.headers.get('content-type'),
            'length': len(body),
            'has_event_marker': ('/event/' in body) or ('json-ld' in body) or ('Events' in body),
            'body_head': body[:300].replace('\n', ' ').replace('\r', ' ')[:300]
        }
        print(f"[PFL ADAPTER] Fetch status: {adapter_diag['fetch']}")
    else:
        adapter_diag['fetch'] = {'status': 'fetch_failed', 'exception': 'No response object'}
        print(f"[PFL ADAPTER] Fetch failed: No response object")
    if not html:
        adapter_diag['status'] = 'blocked' if resp and resp.status_code == 403 else 'fetch_failed'
        ingest_summary.append(adapter_diag)
        print(f"[PFL ADAPTER] No HTML body, status: {adapter_diag['status']}")
        return final_events, ingest_summary

    # --- Index-first event extraction ---
    soup = BeautifulSoup(html, 'html.parser')
    # Loosen selector: try all divs/articles/lis, print debug info
    event_cards = []
    for tag in soup.find_all(['div', 'article', 'li']):
        # Accept if it has a link to /event/ and a date or plausible event name
        a = tag.find('a', href=True)
        if a and '/event/' in a['href']:
            # Try to find a date or event name in the tag
            txt = tag.get_text(separator=' ', strip=True)
            if any(month in txt.lower() for month in ['january','february','march','april','may','june','july','august','september','october','november','december']) or re.search(r'\d{4}-\d{2}-\d{2}', txt):
                event_cards.append(tag)
    print(f"[PFL ADAPTER] Found {len(event_cards)} candidate event cards on index page.")
    records = []
    detail_debug_rows = []
    from datetime import datetime, timedelta
    today = datetime(2026, 3, 31)
    retained_records = []
    for i, card in enumerate(event_cards):
        info = card.find(class_='event-card-info')
        if not info:
            continue
        # Extract event name from h3
        h3 = info.find('h3')
        event_name = h3.text.strip() if h3 and h3.text.strip() else None
        event_name_source = 'index_h3' if event_name else None
        # Try to enrich event name with city/location from index card if present
        location_text = None
        # Look for a span or div with city/location info inside the card
        for loc_tag in info.find_all(['span', 'div']):
            txt = loc_tag.get_text(separator=' ', strip=True)
            if txt and txt.lower() not in (event_name or '').lower() and len(txt) > 2 and not txt.lower().startswith('fri'):
                location_text = txt
                break
        # If event_name is short and location_text is plausible, append it
        if event_name and location_text and location_text not in event_name:
            event_name = f"{event_name} {location_text}".strip()
        # Extract date from h6 (short form like 'Fri, Apr 10')
        h6 = info.find('h6')
        event_date_raw = h6.text.strip() if h6 and h6.text.strip() else None
        event_date_source = 'index_h6_shortdate' if event_date_raw else None
        # Normalize date: parse 'Fri, Apr 10' to YYYY-MM-DD
        event_date_normalized = None
        if event_date_raw:
            m = re.match(r'\w{3}, (\w{3,9}) (\d{1,2})', event_date_raw)
            if m:
                month_str, day_str = m.group(1), m.group(2)
                try:
                    month_num = datetime.strptime(month_str, '%b').month if len(month_str) == 3 else datetime.strptime(month_str, '%B').month
                    day_num = int(day_str)
                    year = today.year
                    dt = datetime(year, month_num, day_num)
                    # If date is >30 days in the past, roll to next year
                    if (dt - today).days < -30:
                        dt = datetime(year + 1, month_num, day_num)
                    event_date_normalized = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
        # Extract canonical detail URL from anchor in info
        detail_url = None
        a = info.find('a', href=True)
        if a:
            href = a['href']
            if href.startswith('/'):
                detail_url = PFL_BASE_URL + href
            elif href.startswith('http'):
                detail_url = href
            if detail_url:
                detail_url = detail_url.split('?')[0].split('#')[0].rstrip('/')
        # Only emit if all three fields exist
        if event_name and event_date_normalized and detail_url:
            record = {
                'promotion': 'PFL',
                'event_name': event_name,
                'event_name_source': event_name_source,
                'date': event_date_normalized,
                'date_source': event_date_source,
                'date_raw': event_date_raw,
                'city': None,
                'region': None,
                'country': None,
                'venue': None,
                'bouts': [],
                'source_url': detail_url,
                'source_type': 'official_events_index',
                'source_confidence': 95,
                'last_seen_at': now_iso(),
            }
            # Optional enrichment from detail page (venue only, do not overwrite event_name/date)
            detail_html, meta = None, {}
            try:
                resp = requests.get(detail_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': PFL_EVENTS_URL,
                }, timeout=15)
                detail_html = resp.text
                meta = {'status_code': resp.status_code, 'url': resp.url}
            except Exception as e:
                meta = {'status_code': None, 'url': detail_url, 'error': str(e)}
            if detail_html:
                soup_detail = BeautifulSoup(detail_html, 'html.parser')
                venue_el = soup_detail.select_one('.field--name-venue, .c-venue-details__item')
                if venue_el:
                    record['venue'] = venue_el.text.strip()
            if len(retained_records) < 5:
                print(f"[PFL RETAINED] event_name={event_name!r} date_raw={event_date_raw!r} date_normalized={event_date_normalized!r} detail_url={detail_url!r}")
            retained_records.append(record)
    # Deduplicate records by promotion+event_name+date
    deduped = {}
    for rec in retained_records:
        key = f"{rec.get('promotion','').strip().lower()}__{(rec.get('event_name') or '').strip().lower()}__{rec.get('date') or ''}"
        if key and key not in deduped:
            deduped[key] = rec
    unique_records = list(deduped.values())
    adapter_diag['detail']['attempted'] = len(retained_records)
    adapter_diag['detail']['debug'] = retained_records[:5]
    adapter_diag['detail']['records_built'] = len(unique_records)
    adapter_diag['final_records'] = len(unique_records)
    if unique_records:
        adapter_diag['status'] = 'ok'
    else:
        adapter_diag['status'] = 'no_valid_events'
    for rec in unique_records:
        final_events.append(normalize_event(rec))
    if final_events:
        adapter_diag['status'] = 'ok'
    elif retained_records:
        adapter_diag['status'] = 'record_build_failed'
    else:
        adapter_diag['status'] = 'zero_candidates'
    adapter_diag['final_records'] = len(final_events)
    ingest_summary.append(adapter_diag)
    print(f"[PFL ADAPTER] Final diagnostics: {adapter_diag}")
    # End of function


# --- UFC fetch implementation ---
def fetch_ufc_events_index(session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.ufc.com/',
    }
    try:
        resp = session.get(UFC_EVENTS_URL, headers=headers, timeout=15)
        print(f'[UFC FETCH] status_code={resp.status_code} url={resp.url} content-type={resp.headers.get("content-type")} length={len(resp.content)}')
        body = resp.text
        print('[UFC FETCH] First 1000 chars:')
        print(body[:1000])
        if resp.status_code != 200 or len(body) < 2000:
            print('[UFC FETCH] Fetch failed or body too small, treating as access problem.')
            return None, resp
        return body, resp
    except Exception as e:
        print(f'[UFC FETCH] Exception: {e}')
        return None, None
def fetch_and_parse_ufc_events(session, diagnostics):
    from datetime import datetime
    adapter_diag = {
        'source': 'ufc',
        'adapter_entry': datetime.now(timezone.utc).isoformat(),
        'source_url': UFC_EVENTS_URL,
        'status': None,
        'fetch': {},
        'parse': {},
        'detail': {},
    }
    print(f'[UFC ADAPTER] Starting UFC adapter at {adapter_diag["adapter_entry"]} for {UFC_EVENTS_URL}')
    html, resp = fetch_ufc_events_index(session)
    final_events = []
    ingest_summary = []
    # --- Fetch diagnostics ---
    if resp is not None:
        body = resp.text
        try:
            records = parse_ufc_events_index(html)
            adapter_diag['parse']['candidate_links'] = len(records)
        except Exception as e:
            adapter_diag['status'] = 'parse_error'
            adapter_diag['parse']['error'] = str(e)
            ingest_summary.append(adapter_diag)
            print(f"[UFC ADAPTER] Parse error: {e}")
            return [], ingest_summary
        if not records:
            adapter_diag['status'] = 'zero_candidates'
            ingest_summary.append(adapter_diag)
            print(f"[UFC ADAPTER] No candidate event records found.")
            return [], ingest_summary
        # --- DEBUG RAIL: UFC count at function return ---
        adapter_diag['detail']['records_built'] = len(records)
        adapter_diag['final_records'] = len(records)
        print(f"[UFC DEBUG] function return: len(records)={len(records)}")
        print(f"[UFC DEBUG] function return: first3_records={records[:3]}")
        print(f"[UFC DEBUG] function return: diag_records_built={adapter_diag['detail'].get('records_built')} final_events={len(records)}")
        if records:
            adapter_diag['status'] = 'ok'
        else:
            adapter_diag['status'] = 'record_build_failed'
        ingest_summary.append(adapter_diag)
        print(f"[UFC ADAPTER] Final diagnostics: {adapter_diag}")
        return records, ingest_summary
    # Remove unreachable/legacy code and undefined names
    return records, ingest_summary

def log(msg, *args, verbose=False, always=False):
    if always or verbose:
        print(msg.format(*args), flush=True)

def main():
    parser = argparse.ArgumentParser(description='AI-RISA Source Ingestion Layer')
    parser.add_argument('--handoff', action='store_true', help='Optionally hand off to build_upcoming_schedule_auto.py')
    parser.add_argument('--handoff-path', default='C:/ai_risa_data/incoming/upcoming_events.json')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    verbose = args.verbose

    log("[START] ingest_upcoming_events_sources.py", verbose=verbose, always=True)
    log("[PATHS] Script directory: {}", ROOT, verbose=verbose, always=True)
    log("[PATHS] Upcoming events: {}", UPCOMING_EVENTS_PATH, verbose=verbose, always=True)
    log("[PATHS] Conflicts: {}", CONFLICTS_PATH, verbose=verbose, always=True)
    log("[PATHS] Summary: {}", SUMMARY_PATH, verbose=verbose, always=True)
    session = requests.Session()
    all_events = []
    diagnostics = []
def _boxingscene_clean_text(value):
    text = re.sub(r'\s+', ' ', (value or '').strip())
    return text.replace('| BoxingScene', '').replace('- BoxingScene', '').strip(' -|')


def _boxingscene_normalize_title(raw_title):
    title = _boxingscene_clean_text(raw_title)
    if not title:
        return None
    if re.search(r'\b(schedule|boxing schedule|results|news|videos|rankings|tickets|odds)\b', title, re.I):
        return None
    title = re.sub(r'\s{2,}', ' ', title).strip()
    if len(title) < 4 or len(title) > 160:
        return None
    return title


def _boxingscene_normalize_date(raw_date):
    candidate = _boxingscene_clean_text(raw_date)
    if not candidate:
        return None
    if re.match(r'^\d{4}-\d{2}-\d{2}$', candidate):
        return candidate
    for fmt in ('%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y'):
        try:
            return datetime.strptime(candidate, fmt).strftime('%Y-%m-%d')
        except Exception:
            continue
    try:
        parsed = date_parser.parse(candidate, fuzzy=False)
        return parsed.strftime('%Y-%m-%d')
    except Exception:
        return None


def _boxingscene_parse_location(raw_location):
    text = _boxingscene_clean_text(raw_location)
    if not text:
        return None, None, None
    parts = [p.strip() for p in re.split(r'\s*,\s*', text) if p.strip()]
    if not parts:
        return None, None, None
    city = parts[0] if len(parts) >= 1 else None
    region = parts[1] if len(parts) >= 2 else None
    country = parts[2] if len(parts) >= 3 else None
    if len(parts) == 2 and len(parts[1]) > 3:
        country = parts[1]
        region = None
    return city, region, country


def _boxingscene_normalize_jsonld_address(address):
    city = None
    region = None
    country = None
    if not isinstance(address, dict):
        return city, region, country

    city = _boxingscene_clean_text(address.get('addressLocality')) or None
    region = _boxingscene_clean_text(address.get('addressRegion')) or None
    country = _boxingscene_clean_text(address.get('addressCountry')) or None

    # BoxingScene JSON-LD often places "Region, Country" in addressRegion.
    if region and not country and ',' in region:
        parts = [p.strip() for p in region.split(',') if p.strip()]
        if len(parts) == 2:
            region = parts[0]
            country = parts[1]
        elif len(parts) >= 3 and not city:
            city = parts[0]
            region = parts[1]
            country = parts[-1]

    return city, region, country


def _boxingscene_extract_bouts_from_strings(strings):
    bouts = []
    seen = set()
    bout_re = re.compile(r'^([A-Za-z0-9 .\'\-]{2,80})\s+(?:vs\.?|v\.?|versus)\s+([A-Za-z0-9 .\'\-]{2,80})$', re.I)
    for raw in strings:
        line = _boxingscene_clean_text(raw)
        if not line:
            continue
        match = bout_re.match(line)
        if not match:
            continue
        red = re.sub(r'\s+', ' ', match.group(1)).strip()
        blue = re.sub(r'\s+', ' ', match.group(2)).strip()
        if len(red) < 2 or len(blue) < 2:
            continue
        key = f'{red.lower()}__{blue.lower()}'
        if key in seen:
            continue
        seen.add(key)
        bouts.append(f'{red} vs {blue}')
        if len(bouts) >= 20:
            break
    return bouts


def _boxingscene_get_with_retries(session, url, context_label, timeout_seconds=12, max_attempts=3, min_body_length=0):
    last_error = None
    max_attempts = max(1, int(max_attempts))
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, timeout=timeout_seconds)
            body = resp.text or ''
            if resp.status_code == 200 and len(body) >= min_body_length:
                if attempt > 1:
                    print(f'[{context_label}] recovered on_attempt={attempt} url={url}')
                return resp, body, None
            last_error = f'bad_response status={resp.status_code} body_len={len(body)}'
            print(f'[{context_label}] attempt={attempt}/{max_attempts} failed {last_error} url={url}')
        except Exception as exc:
            last_error = f'exception={exc}'
            print(f'[{context_label}] attempt={attempt}/{max_attempts} failed {last_error} url={url}')

    return None, None, last_error or 'unknown_fetch_failure'


def _boxingscene_fetch_detail_bouts(session, detail_url):
    resp, body, error = _boxingscene_get_with_retries(
        session,
        detail_url,
        'BOXINGSCENE DETAIL',
        timeout_seconds=12,
        max_attempts=2,
        min_body_length=500,
    )
    if not resp:
        print(f'[BOXINGSCENE DETAIL] failed url={detail_url} reason={error}')
        return []

    try:
        soup = BeautifulSoup(body, 'html.parser')
        strings = [s for s in soup.stripped_strings]
        return _boxingscene_extract_bouts_from_strings(strings)
    except Exception as exc:
        print(f'[BOXINGSCENE DETAIL] parse_exception url={detail_url} error={exc}')
        return []


def _boxingscene_extract_records_from_jsonld(soup, schedule_url):
    records = []
    failure_reasons = {
        'jsonld_invalid': 0,
        'jsonld_missing_title': 0,
        'jsonld_invalid_date': 0,
    }
    candidates = []

    def append_if_event(item):
        if isinstance(item, dict) and str(item.get('@type', '')).lower() == 'sportsevent':
            candidates.append(item)

    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        raw = (script.string or script.get_text() or '').strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            failure_reasons['jsonld_invalid'] += 1
            continue

        objects = data if isinstance(data, list) else [data]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            append_if_event(obj)
            main_entity = obj.get('mainEntity')
            if isinstance(main_entity, dict):
                append_if_event(main_entity)
                item_list = main_entity.get('itemListElement')
                if isinstance(item_list, list):
                    for entry in item_list:
                        append_if_event(entry)

    for event in candidates:
        event_title = _boxingscene_normalize_title(event.get('name'))
        if not event_title:
            failure_reasons['jsonld_missing_title'] += 1
            continue

        date_normalized = _boxingscene_normalize_date(event.get('startDate'))
        if not date_normalized:
            failure_reasons['jsonld_invalid_date'] += 1
            continue

        detail_url = event.get('url') or schedule_url
        if isinstance(detail_url, str) and detail_url.startswith('/'):
            detail_url = f'https://www.boxingscene.com{detail_url}'
        if not isinstance(detail_url, str) or not detail_url:
            detail_url = schedule_url

        city = None
        region = None
        country = None
        venue = None

        location = event.get('location')
        if isinstance(location, dict):
            venue = _boxingscene_clean_text(location.get('name')) or None
            address = location.get('address')
            if isinstance(address, dict):
                city, region, country = _boxingscene_normalize_jsonld_address(address)
            elif isinstance(address, str):
                city, region, country = _boxingscene_parse_location(address)

        bouts = []
        competitors = event.get('competitor')
        if isinstance(competitors, list):
            names = []
            for competitor in competitors:
                if isinstance(competitor, dict):
                    name = _boxingscene_normalize_title(competitor.get('name'))
                    if name:
                        names.append(name)
            for idx in range(0, len(names) - 1, 2):
                bouts.append(f"{names[idx]} vs {names[idx + 1]}")

        records.append({
            'promotion': 'Boxing',
            'event_name': event_title,
            'date': date_normalized,
            'city': city,
            'region': region,
            'country': country,
            'venue': venue,
            'bouts': bouts,
            'source_url': detail_url,
            'source_type': 'trusted_schedule_aggregator',
            'source_confidence': 70,
            'last_seen_at': now_iso(),
        })

    return records, failure_reasons, len(candidates)


def _parse_boxingscene_schedule_html(body, schedule_url):
    soup = BeautifulSoup(body, 'html.parser')
    month_re = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
    date_patterns = [
        re.compile(rf'\b({month_re}\s+\d{{1,2}},\s+\d{{4}})\b', re.I),
        re.compile(rf'\b({month_re}\s+\d{{1,2}}\s+\d{{4}})\b', re.I),
        re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),
    ]
    selectors = ['article', 'li', 'tr', 'div.schedule-item', 'div.event', 'div.card']
    candidate_nodes = []
    for selector in selectors:
        candidate_nodes.extend(soup.select(selector))
    if not candidate_nodes:
        candidate_nodes = soup.find_all(['article', 'li', 'tr', 'div'])

    retained_records = []
    attempted_nodes = 0
    failure_reasons = {
        'no_candidate_nodes': 0,
        'missing_date': 0,
        'invalid_date': 0,
        'missing_title': 0,
    }

    structured_records, structured_failure_reasons, structured_candidates = _boxingscene_extract_records_from_jsonld(soup, schedule_url)
    retained_records.extend(structured_records)

    if not candidate_nodes:
        failure_reasons['no_candidate_nodes'] += 1

    for node in candidate_nodes:
        attempted_nodes += 1
        node_text = _boxingscene_clean_text(node.get_text(' ', strip=True))
        if len(node_text) < 20:
            continue

        date_raw = None
        for pattern in date_patterns:
            match = pattern.search(node_text)
            if match:
                date_raw = match.group(1)
                break
        if not date_raw:
            failure_reasons['missing_date'] += 1
            continue

        date_normalized = _boxingscene_normalize_date(date_raw)
        if not date_normalized:
            failure_reasons['invalid_date'] += 1
            continue

        event_title = None
        for tag_name in ('h1', 'h2', 'h3', 'h4', 'strong'):
            heading = node.find(tag_name)
            if not heading:
                continue
            event_title = _boxingscene_normalize_title(heading.get_text(' ', strip=True))
            if event_title:
                break
        if not event_title:
            anchor = node.find('a', href=True)
            if anchor:
                event_title = _boxingscene_normalize_title(anchor.get_text(' ', strip=True))
        if not event_title:
            left_side = _boxingscene_normalize_title(node_text.split(date_raw)[0])
            right_side = _boxingscene_normalize_title(node_text.split(date_raw)[-1])
            event_title = left_side or right_side
        if not event_title:
            failure_reasons['missing_title'] += 1
            continue

        detail_url = schedule_url
        anchor = node.find('a', href=True)
        if anchor and anchor.get('href'):
            href = anchor.get('href').strip()
            if href.startswith('http'):
                detail_url = href
            elif href.startswith('/'):
                detail_url = f'https://www.boxingscene.com{href}'

        location_text = None
        location_node = node.select_one('.location, .event-location, .venue')
        if location_node:
            location_text = location_node.get_text(' ', strip=True)
        else:
            location_match = re.search(r'\b([A-Za-z][A-Za-z .\'\-]+,\s*[A-Za-z][A-Za-z .\'\-]+(?:,\s*[A-Za-z][A-Za-z .\'\-]+)?)\b', node_text)
            if location_match:
                location_text = location_match.group(1)
        city, region, country = _boxingscene_parse_location(location_text)

        bouts = _boxingscene_extract_bouts_from_strings(node.stripped_strings)
        record = {
            'promotion': 'Boxing',
            'event_name': event_title,
            'date': date_normalized,
            'city': city,
            'region': region,
            'country': country,
            'venue': None,
            'bouts': bouts,
            'source_url': detail_url,
            'source_type': 'trusted_schedule_aggregator',
            'source_confidence': 70,
            'last_seen_at': now_iso(),
        }
        if len(retained_records) < 3:
            print(f"[BOXINGSCENE RETAINED] event_name={event_title!r} date_raw={date_raw!r} date_normalized={date_normalized!r} detail_url={detail_url!r}")
        retained_records.append(record)

    deduped = {}
    for rec in retained_records:
        key = f"{rec.get('promotion', '').strip().lower()}__{(rec.get('event_name') or '').strip().lower()}__{rec.get('date') or ''}"
        if key and key not in deduped:
            deduped[key] = rec

    unique_records = list(deduped.values())
    parse_diag = {
        'attempted_nodes': attempted_nodes,
        'attempted': len(retained_records),
        'records_built': len(unique_records),
        'failure_reasons': failure_reasons,
        'structured_candidates': structured_candidates,
        'structured_records_built': len(structured_records),
        'structured_failure_reasons': structured_failure_reasons,
    }
    return unique_records, parse_diag


def fetch_and_parse_boxingscene_events(session, diagnostics):
    """
    BoxingScene schedule extraction: index-first, trusted aggregator, never overwrite official-source records.
    """
    BOXINGSCENE_URL = 'https://www.boxingscene.com/schedule'
    adapter_diag = {
        'source': 'boxingscene',
        'adapter_entry': now_iso(),
        'source_url': BOXINGSCENE_URL,
        'status': None,
        'detail': {},
    }
    resp, body, error = _boxingscene_get_with_retries(
        session,
        BOXINGSCENE_URL,
        'BOXINGSCENE FETCH',
        timeout_seconds=12,
        max_attempts=3,
        min_body_length=2000,
    )
    if not resp:
        adapter_diag['status'] = 'fetch_failed'
        adapter_diag['detail']['explicit_failure_reason'] = f'schedule_fetch_failed reason={error}'
        diagnostics.append(adapter_diag)
        print(f'[BOXINGSCENE FETCH] failed url={BOXINGSCENE_URL} reason={error}')
        return [], diagnostics

    adapter_diag['fetch_status_code'] = resp.status_code
    adapter_diag['fetch_length'] = len(body)

    records, parse_diag = _parse_boxingscene_schedule_html(body, BOXINGSCENE_URL)
    adapter_diag['detail'].update(parse_diag)

    detail_enriched = 0
    for rec in records:
        if rec.get('bouts'):
            continue
        detail_url = rec.get('source_url')
        if not detail_url or detail_url == BOXINGSCENE_URL:
            continue
        detail_bouts = _boxingscene_fetch_detail_bouts(session, detail_url)
        if detail_bouts:
            rec['bouts'] = detail_bouts
            detail_enriched += 1
    adapter_diag['detail']['detail_pages_enriched'] = detail_enriched

    adapter_diag['final_records'] = len(records)
    if records:
        adapter_diag['status'] = 'ok'
    else:
        adapter_diag['status'] = 'no_valid_events'
        adapter_diag['detail']['explicit_failure_reason'] = 'schedule_parsed_but_no_valid_records'
        print(f"[BOXINGSCENE PARSE] no valid events failure_reasons={adapter_diag['detail'].get('failure_reasons')}")

    diagnostics.append(adapter_diag)
    print(f"[BOXINGSCENE ADAPTER] Final diagnostics: {adapter_diag}")
    return records, diagnostics


ADAPTERS = {
    "ufc": fetch_and_parse_ufc_events,
    "pfl": fetch_and_parse_pfl_events,
    "lfa": fetch_and_parse_lfa_events,
    "ares": fetch_and_parse_ares_events,
    "boxingscene": fetch_and_parse_boxingscene_events,
}


ADAPTERS = {
    "ufc": fetch_and_parse_ufc_events,
    "pfl": fetch_and_parse_pfl_events,
    "lfa": fetch_and_parse_lfa_events,
    "ares": fetch_and_parse_ares_events,
    "boxingscene": fetch_and_parse_boxingscene_events,
}

def main():
    parser = argparse.ArgumentParser(description='AI-RISA Source Ingestion Layer')
    parser.add_argument('--handoff', action='store_true', help='Optionally hand off to build_upcoming_schedule_auto.py')
    parser.add_argument('--handoff-path', default='C:/ai_risa_data/incoming/upcoming_events.json')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    verbose = args.verbose

    print(f"[START] ingest_upcoming_events_sources.py", flush=True)
    print("[PATHS] Script directory:", ROOT, flush=True)
    print("[PATHS] Upcoming events:", UPCOMING_EVENTS_PATH, flush=True)
    print("[PATHS] Conflicts:", CONFLICTS_PATH, flush=True)
    print("[PATHS] Summary:", SUMMARY_PATH, flush=True)
    session = requests.Session()
    all_events = []
    diagnostics = []

    started_at = now_iso()
    status = "success"
    warnings = []
    errors = []
    artifacts = [str(UPCOMING_EVENTS_PATH), str(CONFLICTS_PATH), str(SUMMARY_PATH)]
    counts = {}
    details = {}
    deduped = []
    conflicts = []
    summary_payload = {
        "stage": "ingest",
        "status": "error",
        "started_at": started_at,
        "finished_at": now_iso(),
        "counts": {},
        "warnings": [],
        "errors": [{"type": "ingest_incomplete", "detail": "ingest ended before summary assembly"}],
        "artifacts": artifacts,
        "details": {
            "events": [],
            "conflicts": []
        }
    }
    try:
        for source_name, adapter in ADAPTERS.items():
            log("[INGEST] start {}", source_name, verbose=verbose)
            try:
                events, adapter_diags = adapter(session, diagnostics)
                all_events.extend(events)
                # Collect adapter diagnostics for warnings/errors
                for diag in (adapter_diags if isinstance(adapter_diags, list) else [adapter_diags]):
                    if diag.get('status') in ("fetch_failed", "blocked", "no_valid_events", "count_mismatch"):
                        warnings.append({"source": source_name, **diag})
                    elif diag.get('status') and diag.get('status').startswith("fail"):
                        errors.append({"source": source_name, **diag})
                log("[INGEST] done {} events={}", source_name, len(events), verbose=verbose)
                if source_name == "ufc":
                    log("[UFC DEBUG] after adapter: source_name={} len(events)={} first3={}", source_name, len(events), events[:3], verbose=verbose)
            except Exception as e:
                err = {"source": source_name, "status": f"fail: {type(e).__name__}: {e}"}
                errors.append(err)
                log("[INGEST] fail {}: {}: {}", source_name, type(e).__name__, e, verbose=True)

        log("[UFC DEBUG] before dedupe counts={}", count_by_promotion(all_events), verbose=verbose)
        deduped, conflicts = deduplicate_events(all_events)
        log("[UFC DEBUG] after dedupe counts={}", count_by_promotion(deduped), verbose=verbose)
        log("[UFC DEBUG] before write counts={}", count_by_promotion(deduped), verbose=verbose)

        # Map counts
        counts = count_by_promotion(deduped)
        counts["total_events"] = len(deduped)
        counts["conflicts"] = len(conflicts)
        # Optionally add more ingest-specific counts here

        # Compose unified summary schema
        finished_at = now_iso()
        summary_payload = {
            "stage": "ingest",
            "status": status if not errors else "error",
            "started_at": started_at,
            "finished_at": finished_at,
            "counts": counts,
            "warnings": warnings,
            "errors": errors,
            "artifacts": artifacts,
            "details": {
                "events": deduped,
                "conflicts": conflicts,
            }
        }
    finally:
        log("[WRITE] summary -> {}", SUMMARY_PATH, always=True)
        write_json(SUMMARY_PATH, summary_payload)
        log("[WRITE] events -> {}", UPCOMING_EVENTS_PATH, always=True)
        write_json(UPCOMING_EVENTS_PATH, deduped if 'deduped' in locals() else [])
        log("[WRITE] conflicts -> {}", CONFLICTS_PATH, always=True)
        write_json(CONFLICTS_PATH, conflicts if 'conflicts' in locals() else [])

    if args.handoff:
        # Optionally invoke build_upcoming_schedule_auto.py
        import subprocess
        cmd = [sys.executable, 'C:/ai_risa_data/build_upcoming_schedule_auto.py',
               '--source', args.handoff_path,
               '--schedule-out', 'C:/ai_risa_data/schedules/upcoming_auto.json',
               '--events-dir', 'C:/ai_risa_data/events',
               '--summary-json', 'C:/ai_risa_data/output/upcoming_auto_summary.json',
               '--summary-csv', 'C:/ai_risa_data/output/upcoming_auto_summary.csv',
               '--launch-batch', '--formats', 'md', 'docx', 'pdf']
        log('[HANDOFF] Launching: {}', " ".join(cmd), always=True)
        rc = subprocess.call(cmd)
        log('[HANDOFF] build_upcoming_schedule_auto.py exit code: {}', rc, always=True)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
