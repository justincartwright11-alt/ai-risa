import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from pypdf import PdfReader

BASE = "http://127.0.0.1:5050"
ROUTE = f"{BASE}/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = f"{BASE}/api/button2/generated-report/library"
OPEN_ROUTE = f"{BASE}/api/button2/generated-report/open"

ROOT = Path(r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates")
REPORTS_DIR = ROOT / "reports"
OUT_DIR = ROOT / "ops" / "release_checks" / "button2_global_selected_matchup_template_path_regression_fix_v1"
VISUAL_DIR = OUT_DIR / "visual_proof"
SUMMARY_PATH = OUT_DIR / "global_template_path_regression_summary.json"

TEMPLATE_PACK_ROOT = r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"

MATCHUPS = [
    (
        "Nadaka Yoshinari",
        "Songchainoi Kiatsongrit",
        "ONE Samurai 1",
        "https://www.onefc.com/events/one-samurai-1",
    ),
    (
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
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

FORBIDDEN = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "Cover Page",
    "Premium Cover",
    "SOURCE TRACEABILITY Source Traceability",
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
    "visual QA rollup",
    "template renderer profile",
    "raw ingest mode",
    "valid layers",
    "missing layers",
]

REQUIRED = [
    "PREMIUM FIGHT INTELLIGENCE REPORT",
    "THE INTELLIGENCE BENEATH THE VIOLENCE",
    "Fight Intelligence Dashboard",
    "HEADLINE PREDICTION",
    "Control Zone",
    "Danger Zone",
    "Collapse Trigger",
    "CONTROL LENS",
    "DANGER LENS",
    "COMMAND READ",
    "Traceability / Source Map",
    "Disclaimer / Risk Control",
]

PAGE_MAP = [
    (0, "cover"),
    (1, "dashboard"),
    (3, "matchup_fighter_overview"),
    (5, "tactical_edge"),
    (8, "body_risk_heat_map"),
    (22, "source_map"),
    (23, "disclaimer"),
]


def slug(*parts):
    return re.sub(r"[^a-z0-9]+", "_", "_".join(parts).lower()).strip("_")


def post_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def get_status(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, response.read()


def render_page_png(pdf_path: Path, page_index: int, out_png: Path):
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    pix.save(str(out_png))
    doc.close()


def build_contact_sheet(image_paths, out_path: Path):
    thumbs = []
    for image_path in image_paths:
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((540, 370))
        canvas = Image.new("RGB", (580, 410), (18, 22, 28))
        canvas.paste(image, ((580 - image.width) // 2, 16))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 380), Path(image_path).stem, fill=(220, 220, 220))
        thumbs.append(canvas)

    columns = 2
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 580, rows * 410), (10, 12, 16))
    for index, thumb in enumerate(thumbs):
        x = (index % columns) * 580
        y = (index // columns) * 410
        sheet.paste(thumb, (x, y))
    sheet.save(out_path)


def _target_pdf_filename(fighter_a: str, fighter_b: str, event_name: str) -> str:
    fight_id = slug(fighter_a, "vs", fighter_b, event_name)
    return f"{fight_id}_premium.pdf"


def delete_stale_reports():
    deleted = []
    for fighter_a, fighter_b, event_name, _ in MATCHUPS:
        filename = _target_pdf_filename(fighter_a, fighter_b, event_name)
        candidate = REPORTS_DIR / filename
        if candidate.exists():
            candidate.unlink()
            deleted.append(str(candidate))
    return deleted


def normalize_path(path_value: str) -> str:
    return os.path.normcase(os.path.normpath(path_value.strip()))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VISUAL_DIR.mkdir(parents=True, exist_ok=True)

    deleted_reports = delete_stale_reports()

    library_status, _ = get_status(LIBRARY_ROUTE)

    rows = []
    for fighter_a, fighter_b, event_name, source_url in MATCHUPS:
        payload = {
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
            },
        }

        status_code, data = post_json(ROUTE, payload)
        if status_code != 200 or not data.get("ok"):
            raise RuntimeError(f"Generation failed for {fighter_a} vs {fighter_b}: {status_code} {data}")

        pdf_path = Path(data["output_path"])
        reader = PdfReader(str(pdf_path))
        full_text = "\n".join((page.extract_text() or "") for page in reader.pages)
        lower = full_text.lower()

        forbidden_hits = {token: (token.lower() in lower) for token in FORBIDDEN}
        required_hits = {token: (token in full_text) for token in REQUIRED}

        open_url = f"{OPEN_ROUTE}?filename={urllib.parse.quote(data['output_filename'])}"
        open_status, _ = get_status(open_url)

        mslug = slug(fighter_a, fighter_b, event_name)
        image_paths = []
        for page_index, label in PAGE_MAP:
            out_png = VISUAL_DIR / f"{mslug}_p{page_index + 1:02d}_{label}.png"
            render_page_png(pdf_path, page_index, out_png)
            image_paths.append(out_png)

        contact_sheet = VISUAL_DIR / f"{mslug}_contact_sheet.png"
        build_contact_sheet(image_paths, contact_sheet)

        row = {
            "matchup": f"{fighter_a} vs {fighter_b}",
            "event": event_name,
            "output_path": str(pdf_path),
            "output_filename": data.get("output_filename"),
            "page_count_pdf": len(reader.pages),
            "page_count_api": data.get("page_count"),
            "renderer_profile": data.get("renderer_profile"),
            "premium_template_render_used": data.get("premium_template_render_used"),
            "template_pack_root": data.get("template_pack_root"),
            "template_pack_root_expected": TEMPLATE_PACK_ROOT,
            "template_pack_root_matches": normalize_path(str(data.get("template_pack_root", ""))) == normalize_path(TEMPLATE_PACK_ROOT),
            "required_hits": required_hits,
            "forbidden_hits": forbidden_hits,
            "all_required_present": all(required_hits.values()),
            "all_forbidden_absent": not any(forbidden_hits.values()),
            "open_route_status": open_status,
            "governance": {
                "delivery_performed": data.get("delivery_performed"),
                "external_api_delivery_performed": data.get("external_api_delivery_performed"),
                "queue_write_performed": data.get("queue_write_performed"),
                "learning_apply_performed": data.get("learning_apply_performed"),
                "calibration_write_performed": data.get("calibration_write_performed"),
                "button3_mutation_performed": data.get("button3_mutation_performed"),
            },
            "visual_proof": {
                "images": [str(p) for p in image_paths],
                "contact_sheet": str(contact_sheet),
            },
        }
        rows.append(row)

    summary = {
        "slice": "button2-global-selected-matchup-template-path-regression-fix-v1",
        "deleted_stale_reports": deleted_reports,
        "library_route_status": library_status,
        "reports": rows,
        "all_24_pages": all(item["page_count_pdf"] == 24 for item in rows),
        "all_required_present": all(item["all_required_present"] for item in rows),
        "all_forbidden_absent": all(item["all_forbidden_absent"] for item in rows),
        "all_open_routes_200": all(item["open_route_status"] == 200 for item in rows),
        "all_template_pack_root_matches": all(item["template_pack_root_matches"] for item in rows),
        "all_governance_false": all(all(flag is False for flag in item["governance"].values()) for item in rows),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
