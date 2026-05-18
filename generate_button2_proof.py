"""Generate runtime proof for cover/depth repair."""
import json
import os
from pathlib import Path
from pypdf import PdfReader
from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

# Create proof directory
proof_dir = Path("ops/release_checks/button2_cover_visual_defect_and_content_depth_repair_v1")
proof_dir.mkdir(parents=True, exist_ok=True)
pdf_dir = proof_dir / "pdfs"
pdf_dir.mkdir(parents=True, exist_ok=True)

# Test cases
test_cases = [
    {
        "name": "Rico Verhoeven vs Tariq Osaro",
        "fighter_a": "Rico Verhoeven",
        "fighter_b": "Tariq Osaro",
        "event": "GLORY 100",
        "url": "https://www.glorykickboxing.com/events/glory-100",
    },
    {
        "name": "Anthony Joshua vs Daniel Dubois",
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "event": "Joshua vs Dubois",
        "url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    },
    {
        "name": "Jiri Prochazka vs Carlos Ulberg",
        "fighter_a": "Jiri Prochazka",
        "fighter_b": "Carlos Ulberg",
        "event": "UFC 320",
        "url": "https://www.ufc.com/event/ufc-320",
    },
]

app.config["TESTING"] = True
os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(pdf_dir.resolve())
os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

import datetime
evidence = {
    "slice": "button2-cover-visual-defect-and-content-depth-repair-v1",
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "test_results": []
}

with app.test_client() as client:
    for test_case in test_cases:
        preview = {
            "selected_for_button2": True,
            "selection_preview": True,
            "fighter_a": test_case["fighter_a"],
            "fighter_b": test_case["fighter_b"],
            "event_name": test_case["event"],
            "event_date": "2026-09-21",
            "promotion": "Premium Promotion",
            "source_type": "official",
            "source_url": test_case["url"],
            "report_ready_status": "ready_for_button2_preview",
        }

        response = client.post(
            "/api/button2/selected-matchup/generate-guarded-v1",
            data=json.dumps({"operator_approved": True, "selected_matchup_preview": preview}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.get_json()
            reader = PdfReader(data["output_path"])
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            
            result = {
                "name": test_case["name"],
                "status": "success",
                "page_count": len(reader.pages),
                "has_premium_branding": "AI-RISA" in text and "INTELLIGENCE" in text,
                "has_fighters": test_case["fighter_a"] in text and test_case["fighter_b"] in text,
                "has_confidence": any(w in text for w in ["confidence", "band", "%"]),
                "no_forbidden_strings": all(
                    forbidden.lower() not in text.lower()
                    for forbidden in ["Operator Summary Preview", "Template renderer profile"]
                ),
                "output_path": data["output_path"],
            }
        else:
            result = {
                "name": test_case["name"],
                "status": "failed",
                "error": response.get_json().get("error", "Unknown error"),
            }

        evidence["test_results"].append(result)

# Save evidence
evidence_path = proof_dir / "cover_depth_repair_evidence.json"
with open(evidence_path, "w") as f:
    json.dump(evidence, f, indent=2)

print(f"Evidence saved to {evidence_path}")
print(json.dumps(evidence, indent=2))
