import json
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import (
    DEFAULT_TEMPLATE_PACK_ROOT,
    REQUIRED_MODULE,
    TemplatePackResolverError,
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


def test_template_pack_resolver_finds_default_root(monkeypatch):
    monkeypatch.delenv("BUTTON2_TEMPLATE_PACK_ROOT", raising=False)
    assets = resolve_template_pack_assets()

    assert assets["pack_root"] == DEFAULT_TEMPLATE_PACK_ROOT
    assert Path(assets["module_path"]).name == REQUIRED_MODULE
    assert os.path.exists(assets["module_path"])


def test_template_pack_resolver_supports_override(monkeypatch):
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)
    assets = resolve_template_pack_assets()

    assert assets["pack_root"] == DEFAULT_TEMPLATE_PACK_ROOT
    assert os.path.exists(assets["logo_path"])


def test_template_pack_resolver_missing_pack_fails_clearly(monkeypatch, tmp_path):
    missing_root = tmp_path / "missing_pack"
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", str(missing_root))

    try:
        resolve_template_pack_assets()
        assert False, "Expected TemplatePackResolverError"
    except TemplatePackResolverError as e:
        assert e.attempted_path == str(missing_root)
        assert e.cause == "missing_template_pack_root"


def test_template_pack_resolver_missing_required_assets_is_explicit(monkeypatch, tmp_path):
    bad_pack = tmp_path / "bad_pack"
    bad_pack.mkdir(parents=True, exist_ok=True)
    (bad_pack / "AI-RISA Logo.png").write_bytes(b"fake")
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", str(bad_pack))

    try:
        resolve_template_pack_assets()
        assert False, "Expected TemplatePackResolverError"
    except TemplatePackResolverError as e:
        assert e.cause == "missing_required_template_pack_assets"
        assert REQUIRED_MODULE in e.missing


def test_selected_matchup_generation_uses_asset_backed_template_and_preserves_links(monkeypatch, tmp_path):
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
        assert data["premium_template_render_used"] is True
        assert data["template_pack_asset_backed"] is True
        assert data["page_count"] >= 12
        assert data["delivery_performed"] is False
        assert data["external_api_delivery_performed"] is False
        assert data["queue_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False
        assert data["button3_mutation_performed"] is False

        open_response = client.get(data["pdf_open_url"])
        assert open_response.status_code == 200

        library_response = client.get(LIBRARY_ROUTE)
        assert library_response.status_code == 200
        library_html = library_response.data.decode("utf-8")
        assert data["output_filename"] in library_html

    output_path = data["output_path"]
    reader = PdfReader(output_path)
    assert len(reader.pages) >= 12

    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    assert "Anthony Joshua" in text
    assert "Daniel Dubois" in text
    assert "Source Traceability" in text
    assert "Selected Matchup Report Generation Context" not in text

    banned = [
        "Radar data unavailable",
        "Heat map data unavailable",
        "Control-shift data unavailable",
        "Method distribution data unavailable",
        "visual QA rollup status",
        "customer_ready_not_ready",
        "controlled_export_not_eligible",
        "valid layers",
        "missing layers",
        "overall visual confidence",
        "template renderer profile",
        "raw ingest mode",
    ]
    lower_text = text.lower()
    for phrase in banned:
        assert phrase.lower() not in lower_text


def test_library_and_dashboard_links_remain_visible_after_asset_renderer(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_TEMPLATE_PACK_ROOT", DEFAULT_TEMPLATE_PACK_ROOT)

    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "PDF Reports Folder" in html
    assert "Open PDF Reports Library" in html
    assert "/api/button2/generated-report/library" in html
