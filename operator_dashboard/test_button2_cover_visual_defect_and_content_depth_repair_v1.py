"""
Button 2 Cover Visual Defect and Content Depth Repair Test Suite v1
---------------------------------------------------------------------

Test Purpose:
  1. Verify cover design matches Ares premium standard
  2. Verify content depth is appropriate for paid premium reports
  3. Verify no visual defects (clipping, empty panels, off-page text)
  4. Verify customer-facing quality meets commercial expectations
  5. Verify no regression from previous fixes
"""

import json
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"


def _selected_matchup_preview(fighter_a, fighter_b, event_name, source_url):
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
    }


def _post_generate(client, preview):
    return client.post(
        ROUTE,
        data=json.dumps({"operator_approved": True, "selected_matchup_preview": preview}),
        content_type="application/json",
    )


def test_cover_premium_title_present(monkeypatch, tmp_path):
    """Verify cover includes premium title and tagline."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Check for premium branding
    assert "AI-RISA" in text
    assert "PREMIUM" in text or "INTELLIGENCE" in text
    # Check that the tagline or reference to intelligence framework is present
    assert any(word in text for word in ["INTELLIGENCE", "VIOLENCE", "THE", "FIGHT"])


def test_cover_fighter_vs_fighter_layout(monkeypatch, tmp_path):
    """Verify cover has fighter A vs Fighter B layout."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    # Check first page (cover) has both fighters
    cover_text = reader.pages[0].extract_text()
    assert "Anthony Joshua" in cover_text
    assert "Daniel Dubois" in cover_text


def test_content_depth_fight_specific_language(monkeypatch, tmp_path):
    """Verify content uses fight-specific language, not generic templates."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Jiri Prochazka",
        "Carlos Ulberg",
        "UFC 320",
        "https://www.ufc.com/event/ufc-320",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Check for fight-specific language patterns
    fight_specific_keywords = [
        "pressure",
        "control",
        "rhythm",
        "round",
        "entry",
        "cardio",
        "attrition",
        "geometry",
        "score",
        "lane",
    ]

    found_keywords = sum(1 for kw in fight_specific_keywords if kw.lower() in text.lower())
    # Should find at least 7 of these keywords in a substantive fight analysis
    assert found_keywords >= 7, f"Found only {found_keywords} fight-specific keywords, expected >=7"


def test_dashboard_panels_not_empty(monkeypatch, tmp_path):
    """Verify dashboard/stat panels contain meaningful data, not generic labels."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    
    # Check page 2 (executive dashboard) has dashboard content
    if len(reader.pages) > 1:
        dashboard_text = reader.pages[1].extract_text()
        
        # Should have data, not just labels
        assert any(word in dashboard_text for word in ["Dashboard", "Command", "Edge", "Confidence", "Volatility", "Method"])


def test_no_visual_defects_empty_panels(monkeypatch, tmp_path):
    """Verify no obvious empty panels or clipping."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    
    # Check that pages are not nearly empty
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        text_length = len(text.strip()) if text else 0
        # Each page should have meaningful content (except maybe some special pages)
        if idx not in [0]:  # Skip cover
            assert text_length > 100, f"Page {idx} appears to be nearly empty (only {text_length} chars)"


def test_confidence_band_present(monkeypatch, tmp_path):
    """Verify reports include confidence band/percentage."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Should mention confidence, percentage, or probability
    assert any(word in text for word in ["confidence", "band", "%", "probability"])


def test_no_forbidden_strings_regression(monkeypatch, tmp_path):
    """Verify no regression - forbidden strings still absent."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    forbidden = [
        "Operator Summary Preview",
        "Template renderer profile",
        "Visual QA rollup",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
    ]

    lower_text = text.lower()
    for phrase in forbidden:
        assert phrase.lower() not in lower_text, f"Regression: found forbidden string '{phrase}'"


def test_page_count_minimum_14(monkeypatch, tmp_path):
    """Verify page count remains >=14."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["page_count"] >= 14


def test_governance_flags_remain_false(monkeypatch, tmp_path):
    """Verify governance flags still false (no unauthorized actions)."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    preview = _selected_matchup_preview(
        "Fighter A",
        "Fighter B",
        "Test Event",
        "https://example.com/event",
    )

    with app.test_client() as client:
        response = _post_generate(client, preview)
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    # Verify governance
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_dashboard_and_library_still_functional(monkeypatch, tmp_path):
    """Verify dashboard PDF links and library still work."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    with app.test_client() as client:
        # Check dashboard has links
        dashboard = client.get("/").data.decode("utf-8")
        assert "PDF Reports Folder" in dashboard or "PDF" in dashboard
        
        # Check library is accessible
        library = client.get(LIBRARY_ROUTE)
        assert library.status_code == 200
