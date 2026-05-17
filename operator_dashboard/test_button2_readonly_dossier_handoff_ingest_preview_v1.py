import socket

from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)


def _assert_zero_write_flags(result):
    assert result["preview_only"] is True
    assert result["button2_generation_performed"] is False
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert result["report_write_performed"] is False
    assert result["gate2_approval_required"] is True
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False


def test_builds_button2_ingest_preview_context_for_valid_handoff():
    payload = {
        "destination_marker": "button2_report_generation_preview",
        "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\\nFighter: Jon Jones",
        "internal_notes": "do not leak",
        "write_authorized": True,
    }

    result = build_button2_readonly_dossier_handoff_ingest_preview(payload)

    assert result["ok"] is True
    assert result["destination_marker"] == "button2_report_generation_preview"
    _assert_zero_write_flags(result)

    context = result["button2_ingest_preview_context"]
    assert context["destination_marker"] == "button2_report_generation_preview"
    assert context["ingest_mode"] == "preview_only"
    assert context["context_kind"] == "button1_dossier_handoff"
    assert "Jon Jones" in context["dossier_summary_preview"]

    assert "internal_notes" not in context
    assert "write_authorized" not in context


def test_rejects_invalid_destination_marker_fail_closed():
    payload = {
        "destination_marker": "button2_generate_now",
        "dossier_summary_preview": "unsafe marker",
    }

    result = build_button2_readonly_dossier_handoff_ingest_preview(payload)

    assert result["ok"] is False
    assert result["error"] == "invalid_destination_marker"
    assert result["button2_ingest_preview_context"] is None
    _assert_zero_write_flags(result)


def test_escapes_summary_and_excludes_raw_internal_write_fields():
    payload = {
        "destination_marker": "button2_report_generation_preview",
        "dossier_summary_preview": "<script>alert('x')</script>",
        "database_pointer": "db://secret",
        "merge_instruction": "force",
        "delivery_target": "customer@example.com",
        "file_path_output": "C:/tmp/report.pdf",
    }

    result = build_button2_readonly_dossier_handoff_ingest_preview(payload)

    assert result["ok"] is True
    context = result["button2_ingest_preview_context"]
    assert "<script>" not in context["dossier_summary_preview"]
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in context["dossier_summary_preview"]

    assert "database_pointer" not in context
    assert "merge_instruction" not in context
    assert "delivery_target" not in context
    assert "file_path_output" not in context


def test_no_filesystem_or_live_web_calls(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    result = build_button2_readonly_dossier_handoff_ingest_preview(
        {
            "destination_marker": "button2_report_generation_preview",
            "dossier_summary_preview": "safe",
        }
    )

    assert result["ok"] is True
    _assert_zero_write_flags(result)
