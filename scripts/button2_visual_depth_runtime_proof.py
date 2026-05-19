import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw

BASE = "http://127.0.0.1:5050"
ROUTE = f"{BASE}/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = f"{BASE}/api/button2/generated-report/library"
OPEN_ROUTE = f"{BASE}/api/button2/generated-report/open"

ROOT = Path(r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates")
REPORTS = ROOT / "reports"
OUT_DIR = ROOT / "ops" / "release_checks" / "button2_premium_pdf_fighter_overview_heatmap_visual_depth_v1"
VISUAL_DIR = OUT_DIR / "visual_proof"

MATCHUPS = [
    ("Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
    ("Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
]

REQUIRED = [
    "Fighter Overview",
    "Tale of the Tape",
    "Body Risk Heat Map",
    "Anatomical Risk Map",
    "model-derived",
    "Striking",
    "Cardio",
    "Defense",
    "Experience",
    "Round Control Graph",
    "Method Probability Chart",
    "Scenario Tree / Method Pathways",
]

FORBIDDEN = [
    "Premium Cover",
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
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

PAGE_MAP = [
    (0, "cover"),
    (1, "dashboard"),
    (3, "fighter_overview_tale_of_tape"),
    (8, "body_risk_anatomy_heat_map"),
    (5, "tactical_edge_table"),
    (13, "round_control_graph"),
    (22, "source_map"),
    (23, "disclaimer"),
]


def slug(*parts):
    return re.sub(r"[^a-z0-9]+", "_", "_".join(parts).lower()).strip("_")


def post_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def get_status(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def render_page_png(pdf_path: Path, page_index: int, out_png: Path):
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pix.save(str(out_png))
    doc.close()


def build_contact_sheet(images, out_path):
    thumbs = []
    for img_path in images:
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((520, 360))
        canvas = Image.new("RGB", (560, 400), (18, 22, 28))
        canvas.paste(im, ((560 - im.width) // 2, 20))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 370), Path(img_path).stem, fill=(220, 220, 220))
        thumbs.append(canvas)

    cols = 2
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 560, rows * 400), (10, 12, 16))
    for i, t in enumerate(thumbs):
        x = (i % cols) * 560
        y = (i // cols) * 400
        sheet.paste(t, (x, y))
    sheet.save(out_path)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VISUAL_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    # Ensure routes are live.
    lib_status, _ = get_status(LIBRARY_ROUTE)

    for fa, fb, event, source_url in MATCHUPS:
        payload = {
            "operator_approved": True,
            "selected_matchup_preview": {
                "selected_for_button2": True,
                "selection_preview": True,
                "fighter_a": fa,
                "fighter_b": fb,
                "event_name": event,
                "event_date": "2026-09-21",
                "promotion": "Premium Promotion",
                "source_type": "official",
                "source_url": source_url,
                "report_ready_status": "ready_for_button2_preview",
                "source_traceability": [
                    {
                        "id": "SRC-001",
                        "type": "official",
                        "tier": "official",
                        "url": source_url,
                        "date": "2026-09-21",
                        "discipline": "source traceable",
                    }
                ],
            },
        }
        code, data = post_json(ROUTE, payload)
        if code != 200 or not data.get("ok"):
            raise RuntimeError(f"Generation failed for {fa} vs {fb}: {code} {data}")

        pdf_path = Path(data["output_path"])
        reader = PdfReader(str(pdf_path))
        full_text = "\n".join((p.extract_text() or "") for p in reader.pages)
        lower = full_text.lower()

        required_hits = {m: (m in full_text) for m in REQUIRED}
        forbidden_hits = {m: (m.lower() in lower) for m in FORBIDDEN}

        open_url = f"{OPEN_ROUTE}?filename={urllib.parse.quote(data['output_filename'])}"
        open_status, _ = get_status(open_url)

        # Visual proof images.
        mslug = slug(fa, fb, event)
        pngs = []
        for page_idx, label in PAGE_MAP:
            out_png = VISUAL_DIR / f"{mslug}_p{page_idx+1:02d}_{label}.png"
            render_page_png(pdf_path, page_idx, out_png)
            pngs.append(out_png)

        sheet_path = VISUAL_DIR / f"{mslug}_contact_sheet.png"
        build_contact_sheet(pngs, sheet_path)

        all_results.append(
            {
                "matchup": f"{fa} vs {fb}",
                "event": event,
                "pdf_path": str(pdf_path),
                "output_filename": data["output_filename"],
                "page_count_api": data.get("page_count"),
                "page_count_pdf": len(reader.pages),
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
                    "page_images": [str(p) for p in pngs],
                    "contact_sheet": str(sheet_path),
                },
            }
        )

    summary = {
        "slice": "button2-premium-pdf-fighter-overview-heatmap-visual-depth-v1",
        "library_route_status": lib_status,
        "all_reports": all_results,
        "all_24_pages": all(r["page_count_pdf"] == 24 for r in all_results),
        "all_required_present": all(r["all_required_present"] for r in all_results),
        "all_forbidden_absent": all(r["all_forbidden_absent"] for r in all_results),
        "all_open_routes_200": all(r["open_route_status"] == 200 for r in all_results),
        "all_governance_false": all(
            all(v is False for v in r["governance"].values())
            for r in all_results
        ),
    }

    out_json = OUT_DIR / "fighter_overview_heatmap_visual_depth_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
