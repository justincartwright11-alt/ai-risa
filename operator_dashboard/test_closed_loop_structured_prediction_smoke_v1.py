from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
    generate_button2_report_render_gate_integration,
)
from operator_dashboard.button3_result_comparison_preview_v1 import (
    build_button3_result_comparison_preview,
)
from operator_dashboard.app import app, _build_button3_preview_input_from_generated_report, _build_button3_verified_result_handoff


def test_closed_loop_structured_prediction_contract_button2_to_button3_smoke(tmp_path) -> None:
    output_root = tmp_path / "pdf_output"
    output_root.mkdir()

    button2_request = {
        "operator_approved": True,
        "fight_id": "closed_loop_contract_fight",
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
                    "predicted_winner": "Fighter Beta",
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
    assert "structured_prediction" in button2_result
    structured_prediction = button2_result["structured_prediction"]
    assert structured_prediction["contract_version"] == "button2_structured_prediction_v1"

    button3_payload = _build_button3_preview_input_from_generated_report(
        button2_result,
        fight_id="closed_loop_contract_fight",
        matchup_id="closed_loop_contract_matchup",
        fighter_a="Fighter Alpha",
        fighter_b="Fighter Beta",
        event_name="Closed Loop Smoke Event",
    )
    assert button3_payload["report_id"]
    assert button3_payload["report_path"] == button2_result["output_path"]
    assert button3_payload["structured_prediction"] == structured_prediction

    verified_result_preview = {
        "fight_id": "closed_loop_contract_fight",
        "matchup_id": "closed_loop_contract_matchup",
        "fighter_a": "Fighter Alpha",
        "fighter_b": "Fighter Beta",
        "official_winner": "Fighter Beta",
        "official_method": "Decision",
        "official_round": "5",
        "official_time": "25:00",
        "official_result_source": "https://example.test/official-result",
        "result_verification_status": "verified",
        "source_tier": "official",
    }
    handoff = _build_button3_verified_result_handoff(button3_payload, verified_result_preview)
    assert handoff["ok"] is True
    assert handoff["report_provenance_preserved"] is True
    assert handoff["comparison_payload"]["structured_prediction"] == structured_prediction
    assert handoff["comparison_payload"]["actual_winner"] == "Fighter Beta"

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
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "source_conflict": True})["ok"] is False
    assert _build_button3_verified_result_handoff(button3_payload, {**verified_result_preview, "fighter_a": "Other Fighter"})["ok"] is False
    for flag in ("calibration_write_performed", "gcid_write_performed", "accuracy_ledger_mutation_performed", "customer_output_changed"):
        assert button3_result[flag] is False

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
    assert route_result.json["actual_winner"] == "Fighter Beta"
    assert route_result.json["actual_method"] == "Decision"
    assert route_result.json["actual_round"] == "5"
    assert route_result.json["mutation_performed"] is False
    assert route_result.json["learning_apply_performed"] is False
