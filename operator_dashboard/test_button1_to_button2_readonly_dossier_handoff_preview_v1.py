from operator_dashboard.button1_to_button2_readonly_dossier_handoff_preview import (
    build_button1_to_button2_readonly_dossier_handoff_preview,
)


def test_builds_sanitized_readonly_handoff_payload():
    dossier_data = {
        "fighter_name": "Jon Jones",
        "promotion": "UFC",
        "division": "Light Heavyweight",
        "record": "27W-1L-0D",
        "confidence": "A+",
        "source": "approved_historical",
    }

    result = build_button1_to_button2_readonly_dossier_handoff_preview(dossier_data)

    expected_preview = (
        "Button1 Read-Only Dossier Handoff Preview\n"
        "Fighter: Jon Jones\n"
        "Promotion: UFC\n"
        "Division: Light Heavyweight\n"
        "Record: 27W-1L-0D\n"
        "Confidence: A+\n"
        "Source: approved_historical\n\n"
        "Read-only handoff preview for Button 2 context. No export, PDF, delivery, or mutation action was performed from Button 1."
    )

    assert result["destination_marker"] == "button2_report_generation_preview"
    assert result["dossier_summary_preview"] == expected_preview
    assert result["preview_only"] is True
    assert result["button1_export_performed"] is False
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["delivery_performed"] is False
    assert result["report_write_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False


def test_excludes_raw_internal_and_write_fields():
    dossier_data = {
        "fighter_name": "Jon Jones",
        "internal_notes": "do not leak",
        "write_authorized": True,
        "merge_instruction": "force",
        "database_pointer": "db://secret",
        "file_path_output": "C:/tmp/out.pdf",
        "delivery_target": "customer@email.com",
        "publish_instruction": "send_now",
        "auto_generate_report": True,
    }

    result = build_button1_to_button2_readonly_dossier_handoff_preview(dossier_data)
    preview_text = result["dossier_summary_preview"]

    assert "internal_notes" not in preview_text
    assert "do not leak" not in preview_text
    assert "write_authorized" not in preview_text
    assert "merge_instruction" not in preview_text
    assert "database_pointer" not in preview_text
    assert "file_path_output" not in preview_text
    assert "delivery_target" not in preview_text
    assert "publish_instruction" not in preview_text
    assert "auto_generate_report" not in preview_text


def test_escapes_html_xss_and_uses_safe_defaults():
    dossier_data = {
        "fighter_name": "<script>alert('x')</script>",
        "promotion": "",
        "division": None,
        "record": "<b>27W</b>",
    }

    result = build_button1_to_button2_readonly_dossier_handoff_preview(dossier_data)
    preview_text = result["dossier_summary_preview"]

    assert "<script>" not in preview_text
    assert "<b>" not in preview_text
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in preview_text
    assert "&lt;b&gt;27W&lt;/b&gt;" in preview_text
    assert "Promotion: Unknown Promotion" in preview_text
    assert "Division: Unknown Division" in preview_text
    assert "Confidence: Unknown" in preview_text
    assert "Source: Unknown Source" in preview_text


def test_non_dict_input_fails_closed_with_preview_only_flags():
    result = build_button1_to_button2_readonly_dossier_handoff_preview(None)

    assert result["destination_marker"] == "button2_report_generation_preview"
    assert "Unknown Fighter" in result["dossier_summary_preview"]
    assert result["preview_only"] is True
    assert result["button1_export_performed"] is False
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["delivery_performed"] is False
    assert result["report_write_performed"] is False
    assert result["profile_create_update_merge"] is False
    assert result["database_ranking_writes"] is False
    assert result["result_report_learning_calibration"] is False
