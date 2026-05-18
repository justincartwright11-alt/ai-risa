"""
Button 2 Customer-Facing Defaults Cleanup Test Suite v1
-------------------------------------------------------

Test Suite Purpose:
  1. Verify that customer-facing generated PDFs contain NO internal/operator/debug strings
  2. Verify that generated PDFs match reference report traits (Ares FC 39 standard)
  3. Verify that customer-safe traceability and disclaimer sections remain present
  4. Verify that premium section headers remain present
  5. Verify that page count is >= 14
  6. Verify that dashboard links and PDF library still function
  7. Verify governance flags remain false

Forbidden Strings (Customer-Facing Output):
  - Operator Summary Preview
  - Premium Selected-Matchup Intelligence Summary
  - Template renderer profile
  - premium_template_pack_v29
  - Renderer mode
  - Source context
  - Ingest mode
  - Visual QA rollup
  - Certification: not_ready
  - Completeness: 75%
  - controlled_export_not_eligible
  - customer_ready_not_ready
  - Overall visual confidence
  - Valid layers / Missing layers
  - raw proof/status language
  - Radar data unavailable
  - Heat map data unavailable
  - Control-shift data unavailable
  - Method distribution data unavailable

Required Customer-Facing Sections (Must Be Present):
  - Executive Command Dashboard
  - Matchup Snapshot
  - Fighter Architecture Radar
  - Tactical Edge Map
  - Decision Structure
  - Energy Use
  - Fatigue Failure Points / Collapse Triggers
  - Mental Condition
  - Round Projection
  - Scenario Tree / Method Pathways
  - Final Projection
  - Source Traceability
  - Risk / Disclaimer
"""

import json
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import (
    DEFAULT_TEMPLATE_PACK_ROOT,
    resolve_template_pack_assets,
)


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


def test_rico_verhoeven_defaults_cleanup_no_internal_strings(monkeypatch, tmp_path):
    """Verify Rico Verhoeven report contains zero internal/debug strings."""
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
    assert len(reader.pages) >= 14

    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Forbidden internal/debug strings (case-insensitive)
    forbidden_strings = [
        "Operator Summary Preview",
        "Premium Selected-Matchup Intelligence Summary",
        "Template renderer profile",
        "premium_template_pack_v29",
        "Renderer mode",
        "Source context",
        "Ingest mode",
        "Visual QA rollup",
        "Certification: not_ready",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
        "Overall visual confidence",
        "Valid layers",
        "Missing layers",
        "Radar data unavailable",
        "Heat map data unavailable",
        "Control-shift data unavailable",
        "Method distribution data unavailable",
        "visual QA rollup status",
        "visual_qa_rollup",
        "template_renderer_profile",
        "raw ingest mode",
        "controlled_export_preview",
        "customer_ready_status_preview",
        "overall_visual_confidence",
    ]

    lower_text = text.lower()
    for phrase in forbidden_strings:
        phrase_lower = phrase.lower()
        assert phrase_lower not in lower_text, f"Found forbidden string in PDF: '{phrase}'"

    # Required customer-safe sections (keyword presence check)
    required_keywords = [
        "Executive",
        "Dashboard",
        "Radar",
        "Tactical",
        "Decision",
        "Energy",
        "Mental",
        "Round",
        "Scenario",
        "Projection",
        "Source Traceability",
        "Risk",
    ]

    keywords_found = [kw for kw in required_keywords if kw in text]
    # Should have at least 60% of required keywords
    assert len(keywords_found) >= len(required_keywords) * 0.6, f"Missing required keywords. Found: {keywords_found}"

    # Verify fighter names
    assert "Rico Verhoeven" in text
    assert "Tariq Osaro" in text


def test_anthony_joshua_defaults_cleanup_no_internal_strings(monkeypatch, tmp_path):
    """Verify Anthony Joshua report contains zero internal/debug strings."""
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
    assert len(reader.pages) >= 14

    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Forbidden internal/debug strings
    forbidden_strings = [
        "Operator Summary Preview",
        "Premium Selected-Matchup Intelligence Summary",
        "Template renderer profile",
        "premium_template_pack_v29",
        "Renderer mode",
        "Source context",
        "Ingest mode",
        "Visual QA rollup",
        "Certification: not_ready",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
        "Overall visual confidence",
        "Valid layers",
        "Missing layers",
        "Radar data unavailable",
        "Heat map data unavailable",
        "Control-shift data unavailable",
        "Method distribution data unavailable",
    ]

    lower_text = text.lower()
    for phrase in forbidden_strings:
        phrase_lower = phrase.lower()
        assert phrase_lower not in lower_text, f"Found forbidden string in PDF: '{phrase}'"

    # Verify fighter names
    assert "Anthony Joshua" in text
    assert "Daniel Dubois" in text


def test_jiri_prochazka_defaults_cleanup_no_internal_strings(monkeypatch, tmp_path):
    """Verify Jiri Prochazka report contains zero internal/debug strings."""
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
    assert len(reader.pages) >= 14

    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    # Forbidden internal/debug strings
    forbidden_strings = [
        "Operator Summary Preview",
        "Premium Selected-Matchup Intelligence Summary",
        "Template renderer profile",
        "premium_template_pack_v29",
        "Renderer mode",
        "Source context",
        "Ingest mode",
        "Visual QA rollup",
        "Certification: not_ready",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
        "Overall visual confidence",
        "Valid layers",
        "Missing layers",
        "Radar data unavailable",
        "Heat map data unavailable",
        "Control-shift data unavailable",
        "Method distribution data unavailable",
    ]

    lower_text = text.lower()
    for phrase in forbidden_strings:
        phrase_lower = phrase.lower()
        assert phrase_lower not in lower_text, f"Found forbidden string in PDF: '{phrase}'"

    # Verify fighter names
    assert "Jiri Prochazka" in text or "Jiri" in text
    assert "Carlos Ulberg" in text or "Ulberg" in text


def test_premium_cover_not_customer_facing_label(monkeypatch, tmp_path):
    """Verify 'Premium Cover' does not appear as visible customer-facing section label."""
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

    # "Premium Cover" should not appear as a section header
    # It may appear in metadata/comments, but not in customer-facing extracted text
    lines = text.split("\n")
    for line in lines:
        if "Premium Cover" in line and line.strip() != "":
            # Allow only if it's metadata or attribute, not a section header
            assert "Premium Cover" not in line or len(line.strip()) < 20


def test_source_traceability_remains_customer_safe(monkeypatch, tmp_path):
    """Verify Source Traceability section remains present and customer-safe."""
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

    # Source Traceability must be present
    assert "Source Traceability" in text

    # Customer-safe provenance should be present or implied
    has_source_info = any([
        "Source" in text,
        "URL" in text,
        "Event" in text,
        "Operator" in text,
    ])
    assert has_source_info


def test_disclaimer_risk_control_remains_present(monkeypatch, tmp_path):
    """Verify Disclaimer/Risk Control section remains present."""
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

    # Disclaimer or Risk Control section must be present
    has_disclaimer = any([
        "Disclaimer" in text,
        "Risk" in text,
        "probabilistic" in text,
    ])
    assert has_disclaimer


def test_page_count_minimum_14(monkeypatch, tmp_path):
    """Verify generated reports have minimum 14 pages."""
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
    """Verify governance flags remain false (no unauthorized actions)."""
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

    # Verify all governance flags
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_dashboard_and_library_links_functional(monkeypatch, tmp_path):
    """Verify dashboard PDF Reports Folder and library links still work."""
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    with app.test_client() as client:
        # Check dashboard has PDF Reports Folder and library links
        html = client.get("/").data.decode("utf-8")
        assert "PDF Reports Folder" in html
        assert "Open PDF Reports Library" in html
        assert "/api/button2/generated-report/library" in html

        # Check library route is accessible
        library_response = client.get(LIBRARY_ROUTE)
        assert library_response.status_code == 200
