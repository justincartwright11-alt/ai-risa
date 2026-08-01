from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
    generate_button2_report_render_gate_integration,
)
from operator_dashboard.button3_result_comparison_preview_v1 import (
    build_button3_result_comparison_preview,
)
from operator_dashboard.app import app, _build_button3_preview_input_from_generated_report, _build_button3_verified_result_handoff
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_button1_runtime_context_preview,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"
TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"


def test_closed_loop_structured_prediction_contract_button2_to_button3_smoke(tmp_path) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    button1_fixture = fixture["button1"]
    button2_fixture = fixture["button2"]
    button3_fixture = fixture["button3"]
    assert fixture["fixture_only"] is True
    assert button1_fixture["operator_approved"] is True
    assert button1_fixture["button2_readiness_status"] == "READY_FOR_BUTTON_2"
    assert button2_fixture["provenance_status"] == "fixture_only_immutable"
    assert button2_fixture["customer_release_authorized"] is False
    assert button2_fixture["internal_preview_selectable"] is True
    assert button2_fixture["report_id"] == "internal_fixture_report_closed_loop_v1"
    assert button2_fixture["report_version"] == "DRAFT_INTERNAL_FIXTURE_v1"
    assert button2_fixture["prediction_schema_version"] == "button2_structured_prediction_v1"
    assert button2_fixture["structured_prediction"]["predicted_winner"] == button2_fixture["fighter_b"]
    assert button2_fixture["structured_prediction"]["contract_version"] == button2_fixture["prediction_schema_version"]
    assert button2_fixture["prediction_provenance"] == "fixture_only_immutable"
    assert button2_fixture["source_provenance"] == "fixture_only_immutable"
    assert button3_fixture["fixture_only"] is True
    assert button3_fixture["internal_test_only"] is True
    assert button3_fixture["read_only"] is True

    with patch.dict(
        os.environ,
        {
            "AI_RISA_LOCAL_FIXTURE_MODE": "1",
            "AI_RISA_BUTTON2_QUEUE_PATH": str(FIXTURE_PATH),
        },
    ):
        button1_context = build_button1_runtime_context_preview()
        button1_payload = button1_context.input_ref["payload"]
        assert button1_payload["live_source_status"]["fixture_id"] == fixture["fixture_id"]
        assert button1_payload["live_source_status"]["internal_test_only"] is True
        assert button1_payload["live_source_status"]["read_only"] is True
        assert button1_payload["live_source_status"]["customer_release_authorized"] is False
        assert button1_payload["live_source_status"]["save_allowed"] is False
        assert button1_payload["live_source_status"]["would_write_count"] == 0
        assert button1_payload["candidate_rows"][0]["candidate_id"] == button1_fixture["candidate_id"]
        assert button1_payload["candidate_rows"][0]["fighter_a"] == button1_fixture["fighter_a"]
        assert button1_payload["candidate_rows"][0]["fighter_b"] == button1_fixture["fighter_b"]
        assert button1_payload["candidate_rows"][0]["button2_readiness_status"] == "ready_for_button2_preview"
        assert button1_payload["candidate_rows"][0]["provenance_status"] != "provenance_missing"

        with app.test_client() as client:
            queue_result = client.get("/api/button2/queue-ready")
    assert queue_result.status_code == 200
    queue_data = queue_result.json
    assert queue_data["ready_count"] == 0
    assert queue_data["internal_preview_count"] == 1
    internal_preview = queue_data["internal_preview_rows"][0]
    assert internal_preview["internal_preview_selectable"] is True
    assert internal_preview["customer_ready_possible"] is False
    assert internal_preview["report_id"] == button2_fixture["report_id"]
    assert internal_preview["report_version"] == button2_fixture["report_version"]
    assert internal_preview["prediction_schema_version"] == button2_fixture["prediction_schema_version"]
    assert internal_preview["structured_prediction"] == button2_fixture["structured_prediction"]
    assert internal_preview["prediction_provenance"] == button2_fixture["prediction_provenance"]
    assert internal_preview["source_provenance"] == button2_fixture["source_provenance"]
    assert internal_preview["queue_write_performed"] is False
    assert internal_preview["pdf_generation_performed"] is False
    assert internal_preview["permanent_mutation_performed"] is False
    assert queue_data["total_rows"] == 1
    assert queue_data["queue_rows"][0]["provenance_status"] == "fixture_only_immutable"
    assert queue_data["queue_rows"][0]["customer_release_authorized"] is False
    assert queue_data["queue_rows"][0]["read_only"] is True

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "Governed Internal Report Preview" in template
    assert "button2InternalPreviewRows" in template
    assert "button2SelectInternalPreview" in template
    assert "Select Internal Preview for Button 3" in template
    assert "button3SelectedGeneratedReportPreview =" in template
    assert "report_version" in template and "prediction_schema_version" in template
    assert "prediction_provenance" in template and "source_provenance" in template
    assert "internal_preview_selectable === true" in template
    assert "internal_test_only === true" in template and "read_only === true" in template
    assert "customer_release_authorized === false" in template
    assert "pdf_generation_performed: false" in template
    assert "queue_write_performed: false" in template
    assert "permanent_mutation_performed: false" in template
    assert "learning_applied: false" in template
    assert "calibration_applied: false" in template
    assert "accuracy_ledger_written: false" in template
    assert "gcid_written: false" in template
    assert "panel.style.display = 'none'" in template
    assert "b3-verified-result-selector" in template
    assert "button3LoadVerifiedResultPreviews" in template
    assert "button3VerifiedResultPreviews" in template

    from operator_dashboard.button2_queue_loader_readonly_v1 import (
        get_button2_queue_loader_metadata,
        load_button2_queue_readonly,
    )

    metadata = get_button2_queue_loader_metadata()
    assert metadata["mode"] == "governed_local_fixture"
    assert metadata["fixture_id"] == fixture["fixture_id"]
    assert metadata["row_count"] == 1
    assert metadata["read_only"] is True

    with patch.dict(
        os.environ,
        {
            "AI_RISA_LOCAL_FIXTURE_MODE": "1",
            "AI_RISA_BUTTON2_QUEUE_PATH": str(FIXTURE_PATH),
        },
    ):
        loaded_preview = load_button2_queue_readonly()[0]
    assert loaded_preview["report_id"] == button2_fixture["report_id"]
    assert loaded_preview["report_version"] == button2_fixture["report_version"]
    assert loaded_preview["structured_prediction"] == button2_fixture["structured_prediction"]

    with patch.dict(os.environ, {"AI_RISA_LOCAL_FIXTURE_MODE": "1", "AI_RISA_BUTTON2_QUEUE_PATH": str(FIXTURE_PATH)}):
        with app.test_client() as client:
            result_preview_response = client.post(
                "/api/operator/button3/auto-result-source-yield-live-executor-preview",
                json={"limit": 200},
            )
    assert result_preview_response.status_code == 200
    result_preview_rows = result_preview_response.json["rows"]
    assert len(result_preview_rows) == 1
    result_preview = result_preview_rows[0]
    assert result_preview["result_preview_id"] == button3_fixture["result_preview_id"]
    assert result_preview["matchup_id"] == button2_fixture["matchup_id"]
    assert result_preview["fighter_a"] == button2_fixture["fighter_a"]
    assert result_preview["fighter_b"] == button2_fixture["fighter_b"]
    assert result_preview["official_result_source"] == button3_fixture["official_result_source"]
    assert result_preview["result_verification_status"] == "verified"
    assert result_preview["immutable_result_provenance"] == "fixture_only_immutable"
    assert result_preview["internal_test_only"] is True
    assert result_preview["read_only"] is True

    with patch.dict(os.environ, {}, clear=True):
        assert isinstance(load_button2_queue_readonly(), list)
        assert get_button2_queue_loader_metadata()["mode"] == "canonical_queue"
        default_button1_context = build_button1_runtime_context_preview()
        default_button1_status = default_button1_context.input_ref["payload"]["live_source_status"]
        assert default_button1_status.get("fixture_id") is None
        assert default_button1_status.get("feed_status") != "governed_local_fixture_loaded"

    with patch.dict(
        os.environ,
        {
            "AI_RISA_LOCAL_FIXTURE_MODE": "1",
            "AI_RISA_BUTTON2_QUEUE_PATH": str(tmp_path / "outside.json"),
        },
        clear=False,
    ):
        assert load_button2_queue_readonly() == []
        assert get_button2_queue_loader_metadata()["blocked_reason"] == "local_fixture_path_outside_fixtures"

    with patch.dict(os.environ, {"AI_RISA_LOCAL_FIXTURE_MODE": "1"}, clear=True):
        assert load_button2_queue_readonly() == []
        assert get_button2_queue_loader_metadata()["blocked_reason"] == "local_fixture_path_required"

        invalid_button1_context = build_button1_runtime_context_preview()
        invalid_button1_payload = invalid_button1_context.input_ref["payload"]
        assert invalid_button1_payload["candidate_rows"] == []
        assert invalid_button1_payload["live_source_status"]["feed_status"] == "unavailable"
        assert invalid_button1_payload["live_source_status"]["fallback_used"] is False

    output_root = tmp_path / "pdf_output"
    output_root.mkdir()

    button2_request = {
        "operator_approved": True,
        "fight_id": button1_fixture["candidate_id"],
        "matchup_id": button2_fixture["matchup_id"],
        "event_name": button2_fixture["event_name"],
        "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
    }

    mock_ingest = MagicMock(
        return_value={
            "ok": True,
            "button2_ingest_preview_context": {
                "destination_marker": "button2_report_generation_preview",
                "selected_matchup_payload": {
                    "fighter_a": "Fighter Alpha",
                    "fighter_b": "Fighter Beta",
                },
            },
        }
    )

    mock_context = MagicMock(
        return_value={
            "ok": True,
            "report_context_preview": {
                "destination_marker": "button2_report_generation_preview",
                "selected_matchup": {
                    "fighter_a": "Fighter Alpha",
                    "fighter_b": "Fighter Beta",
                },
                "prediction_context": {
                    "predicted_winner": button2_fixture["fighter_b"],
                    "predicted_method": "Decision",
                    "predicted_round": "R5",
                    "confidence": 64.2,
                    "structural_reasoning": "Beta wins second-phase exchanges by forcing reset reads.",
                    "tactical_pathway": "Pressure to fence breaks, then exit on angle before counters set.",
                    "evidence_notes": "source:https://example.test/closed-loop-proof",
                },
            },
        }
    )

    mock_render_template_pack = MagicMock(
        return_value={
            "pdf_bytes": b"SMOKE_TEST_NON_PDF_BYTES_OK",
            "renderer_profile": "premium_template_pack_v29_asset_backed_v1",
            "template_pack_root": "C:/tmp/template_pack",
            "template_pack_asset_backed": True,
            "template_pack_assets": {},
            "page_count": 24,
            "layout_safety": {},
            "prediction_context": {},
        }
    )

    with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
        with patch(
            "operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview",
            mock_ingest,
        ):
            with patch(
                "operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview",
                mock_context,
            ):
                with patch(
                    "operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_template_pack_asset_pdf",
                    mock_render_template_pack,
                ):
                    button2_result = generate_button2_report_render_gate_integration(button2_request)

    assert button2_result["ok"] is True
    assert button2_request["operator_approved"] is True
    assert button2_request["fight_id"] == button1_fixture["candidate_id"]
    assert button2_request["matchup_id"] == button2_fixture["matchup_id"]
    assert "structured_prediction" in button2_result
    structured_prediction = button2_result["structured_prediction"]
    assert structured_prediction["contract_version"] == "button2_structured_prediction_v1"
    assert button2_result["generation_request_id"] or button2_result["output_path"]
    assert button2_result["customer_approved"] is True

    button3_payload = _build_button3_preview_input_from_generated_report(
        button2_result,
        fight_id=button2_request["fight_id"],
        matchup_id=button2_request["matchup_id"],
        fighter_a=button2_fixture["fighter_a"],
        fighter_b=button2_fixture["fighter_b"],
        event_name=button2_request["event_name"],
    )
    assert button3_payload["report_id"]
    assert button3_payload["report_path"] == button2_result["output_path"]
    assert button3_payload["structured_prediction"] == structured_prediction
    assert button3_payload["prediction_provenance"] == "button2_generated_report"
    assert button3_payload["fight_id"] == button2_request["fight_id"]
    assert button3_payload["fighter_a"] == button2_fixture["fighter_a"]
    assert button3_payload["fighter_b"] == button2_fixture["fighter_b"]

    verified_result_preview = result_preview
    handoff = _build_button3_verified_result_handoff(button3_payload, verified_result_preview)
    assert handoff["ok"] is True
    assert handoff["comparison_preview_only"] is True
    assert handoff["report_provenance_preserved"] is True
    assert handoff["verified_result_preview_preserved"] is True
    assert handoff["comparison_payload"]["structured_prediction"] == structured_prediction
    assert handoff["comparison_payload"]["actual_winner"] == button3_fixture["official_winner"]

    button3_payload = handoff["comparison_payload"]

    button3_result = build_button3_result_comparison_preview(button3_payload)

    assert button3_result["ok"] is True
    assert button3_result["predicted_winner"] == structured_prediction["predicted_winner"]
    assert button3_result["predicted_method"] == structured_prediction["predicted_method"]
    assert button3_result["predicted_round"] == "R5"

    assert button3_result["structured_prediction_context"] == {
        "source": "button2_structured_prediction_contract",
        "contract_version": "button2_structured_prediction_v1",
        "structural_reasoning_present": True,
        "tactical_pathway_present": True,
        "evidence_notes_present": True,
    }

    structural_evidence_preview = button3_result["structural_evidence_preview"]
    assert structural_evidence_preview["state"] == "supported"
    assert structural_evidence_preview["score"] == 1.0
    assert structural_evidence_preview["reason_code"] == "all_structural_fields_present"
    assert structural_evidence_preview["learning_eligibility_effect"] == "none"
    assert structural_evidence_preview["non_mutating"] is True

    assert button3_result["mutation_performed"] is False
    assert button3_result["database_write_performed"] is False
    assert button3_result["queue_write_performed"] is False
    assert button3_result["learning_apply_performed"] is False
    assert button3_result["button3_mutation_performed"] is False
    assert button3_result["controlled_learning_candidate_eligible"] is False
    learning_preview = button3_result["learning_recommendation_preview"]
    assert learning_preview["controlled_learning_status"] == "NO_LEARNING_NEEDED"
    assert learning_preview["error_diagnosis_category"] == "NO_ERROR_DETECTED"
    assert learning_preview["safety_flags"] == {
        "learning_preview_only": True,
        "learning_applied": False,
        "calibration_write_authorized": False,
        "accuracy_ledger_write_authorized": False,
        "gCID_write_authorized": False,
        "operator_approval_required": True,
    }
    assert button3_result["accuracy_preview"]["overall"] == "hit"
    assert button3_result["learning_recommendation_preview"]["what_ai_risa_got_right"]["winner_correctness"] is True
    assert button3_result["learning_recommendation_preview"]["operator_facing_summary"]
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "source_conflict": True})["ok"] is False
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "fighter_a": "Other Fighter"})["ok"] is False
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "official_result_source": ""})["reason"] == "missing_result_source"
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "result_verification_status": "pending"})["reason"] == "incomplete_result_verification"
    for flag in ("calibration_write_performed", "gcid_write_performed", "accuracy_ledger_mutation_performed", "customer_output_changed"):
        assert button3_result[flag] is False
    assert button3_result["preview_only"] is True
    assert button3_result["learning_apply_performed"] is False
    assert button3_result["calibration_write_performed"] is False
    assert button3_result["accuracy_ledger_write_performed"] is False
    assert button3_result["gcid_write_performed"] is False
    assert button3_result["customer_output_release_authorized"] is False
    assert button3_result["mutation_performed"] is False
    assert button3_result.get("model_weights_changed", False) is False
    assert button3_result.get("fighter_ratings_changed", False) is False
    assert button3_result.get("prediction_logic_changed", False) is False
    assert button3_result.get("permanent_mutation_performed", False) is False

    with app.test_client() as client:
        route_result = client.post(
            "/api/button3/result-comparison/preview-v1",
            json={
                **button3_payload,
                "official_winner": "Fighter Beta",
                "official_method": "Decision",
                "official_round": "5",
                "official_time": "25:00",
                "official_result_source": "https://example.test/official-result",
                "result_verification_status": "operator_entered",
                "source_tier": "official",
            },
        )
    assert route_result.status_code == 200
    assert route_result.json["actual_winner"] == button3_fixture["official_winner"]
    assert route_result.json["actual_method"] == "Decision"
    assert route_result.json["actual_round"] == "5"
    assert route_result.json["mutation_performed"] is False
    assert route_result.json["learning_apply_performed"] is False
