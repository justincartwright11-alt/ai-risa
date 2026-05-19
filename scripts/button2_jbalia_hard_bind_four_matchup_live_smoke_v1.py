"""Live runtime smoke proof for four canonical matchups from the locked Jbalia hard-bind baseline."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

SLICE_NAME = "button2-jbalia-hard-bind-four-matchup-live-smoke-v1"
SLICE_DIR = Path(
    r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates\ops\release_checks\button2_jbalia_hard_bind_four_matchup_live_smoke_v1"
)
VISUAL_DIR = SLICE_DIR / "visual_proof"
OUTPUT_DIR = SLICE_DIR / "generated_pdfs"
SUMMARY_PATH = SLICE_DIR / "live_smoke_summary.json"

MATCHUPS = [
    ("rico", "Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
    ("anthony", "Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("alex", "Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
    ("nadaka", "Nadaka Yoshinari", "Songchainoi Kiatsongrit", "ONE Samurai 1", "https://www.onefc.com/events/one-samurai-1"),
]

REQUIRED_COVER_MARKERS = [
    "PREMIUM FIGHT",
    "INTELLIGENCE REPORT",
    "THE INTELLIGENCE BENEATH THE VIOLENCE",
    "CUSTOMER READY",
    "Report ID:",
    "Confidence:",
    "Generated:",
    "AI-RISA | COMBAT INTELLIGENCE | OPERATOR APPROVED | SOURCE TRACEABLE",
    "template_pack_sample",
]

REQUIRED_DASHBOARD_MARKERS = [
    "EXECUTIVE COMMAND DASHBOARD",
    "HEADLINE PREDICTION",
    "CONFIDENCE",
    "VOLATILITY",
    "EXECUTIVE SUMMARY",
    "CONTROL ZONE",
    "DANGER ZONE",
    "COLLAPSE TRIGGER",
    "FIGHT CONTROL INTELLIGENCE STRIP",
    "CONTROL THESIS",
    "FLIP POINT",
    "WATCH CUE",
    "COMMAND RULE",
    "ROUND CONTROL PROJECTION",
    "METHOD PROBABILITY",
    "RISK CONTROL",
]

FORBIDDEN = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "Cover Page",
    "Premium Cover",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Buyer Meaning / Coach Meaning",
]

VISUAL_TARGETS = [
    (0, "cover"),
    (1, "executive_dashboard"),
    (2, "headline_projection"),
    (3, "matchup_snapshot"),
    (4, "fighter_architecture_radar"),
    (5, "tactical_edge_map"),
    (13, "round_control_projection"),
    (15, "scorecard_scenario"),
    (22, "source_map"),
    (23, "disclaimer"),
]


def _preview_payload(fighter_a: str, fighter_b: str, event_name: str, source_url: str) -> dict:
    return {
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
        "matchup_id": f"{fighter_a.lower().replace(' ', '_')}_vs_{fighter_b.lower().replace(' ', '_')}",
    }


def _extract_text_and_pages(pdf_path: Path) -> tuple[str, int]:
    reader = PdfReader(str(pdf_path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text, len(reader.pages)


def _render_contact_sheet(pdf_path: Path, slug: str) -> dict:
    doc = fitz.open(str(pdf_path))
    thumbs = []
    for page_index, label in VISUAL_TARGETS:
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.22, 0.22), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        thumbs.append((label, image))
    doc.close()

    tile_w = max(img.width for _, img in thumbs)
    tile_h = max(img.height for _, img in thumbs)
    cols = 3
    rows = 4
    canvas = Image.new("RGB", (cols * tile_w + 40, rows * (tile_h + 28) + 24), color=(18, 24, 36))
    draw = ImageDraw.Draw(canvas)

    for i, (label, img) in enumerate(thumbs):
        r = i // cols
        c = i % cols
        x = 20 + c * tile_w
        y = 12 + r * (tile_h + 28)
        canvas.paste(img, (x, y))
        draw.text((x + 4, y + tile_h + 6), label, fill=(240, 240, 240))

    sheet_path = VISUAL_DIR / f"{slug}_contact_sheet.png"
    canvas.save(sheet_path)

    page_paths = {}
    for label, img in thumbs:
        out_path = VISUAL_DIR / f"{slug}_{label}.png"
        img.save(out_path)
        page_paths[label] = str(out_path)

    return {
        "contact_sheet": str(sheet_path),
        "pages": page_paths,
    }


def _all_governance_false(row: dict) -> bool:
    gov = row["governance"]
    return (
        gov["delivery_performed"] is False
        and gov["external_api_delivery_performed"] is False
        and gov["queue_write_performed"] is False
        and gov["learning_apply_performed"] is False
        and gov["calibration_write_performed"] is False
        and gov["button3_mutation_performed"] is False
    )


def main() -> int:
    SLICE_DIR.mkdir(parents=True, exist_ok=True)
    VISUAL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(OUTPUT_DIR)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    rows = []
    with app.test_client() as client:
        for slug, fighter_a, fighter_b, event_name, source_url in MATCHUPS:
            response = client.post(
                ROUTE,
                json={
                    "operator_approved": True,
                    "selected_matchup_preview": _preview_payload(fighter_a, fighter_b, event_name, source_url),
                },
            )
            data = response.get_json() or {}
            output_path = Path(str(data.get("output_path", "")))

            text = ""
            page_count = None
            cover_markers_ok = False
            dashboard_markers_ok = False
            forbidden_hits = []
            visual = {}

            if response.status_code == 200 and data.get("ok") and output_path.exists():
                text, page_count = _extract_text_and_pages(output_path)
                lower = text.lower()
                cover_markers_ok = all(marker in text for marker in REQUIRED_COVER_MARKERS)
                dashboard_markers_ok = all(marker in text for marker in REQUIRED_DASHBOARD_MARKERS)
                forbidden_hits = [m for m in FORBIDDEN if m.lower() in lower]
                visual = _render_contact_sheet(output_path, slug)

            open_status = None
            if data.get("output_filename"):
                open_resp = client.get(OPEN_ROUTE, query_string={"filename": data["output_filename"]})
                open_status = open_resp.status_code

            library_resp = client.get(LIBRARY_ROUTE)
            library_html = library_resp.data.decode("utf-8") if library_resp.status_code == 200 else ""
            listed = bool(data.get("output_filename") and data["output_filename"] in library_html)

            rows.append(
                {
                    "slug": slug,
                    "fighter_a": fighter_a,
                    "fighter_b": fighter_b,
                    "event_name": event_name,
                    "status_code": response.status_code,
                    "ok": bool(data.get("ok")),
                    "renderer_profile": data.get("renderer_profile"),
                    "renderer_route_used": data.get("renderer_route_used"),
                    "template_pack_root": data.get("template_pack_root"),
                    "output_filename": data.get("output_filename"),
                    "output_path": str(output_path),
                    "page_count": page_count,
                    "response_page_count": data.get("page_count"),
                    "stale_file_reused": data.get("stale_file_reused"),
                    "selected_matchup_matches_pdf_text": data.get("selected_matchup_matches_pdf_text"),
                    "cover_markers_ok": cover_markers_ok,
                    "dashboard_markers_ok": dashboard_markers_ok,
                    "forbidden_hits": forbidden_hits,
                    "open_route_status": open_status,
                    "library_status": library_resp.status_code,
                    "library_lists_exact_filename": listed,
                    "governance": {
                        "delivery_performed": data.get("delivery_performed"),
                        "external_api_delivery_performed": data.get("external_api_delivery_performed"),
                        "queue_write_performed": data.get("queue_write_performed"),
                        "learning_apply_performed": data.get("learning_apply_performed"),
                        "calibration_write_performed": data.get("calibration_write_performed"),
                        "button3_mutation_performed": data.get("button3_mutation_performed"),
                    },
                    "visual_proof": visual,
                }
            )

    summary = {
        "slice": SLICE_NAME,
        "active_baseline_tag": "button2-jbalia-template-sample-renderer-hard-bind-v1",
        "active_baseline_commit": "caba638",
        "non_regression_anchors": [
            {"tag": "button2-disable-section-card-engine-and-force-jbalia-premium-renderer-v1", "commit": "9adc303"},
            {"tag": "button2-selected-matchup-live-route-output-path-repair-v1", "commit": "e0a2fd0"},
        ],
        "template_pack_root": DEFAULT_TEMPLATE_PACK_ROOT,
        "reports": rows,
        "all_http_200": all(r["status_code"] == 200 for r in rows),
        "all_ok": all(r["ok"] for r in rows),
        "all_jbalia_renderer_profile": all(r["renderer_profile"] == "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1" for r in rows),
        "all_24_pages": all(r["page_count"] == 24 and r["response_page_count"] == 24 for r in rows),
        "all_stale_file_reused_false": all(r["stale_file_reused"] is False for r in rows),
        "all_selected_matchup_integrity_true": all(r["selected_matchup_matches_pdf_text"] is True for r in rows),
        "all_cover_markers_ok": all(r["cover_markers_ok"] for r in rows),
        "all_dashboard_markers_ok": all(r["dashboard_markers_ok"] for r in rows),
        "all_forbidden_absent": all(not r["forbidden_hits"] for r in rows),
        "all_open_route_200": all(r["open_route_status"] == 200 for r in rows),
        "all_library_route_200": all(r["library_status"] == 200 for r in rows),
        "all_library_list_exact_filename": all(r["library_lists_exact_filename"] is True for r in rows),
        "all_governance_false": all(_all_governance_false(r) for r in rows),
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    hard_stop_ok = (
        summary["all_http_200"]
        and summary["all_ok"]
        and summary["all_jbalia_renderer_profile"]
        and summary["all_24_pages"]
        and summary["all_stale_file_reused_false"]
        and summary["all_selected_matchup_integrity_true"]
        and summary["all_cover_markers_ok"]
        and summary["all_dashboard_markers_ok"]
        and summary["all_forbidden_absent"]
        and summary["all_open_route_200"]
        and summary["all_library_route_200"]
        and summary["all_library_list_exact_filename"]
        and summary["all_governance_false"]
    )

    print(f"Wrote summary: {SUMMARY_PATH}")
    if hard_stop_ok:
        print("LIVE SMOKE RESULT: PASS")
        return 0

    print("LIVE SMOKE RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
