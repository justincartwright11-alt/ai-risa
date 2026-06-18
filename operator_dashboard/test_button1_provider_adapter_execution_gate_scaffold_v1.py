from operator_dashboard.button1_provider_adapter_execution_gate_v1 import (
    ALLOWED_SOURCE_BUTTON,
    evaluate_button1_provider_adapter_execution_gate,
)


def test_gate_scaffold_defaults_to_deny_even_with_valid_inputs():
    result = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": ALLOWED_SOURCE_BUTTON,
            "provider_id": "ufc_official_events",
            "operator_approval_token": "preview-token",
            "provider_enabled": True,
        }
    )

    assert result["execution_gate_checked"] is True
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_scaffold_default_deny" in result["execution_gate_reason_codes"]


def test_gate_scaffold_denies_when_source_button_invalid():
    result = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": "button2_generate_reports",
            "provider_id": "ufc_official_events",
            "operator_approval_token": "preview-token",
            "provider_enabled": True,
        }
    )

    assert result["execution_gate_allowed"] is False
    assert "execution_gate_invalid_source_button" in result["execution_gate_reason_codes"]


def test_gate_scaffold_denies_when_provider_not_enabled():
    result = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": ALLOWED_SOURCE_BUTTON,
            "provider_id": "ufc_official_events",
            "operator_approval_token": "preview-token",
            "provider_enabled": False,
        }
    )

    assert result["execution_gate_allowed"] is False
    assert "execution_gate_provider_not_enabled" in result["execution_gate_reason_codes"]


def test_gate_scaffold_can_emit_allow_decision_in_preview_shape_only():
    result = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": ALLOWED_SOURCE_BUTTON,
            "provider_id": "ufc_official_events",
            "operator_approval_token": "preview-token",
            "provider_enabled": True,
            "enable_preview_allow_decision": True,
        }
    )

    assert result["execution_gate_allowed"] is True
    assert result["execution_gate_decision"] == "allow"


def test_gate_scaffold_never_performs_execution_or_writes_or_promotion():
    result = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": ALLOWED_SOURCE_BUTTON,
            "provider_id": "ufc_official_events",
            "operator_approval_token": "preview-token",
            "provider_enabled": True,
            "enable_preview_allow_decision": True,
        }
    )

    assert result["provider_execution_performed"] is False
    assert result["network_calls_performed"] is False
    assert result["source_calls_performed"] is False
    assert result["scraping_performed"] is False
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False
    assert result["button2_promotion_performed"] is False
