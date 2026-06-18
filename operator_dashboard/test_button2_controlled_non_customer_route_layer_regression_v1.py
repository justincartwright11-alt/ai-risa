from pathlib import Path

from operator_dashboard.app import app


OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"
REPO_ROOT = Path(__file__).resolve().parent.parent
CONTROLLED_FIXTURE_DIR = REPO_ROOT / "ops" / "release_checks" / "button2-controlled-fixture-render-smoke-proof-v1"
CONTROLLED_FIXTURE_PDF = CONTROLLED_FIXTURE_DIR / "controlled_fixture_render_smoke.pdf"
CONTROLLED_FIXTURE_SUMMARY = CONTROLLED_FIXTURE_DIR / "controlled_fixture_render_smoke_summary.json"
REPORTS_DIR = REPO_ROOT / "reports"
QUEUE_PATH = REPO_ROOT / "ops" / "prf_queue" / "button2_approved_fight_queue.json"


def _file_meta(path: Path):
    if not path.exists() or not path.is_file():
        return {
            "exists": False,
            "size_bytes": 0,
            "mtime_ns": None,
        }
    stat = path.stat()
    return {
        "exists": True,
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _dir_entries(path: Path):
    if not path.exists() or not path.is_dir():
        return []
    return sorted(child.name for child in path.iterdir() if child.is_file())


def _snapshot_state():
    return {
        "fixture_dir_entries": _dir_entries(CONTROLLED_FIXTURE_DIR),
        "fixture_pdf_meta": _file_meta(CONTROLLED_FIXTURE_PDF),
        "fixture_summary_meta": _file_meta(CONTROLLED_FIXTURE_SUMMARY),
        "reports_dir_entries": _dir_entries(REPORTS_DIR),
        "queue_meta": _file_meta(QUEUE_PATH),
    }


def test_open_route_serves_controlled_fixture_pdf_without_mutation(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(CONTROLLED_FIXTURE_DIR))

    before = _snapshot_state()

    with app.test_client() as client:
        response = client.get(
            OPEN_ROUTE,
            query_string={"filename": CONTROLLED_FIXTURE_PDF.name},
        )

    after = _snapshot_state()

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert len(response.data) == before["fixture_pdf_meta"]["size_bytes"]
    assert before["reports_dir_entries"] == after["reports_dir_entries"]
    assert before["queue_meta"] == after["queue_meta"]
    assert before["fixture_dir_entries"] == after["fixture_dir_entries"]
    assert before["fixture_pdf_meta"] == after["fixture_pdf_meta"]
    assert before["fixture_summary_meta"] == after["fixture_summary_meta"]


def test_library_route_lists_controlled_fixture_pdf_only_with_safe_open_link_without_mutation(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(CONTROLLED_FIXTURE_DIR))

    before = _snapshot_state()

    with app.test_client() as client:
        response = client.get(LIBRARY_ROUTE)

    after = _snapshot_state()
    html = response.data.decode("utf-8")
    safe_open_link = f"/api/button2/generated-report/open?filename={CONTROLLED_FIXTURE_PDF.name}"

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert "controlled_fixture_render_smoke.pdf" in html
    assert safe_open_link in html
    assert "controlled_fixture_render_smoke_summary.json" not in html
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert before["reports_dir_entries"] == after["reports_dir_entries"]
    assert before["queue_meta"] == after["queue_meta"]
    assert before["fixture_dir_entries"] == after["fixture_dir_entries"]
    assert before["fixture_pdf_meta"] == after["fixture_pdf_meta"]
    assert before["fixture_summary_meta"] == after["fixture_summary_meta"]