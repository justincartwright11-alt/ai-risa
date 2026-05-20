from __future__ import annotations

import io
import json
import math
from pathlib import Path
from urllib import error, request

import fitz
from PIL import Image, ImageDraw
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[5]
OUT_DIR = Path(__file__).resolve().parent
ROUTE = "http://127.0.0.1:5050/api/button2/generate-selected-batch"
PROOF_PAGES = [2, 6, 14, 16, 17, 23]
SCAFFOLD_MARKERS = [
    "operator note",
]
GENERIC_LENS_MARKERS = [
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
]

CASES = [
    {
        "slug": "callum_walsh_vs_austin_williams",
        "selected_matchup_preview": {
            "matchup_id": "joshua_vs_dubois_callum_walsh_vs_austin_williams",
            "event_id": "live_boxing_event_card_001",
            "event_name": "Joshua vs Dubois",
            "event_date": "2026-09-21",
            "promotion": "Matchroom Boxing",
            "fighter_a": "Callum Walsh",
            "fighter_b": "Austin Williams",
            "weight_class": "Super Welterweight",
            "bout_order": 3,
            "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
            "source_type": "official",
            "provenance_status": "source_backed_ready",
            "button2_readiness_status": "ready_for_button2_preview",
            "report_ready_status": "ready_for_button2_preview",
            "customer_ready_possible": True,
            "blocked_reason": "",
            "selected_for_button2": True,
            "approved_for_button2": True,
        },
    },
    {
        "slug": "ben_whittaker_vs_willy_hutchinson",
        "selected_matchup_preview": {
            "matchup_id": "joshua_vs_dubois_ben_whittaker_vs_willy_hutchinson",
            "event_id": "live_boxing_event_card_001",
            "event_name": "Joshua vs Dubois",
            "event_date": "2026-09-21",
            "promotion": "Matchroom Boxing",
            "fighter_a": "Ben Whittaker",
            "fighter_b": "Willy Hutchinson",
            "weight_class": "Light Heavyweight",
            "bout_order": 2,
            "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
            "source_type": "official",
            "provenance_status": "source_backed_ready",
            "button2_readiness_status": "ready_for_button2_preview",
            "report_ready_status": "ready_for_button2_preview",
            "customer_ready_possible": True,
            "blocked_reason": "",
            "selected_for_button2": True,
            "approved_for_button2": True,
        },
    },
    {
        "slug": "ryan_curtis_vs_adam_borics",
        "selected_matchup_preview": {
            "matchup_id": "bellator_298_ryan_curtis_adam_borics",
            "event_name": "Bellator 298",
            "event_date": "2026-06-15",
            "promotion": "Bellator",
            "fighter_a": "Ryan Curtis",
            "fighter_b": "Adam Borics",
            "weight_class": "Featherweight",
            "bout_order": 2,
            "source_url": "https://www.bellator.com/events/bellator-298",
            "source_type": "official",
            "provenance_status": "source_backed",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "customer_ready_possible": True,
            "blocked_reason": "",
            "selected_for_button2": True,
        },
    },
]


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=600) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from live route: {body}") from exc


def _extract_text(pdf_path: Path) -> tuple[str, int]:
    with pdf_path.open("rb") as handle:
        reader = PdfReader(handle)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return text, len(reader.pages)


def _render_proof_pages(pdf_path: Path, slug: str) -> tuple[list[str], str]:
    doc = fitz.open(pdf_path)
    images: list[Image.Image] = []
    png_paths: list[str] = []
    try:
        for page_no in PROOF_PAGES:
            page = doc.load_page(page_no - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            png_name = f"{slug}_p{page_no:02d}.png"
            png_path = OUT_DIR / png_name
            image.save(png_path)
            images.append(image)
            png_paths.append(str(png_path.relative_to(ROOT)).replace("\\", "/"))

        cols = 2
        rows = math.ceil(len(images) / cols)
        cell_w = max(image.width for image in images)
        cell_h = max(image.height for image in images)
        header_h = 40
        gap = 20
        sheet = Image.new(
            "RGB",
            (cols * cell_w + (cols + 1) * gap, rows * (cell_h + header_h) + (rows + 1) * gap),
            (247, 244, 236),
        )
        draw = ImageDraw.Draw(sheet)
        for index, image in enumerate(images):
            row = index // cols
            col = index % cols
            x = gap + col * (cell_w + gap)
            y = gap + row * (cell_h + header_h + gap)
            draw.rectangle((x, y, x + cell_w, y + header_h + cell_h), outline=(33, 33, 33), width=2)
            draw.text((x + 12, y + 10), f"Page {PROOF_PAGES[index]}", fill=(20, 20, 20))
            sheet.paste(image, (x, y + header_h))

        sheet_name = f"{slug}_dense_page_contact_sheet.png"
        sheet_path = OUT_DIR / sheet_name
        sheet.save(sheet_path)
        return png_paths, str(sheet_path.relative_to(ROOT)).replace("\\", "/")
    finally:
        doc.close()


def _find_markers(text: str, markers: list[str]) -> list[str]:
    text_lower = text.lower()
    return [marker for marker in markers if marker in text_lower]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "route": ROUTE,
        "proof_pages": PROOF_PAGES,
        "cases": [],
    }

    for case in CASES:
        payload = {
            "operator_approval": True,
            "selected_matchup_ids": [case["selected_matchup_preview"]["matchup_id"]],
        }
        response = _post_json(ROUTE, payload)
        if not response.get("ok"):
            raise RuntimeError(f"Live route failed for {case['slug']}: {response}")

        results = response.get("results", [])
        if not isinstance(results, list) or len(results) != 1:
            raise RuntimeError(f"Unexpected batch results for {case['slug']}: {response}")
        result = results[0]
        if not result.get("ok"):
            raise RuntimeError(f"Batch result failed for {case['slug']}: {result}")

        pdf_path = Path(result["output_path"])
        text, page_count = _extract_text(pdf_path)
        png_paths, contact_sheet = _render_proof_pages(pdf_path, case["slug"])
        layout_safety = result.get("layout_safety", {})
        lens_depth = layout_safety.get("lens_depth", {}) if isinstance(layout_safety, dict) else {}
        page_bounds = layout_safety.get("page_bounds", {}) if isinstance(layout_safety, dict) else {}
        footer_pages = layout_safety.get("footer_safe_zone_pages", {}) if isinstance(layout_safety, dict) else {}
        case_summary = {
            "slug": case["slug"],
            "fighter_a": case["selected_matchup_preview"]["fighter_a"],
            "fighter_b": case["selected_matchup_preview"]["fighter_b"],
            "event_name": case["selected_matchup_preview"]["event_name"],
            "customer_ready": result.get("customer_ready"),
            "visual_gate_status": result.get("visual_gate_status"),
            "output_path": str(pdf_path.relative_to(ROOT)).replace("\\", "/"),
            "output_filename": result.get("output_filename"),
            "report_id": result.get("report_id"),
            "page_count": page_count,
            "operator_note_hits": _find_markers(text, SCAFFOLD_MARKERS),
            "generic_lens_hits": _find_markers(text, GENERIC_LENS_MARKERS),
            "contains_fighter_a": case["selected_matchup_preview"]["fighter_a"].lower() in text.lower(),
            "contains_fighter_b": case["selected_matchup_preview"]["fighter_b"].lower() in text.lower(),
            "contains_event_name": case["selected_matchup_preview"]["event_name"].lower() in text.lower(),
            "contains_source_url": case["selected_matchup_preview"]["source_url"].lower() in text.lower(),
            "layout_safety": {
                "operator_note_absent_passed": layout_safety.get("operator_note_absent_passed"),
                "dashboard_lens_depth_passed": layout_safety.get("dashboard_lens_depth_passed"),
                "round_heading_body_clear_passed": layout_safety.get("round_heading_body_clear_passed"),
                "scorecard_readability_passed": layout_safety.get("scorecard_readability_passed"),
                "stoppage_readability_passed": layout_safety.get("stoppage_readability_passed"),
                "readable_min_font_passed": layout_safety.get("readable_min_font_passed"),
                "footer_safe_zone_passed": layout_safety.get("footer_safe_zone_passed"),
                "logo_blend_ok": layout_safety.get("logo_blend_ok"),
                "logo_black_tile_risk": layout_safety.get("logo_black_tile_risk"),
            },
            "lens_depth": lens_depth,
            "page_bounds": {key: page_bounds.get(key) for key in ("6", "14", "16", "17", "23")},
            "footer_safe_zone_pages": {key: footer_pages.get(key) for key in ("6", "16", "17")},
            "proof_png_paths": png_paths,
            "contact_sheet": contact_sheet,
        }
        summary["cases"].append(case_summary)

    summary_path = OUT_DIR / "live_proof_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())