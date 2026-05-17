import socket

from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)


def _assert_preview_flags(result):
    assert result["preview_only"] is True
    assert result["report_context_preview_ready"] is True
    assert result["button2_generation_performed"] is False
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert result["report_write_performed"] is False
    assert result["gate2_approval_required"] is True
    assert result["gate2_bypass_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False


def test_builds_report_context_preview_from_ingest_context():
    payload = {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\\nFighter: Jon Jones",
        }
    }

    result = build_button2_dossier_handoff_report_context_preview(payload)

    assert result["ok"] is True
    assert result["destination_marker"] == "button2_report_generation_preview"
    _assert_preview_flags(result)

    report_context = result["report_context_preview"]
    assert report_context["destination_marker"] == "button2_report_generation_preview"
    assert report_context["report_context_kind"] == "dossier_handoff_report_context_preview"
    assert report_context["source_context_kind"] == "button1_dossier_handoff"
    assert report_context["source_ingest_mode"] == "preview_only"
    assert "Jon Jones" in report_context["handoff_summary_preview"]


def test_rejects_invalid_destination_marker_fail_closed():
    payload = {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_generate_now",
            "dossier_summary_preview": "invalid marker",
        }
    }

    result = build_button2_dossier_handoff_report_context_preview(payload)

    assert result["ok"] is False
    assert result["error"] == "invalid_destination_marker"
    assert result["report_context_preview"] is None
    assert result["preview_only"] is True
    assert result["report_context_preview_ready"] is False
    assert result["button2_generation_performed"] is False
    assert result["gate2_approval_required"] is True
    assert result["gate2_bypass_performed"] is False


def test_excludes_raw_internal_write_fields_and_preserves_summary_safely():
    payload = {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "<script>alert('x')</script>",
            "internal_notes": "do not leak",
            "write_authorized": True,
            "database_pointer": "db://secret",
            "merge_instruction": "force",
        }
    }

    result = build_button2_dossier_handoff_report_context_preview(payload)

    assert result["ok"] is True
    report_context = result["report_context_preview"]
    assert "<script>" not in report_context["handoff_summary_preview"]
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in report_context["handoff_summary_preview"]

    assert "internal_notes" not in report_context
    assert "write_authorized" not in report_context
    assert "database_pointer" not in report_context
    assert "merge_instruction" not in report_context


def test_no_filesystem_or_live_web_calls(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    result = build_button2_dossier_handoff_report_context_preview(
        {
            "button2_ingest_preview_context": {
                "destination_marker": "button2_report_generation_preview",
                "dossier_summary_preview": "safe",
            }
        }
    )

    assert result["ok"] is True
    _assert_preview_flags(result)
