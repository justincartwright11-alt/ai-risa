from pathlib import Path

from operator_dashboard.app import app


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "start_ai_risa_dashboard_windows.ps1"
RUNTIME_WARNING_TEXT = "PDF output root missing - start dashboard with Windows launch script."


def test_windows_launch_script_exists():
    assert SCRIPT_PATH.exists()


def test_windows_launch_script_contains_button2_output_root_setting():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "BUTTON2_PDF_OUTPUT_ROOT" in content


def test_windows_launch_script_contains_weasyprint_path():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert r"C:\msys64\ucrt64\bin" in content


def test_windows_launch_script_contains_add_dll_directory():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "os.add_dll_directory" in content


def test_missing_output_root_warning_is_rendered(monkeypatch):
    monkeypatch.delenv("BUTTON2_PDF_OUTPUT_ROOT", raising=False)
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert RUNTIME_WARNING_TEXT in html
    assert "id=\"b2-runtime-warning\"" in html


def test_runtime_warning_absent_when_output_root_is_configured(monkeypatch):
    monkeypatch.setenv(
        "BUTTON2_PDF_OUTPUT_ROOT",
        "C:/Users/jusin/OneDrive/Documents/Custom Office Templates/reports",
    )
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert RUNTIME_WARNING_TEXT not in html
