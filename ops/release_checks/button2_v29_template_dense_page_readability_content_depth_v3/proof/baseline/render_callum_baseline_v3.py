from pathlib import Path
import json
import sys
import fitz
from PIL import Image, ImageDraw

root = Path(r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates")
sys.path.insert(0, str(root))
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer

queue_path = root / "ops" / "prf_queue" / "button2_approved_fight_queue.json"
out_dir = root / "ops" / "release_checks" / "button2_v29_template_dense_page_readability_content_depth_v3" / "proof" / "baseline"
out_dir.mkdir(parents=True, exist_ok=True)
reports = root / "reports"
reports.mkdir(parents=True, exist_ok=True)
payload = json.loads(queue_path.read_text(encoding="utf-8"))
rows = payload.get("queue", [])
row = next(r for r in rows if r.get("fighter_a") == "Callum Walsh" and r.get("fighter_b") == "Austin Williams")
preview = {
    "selected_matchup": {
        "fighter_a": row["fighter_a"],
        "fighter_b": row["fighter_b"],
        "event_name": row["event_name"],
        "event_date": row["event_date"],
        "promotion": row["promotion"],
        "source_url": row["source_url"],
        "source_type": row["source_type"],
    },
    "handoff_summary_preview": "Selected matchup handoff summary.",
    "source_traceability": [{
        "source_url": row["source_url"],
        "source_type": row["source_type"],
        "source_date": row["event_date"],
    }],
}
out = renderer.render_button2_template_pack_asset_pdf(preview)
pdf_path = reports / "callum_walsh_vs_austin_williams_joshua_vs_dubois_locked_baseline_v3.pdf"
pdf_path.write_bytes(out["pdf_bytes"])
page_map = [(1, "dashboard"), (5, "tactical_edge"), (13, "round_outlook"), (15, "scorecard"), (16, "stoppage"), (22, "source_map")]
doc = fitz.open(str(pdf_path))
thumbs = []
page_files = []
for idx, label in page_map:
    pix = doc.load_page(idx).get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    page_file = out_dir / f"callum_baseline_p{idx+1:02d}_{label}.png"
    pix.save(str(page_file))
    page_files.append(str(page_file))
    im = Image.open(page_file).convert("RGB")
    im.thumbnail((540, 370))
    canvas = Image.new("RGB", (580, 412), (18, 22, 28))
    canvas.paste(im, ((580 - im.width) // 2, 14))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 382), page_file.stem, fill=(220, 220, 220))
    thumbs.append(canvas)
cols = 2
rows_count = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 580, rows_count * 412), (10, 12, 16))
for i, thumb in enumerate(thumbs):
    sheet.paste(thumb, ((i % cols) * 580, (i // cols) * 412))
contact_sheet = out_dir / "callum_baseline_dense_page_contact_sheet.png"
sheet.save(contact_sheet)
print(json.dumps({
    "pdf_path": str(pdf_path),
    "contact_sheet": str(contact_sheet),
    "page_files": page_files,
    "layout_safety": out.get("layout_safety", {}),
}, indent=2))
