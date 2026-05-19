import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from pypdf import PdfReader

BASE = "http://127.0.0.1:5050"
ROUTE = f"{BASE}/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = f"{BASE}/api/button2/generated-report/library"
OPEN_ROUTE = f"{BASE}/api/button2/generated-report/open"

ROOT = Path(r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates")
REPORTS_DIR = ROOT / "reports"
OUT_DIR = ROOT / "ops" / "release_checks" / "button2_selected_matchup_live_route_output_path_repair_v1"
SUMMARY_PATH = OUT_DIR / "live_route_output_path_summary.json"

TEMPLATE_PACK_ROOT = r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"

MATCHUPS = [
    (
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    ),
    (
        "Nadaka Yoshinari",
        "Songchainoi Kiatsongrit",
        "ONE Samurai 1",
        "https://www.onefc.com/events/one-samurai-1",
    ),
    (
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    ),
    (
        "Alex Pereira",
        "Jiri Prochazka",
        "UFC 300",
        "https://www.ufc.com/event/ufc-300",
    ),
]


def slug(*parts):
    return re.sub(r"[^a-z0-9]+", "_", "_".join(parts).lower()).strip("_")


def request_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def request_get(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.status, response.read()


def delete_four_test_outputs():
    deleted = []
    if not REPORTS_DIR.exists():
        return deleted

    for fighter_a, fighter_b, event_name, _ in MATCHUPS:
        base = slug(fighter_a, "vs", fighter_b, event_name)
        patterns = [
            f"{base}_premium.pdf",
            f"{base}_premium_*.pdf",
        ]
        for pattern in patterns:
            for candidate in REPORTS_DIR.glob(pattern):
                if candidate.is_file():
                    candidate.unlink()
                    deleted.append(str(candidate))
    return deleted


def preview_payload(fighter_a, fighter_b, event_name, source_url):
    return {
        "operator_approved": True,
        "selected_matchup_preview": {
            "selected_for_button2": True,
            "selection_preview": True,
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "event_name": event_name,
            "event_date": "2026-09-21",
            "promotion": "Premium Promotion",
            "source_type": "official",
            "source_url": source_url,
            "report_ready_status": "ready_for_button2_preview",
            "matchup_id": slug(fighter_a, "vs", fighter_b),
        },
    }


def verify_pdf_text(output_path, fighter_a, fighter_b, event_name):
    reader = PdfReader(str(output_path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    lower = text.lower()
    return {
        "page_count": len(reader.pages),
        "fighter_a_present": fighter_a.lower() in lower,
        "fighter_b_present": fighter_b.lower() in lower,
        "event_present": event_name.lower() in lower,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Require fresh reachable live runtime.
    library_status, _ = request_get(LIBRARY_ROUTE)

    deleted = delete_four_test_outputs()

    rows = []
    for fighter_a, fighter_b, event_name, source_url in MATCHUPS:
        status_code, data = request_json(ROUTE, preview_payload(fighter_a, fighter_b, event_name, source_url))
        if status_code != 200 or not data.get("ok"):
            raise RuntimeError(f"Generation failed for {fighter_a} vs {fighter_b}: {status_code} {data}")

        output_path = Path(data["output_path"])
        open_url = f"{OPEN_ROUTE}?filename={urllib.parse.quote(data['output_filename'])}"
        open_status, _ = request_get(open_url)

        pdf_check = verify_pdf_text(output_path, fighter_a, fighter_b, event_name)
        forbidden_scan = data.get("text_scan_forbidden_markers", {})

        row = {
            "matchup": f"{fighter_a} vs {fighter_b}",
            "event": event_name,
            "status_code": status_code,
            "output_path": str(output_path),
            "output_filename": data.get("output_filename"),
            "pdf_open_url": data.get("pdf_open_url"),
            "renderer_route_used": data.get("renderer_route_used"),
            "renderer_profile": data.get("renderer_profile"),
            "template_pack_root": data.get("template_pack_root"),
            "template_pack_asset_backed": data.get("template_pack_asset_backed"),
            "jbalia_layout_applied": data.get("jbalia_layout_applied"),
            "generation_request_id": data.get("generation_request_id"),
            "generated_at": data.get("generated_at"),
            "file_modified_at": data.get("file_modified_at"),
            "file_size_bytes": data.get("file_size_bytes"),
            "response_page_count": data.get("page_count"),
            "pdf_page_count": pdf_check["page_count"],
            "selected_matchup_matches_pdf_text_response": data.get("selected_matchup_matches_pdf_text"),
            "selected_matchup_matches_pdf_text_verified": (
                pdf_check["fighter_a_present"] and pdf_check["fighter_b_present"] and pdf_check["event_present"]
            ),
            "stale_file_reused": data.get("stale_file_reused"),
            "forbidden_scan": forbidden_scan,
            "open_route_status": open_status,
            "governance": {
                "delivery_performed": data.get("delivery_performed"),
                "external_api_delivery_performed": data.get("external_api_delivery_performed"),
                "queue_write_performed": data.get("queue_write_performed"),
                "learning_apply_performed": data.get("learning_apply_performed"),
                "calibration_write_performed": data.get("calibration_write_performed"),
                "button3_mutation_performed": data.get("button3_mutation_performed"),
            },
        }
        rows.append(row)

    library_status_after, library_body = request_get(LIBRARY_ROUTE)
    library_html = library_body.decode("utf-8", errors="ignore")

    summary = {
        "slice": "button2-selected-matchup-live-route-output-path-repair-v1",
        "deleted_test_outputs": deleted,
        "library_route_status_before": library_status,
        "library_route_status_after": library_status_after,
        "reports": rows,
        "all_fresh_unique_filenames": all("_premium_" in str(r.get("output_filename", "")) for r in rows),
        "all_renderer_route_template_pack": all(r.get("renderer_route_used") == "template_pack_asset_renderer" for r in rows),
        "all_template_pack_root_expected": all(r.get("template_pack_root") == TEMPLATE_PACK_ROOT for r in rows),
        "all_template_pack_asset_backed": all(r.get("template_pack_asset_backed") is True for r in rows),
        "all_jbalia_layout_applied": all(r.get("jbalia_layout_applied") is True for r in rows),
        "all_24_pages": all(r.get("response_page_count") == 24 and r.get("pdf_page_count") == 24 for r in rows),
        "all_selected_matchup_integrity": all(
            r.get("selected_matchup_matches_pdf_text_response") is True and r.get("selected_matchup_matches_pdf_text_verified") is True
            for r in rows
        ),
        "all_stale_reuse_false": all(r.get("stale_file_reused") is False for r in rows),
        "all_forbidden_absent": all(not bool(r.get("forbidden_scan", {}).get("any_forbidden_found")) for r in rows),
        "all_open_routes_200": all(r.get("open_route_status") == 200 for r in rows),
        "all_library_listings_present": all(str(r.get("output_filename", "")) in library_html for r in rows),
        "all_governance_false": all(all(v is False for v in r.get("governance", {}).values()) for r in rows),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
