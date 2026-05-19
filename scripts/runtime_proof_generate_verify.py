"""
runtime_proof_generate_verify.py
Step 5+6: Generate 3 fresh PDFs via guarded route, extract text, verify page counts, sections, forbidden phrases.
Outputs structured JSON results to stdout.
"""
import json, sys, time
import urllib.request, urllib.error

BASE = "http://127.0.0.1:5050"
ENDPOINT = "/api/button2/selected-matchup/generate-guarded-v1"

MATCHUPS = [
    {
        "fighter_a": "Alex Pereira",
        "fighter_b": "Jiri Prochazka",
        "event_name": "UFC 300",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "expected_filename": "alex_pereira_vs_jiri_prochazka_ufc_300_premium.pdf",
    },
    {
        "fighter_a": "Rico Verhoeven",
        "fighter_b": "Tariq Osaro",
        "event_name": "GLORY 100",
        "source_url": "https://www.glorykickboxing.com/events/glory-100",
        "expected_filename": "rico_verhoeven_vs_tariq_osaro_glory_100_premium.pdf",
    },
    {
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "event_name": "Joshua vs Dubois",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "expected_filename": "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf",
    },
]

REQUIRED_SECTIONS = [
    "Cover Page",
    "Fight Intelligence Dashboard",
    "Headline Projection",
    "Matchup Snapshot",
    "Fighter Architecture Radar",
    "Tactical Edge Map",
    "Decision Structure",
    "Energy Use Analysis",
    "Fatigue Failure Points",
    "Mental Condition Under Stress",
    "Collapse Triggers",
    "Deception and Unpredictability",
    "Range / Geography Control",
    "Round-by-Round Control Projection",
    "Scenario Tree / Method Pathways",
    "Scorecard Scenario",
    "Stoppage Windows",
    "Risk Warnings and Exposure Discipline",
    "Betting Market Intelligence",
    "Coach / Corner Notes",
    "Final Projection",
    "Confidence Explanation",
    "Traceability / Source Map",
    "Disclaimer / Risk Control",
]

FORBIDDEN_PHRASES = [
    # Original stale-14-page placeholder phrases (primary check)
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
    "SOURCE TRACEABILITY Source Traceability",
    # Renderer description text (case-insensitive — must not appear in any form)
    "Premium Cover",
    # Governance/status string leakage
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
]

def wait_for_server(retries=10, delay=1.0):
    for i in range(retries):
        try:
            urllib.request.urlopen(f"{BASE}/", timeout=3)
            return True
        except Exception:
            time.sleep(delay)
    return False

def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def extract_pdf_text(pdf_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        pages = len(reader.pages)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
        return pages, full_text
    except ImportError:
        pass
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = len(reader.pages)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""
        return pages, full_text
    except ImportError:
        pass
    return None, ""

def check_pdf_library_route():
    try:
        req = urllib.request.Request(f"{BASE}/api/button2/generated-report/library", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return {"status": resp.status, "ok": True, "body_len": len(body)}
    except Exception as e:
        return {"status": None, "ok": False, "error": str(e)}

def check_open_pdf_route(filename):
    try:
        url = f"{BASE}/api/button2/generated-report/open?filename={urllib.parse.quote(filename)}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": resp.status, "ok": True}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "ok": e.code < 500}
    except Exception as e:
        return {"status": None, "ok": False, "error": str(e)}

import urllib.parse

def main():
    print("Waiting for server...", flush=True)
    if not wait_for_server():
        print(json.dumps({"error": "Server not reachable after retries"}))
        sys.exit(1)
    print("Server ready.", flush=True)

    results = []
    for m in MATCHUPS:
        matchup_key = f"{m['fighter_a']} vs {m['fighter_b']}"
        print(f"\nGenerating: {matchup_key} / {m['event_name']}", flush=True)

        payload = {
            "operator_approved": True,
            "selected_matchup_preview": {
                "fighter_a": m["fighter_a"],
                "fighter_b": m["fighter_b"],
                "event_name": m["event_name"],
                "source_url": m["source_url"],
                "selected_for_button2": True,
            }
        }

        try:
            resp = post_json(f"{BASE}{ENDPOINT}", payload)
        except Exception as e:
            results.append({"matchup": matchup_key, "error": str(e), "generation_ok": False})
            continue

        gen_ok = resp.get("success") or resp.get("report_status") == "customer_ready"
        pdf_path = resp.get("pdf_path") or resp.get("output_path") or resp.get("file_path")
        page_count_from_api = resp.get("page_count")
        governance = {
            "customer_approved": resp.get("customer_approved"),
            "customer_ready_gates_passed": resp.get("customer_ready_gates_passed"),
            "report_status": resp.get("report_status"),
            "report_quality_status": resp.get("report_quality_status"),
            "operator_flag": resp.get("operator_flag"),
            "draft_only": resp.get("draft_only"),
            "controlled_export_not_eligible": resp.get("controlled_export_not_eligible"),
        }

        # Also try to find the file via expected filename
        reports_dir = r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports"
        import os
        if not pdf_path or not os.path.exists(pdf_path):
            candidate = os.path.join(reports_dir, m["expected_filename"])
            if os.path.exists(candidate):
                pdf_path = candidate

        if pdf_path and os.path.exists(pdf_path):
            pages, full_text = extract_pdf_text(pdf_path)
            section_scan = {s: (s in full_text) for s in REQUIRED_SECTIONS}
            forbidden_scan = {p: (p.lower() in full_text.lower()) for p in FORBIDDEN_PHRASES}
            sections_all_present = all(section_scan.values())
            forbidden_all_clean = not any(forbidden_scan.values())
        else:
            pages = None
            section_scan = {}
            forbidden_scan = {}
            sections_all_present = False
            forbidden_all_clean = False
            full_text = ""

        open_pdf_result = check_open_pdf_route(m["expected_filename"])

        result = {
            "matchup": matchup_key,
            "event_name": m["event_name"],
            "generation_ok": gen_ok,
            "pdf_path": pdf_path,
            "page_count_from_api": page_count_from_api,
            "page_count_from_pdf": pages,
            "sections_all_present": sections_all_present,
            "section_scan": section_scan,
            "forbidden_all_clean": forbidden_all_clean,
            "forbidden_scan": forbidden_scan,
            "governance": governance,
            "open_pdf_route": open_pdf_result,
        }
        results.append(result)
        status = "PASS" if (pages and pages >= 24 and sections_all_present and forbidden_all_clean) else "FAIL"
        print(f"  {status}: pages={pages}, sections_all_present={sections_all_present}, forbidden_clean={forbidden_all_clean}", flush=True)

    library_result = check_pdf_library_route()

    summary = {
        "all_generation_ok": all(r.get("generation_ok") for r in results),
        "all_24_plus_pages": all((r.get("page_count_from_pdf") or 0) >= 24 for r in results),
        "all_sections_present": all(r.get("sections_all_present") for r in results),
        "all_forbidden_clean": all(r.get("forbidden_all_clean") for r in results),
        "pdf_library_route": library_result,
    }

    output = {"summary": summary, "reports": results}
    print("\n--- JSON RESULT ---")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
