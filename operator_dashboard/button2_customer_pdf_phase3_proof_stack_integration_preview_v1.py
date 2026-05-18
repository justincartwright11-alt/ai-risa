"""
Button 2 Customer PDF Phase 3 - Proof Stack Integration Preview v1

Fail-closed, governance-safe orchestrator that combines all seven proof-channel
signals into one fail-closed rendered-output proof stack result.

Reference: docs/button2-customer-pdf-phase3-proof-stack-integration-design-v1.md
Commit lock: 699a84b
"""


def run_proof_stack_integration(
    seven_proof_channels_results,
    stack_channel_available=True,
):
    """
    Combine all seven proof-channel signals into one fail-closed proof stack result.

    Args:
        seven_proof_channels_results: dict mapping channel_name -> proof_result dict
            Expected keys: text_extraction, geometry, page_section, typography_style,
            header_footer_watermark, source_traceability, visual_qa_rollup
        stack_channel_available: bool, default True (channel availability flag)

    Returns:
        dict with proof status, stack signal, aggregated failure reasons, and hard safety flags

    Each channel proof_result should have:
        - proof_status (str: passed | failed_closed)
        - {channel}_signal (str: clear | detected | unavailable)
        - failure_reasons (list of str)
        - pdf_generation_performed (bool: false)
        - file_write_performed (bool: false)
        - renderer_behavior_changed (bool: false)
        - dashboard_behavior_changed (bool: false)
        - delivery_workflow_changed (bool: false)
        - certification_automation_changed (bool: false)
    """

    result = {
        "schema_version": "button2.phase3.proof_stack_integration.v1",
        "proof_channel": "proof_stack_integration",
        "proof_status": "failed_closed",
        "stack_signal": "unavailable",
        "failure_reasons": [],
        "channel_signals": {
            "text_extraction": "unavailable",
            "geometry": "unavailable",
            "page_section": "unavailable",
            "typography_style": "unavailable",
            "header_footer_watermark": "unavailable",
            "source_traceability": "unavailable",
            "visual_qa_rollup": "unavailable",
        },
        "channel_failure_reasons": {
            "text_extraction": [],
            "geometry": [],
            "page_section": [],
            "typography_style": [],
            "header_footer_watermark": [],
            "source_traceability": [],
            "visual_qa_rollup": [],
        },
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    # Channel availability check
    if not stack_channel_available:
        result["stack_signal"] = "unavailable"
        result["failure_reasons"].append("stack_channel_unavailable")
        return result

    # Normalize inputs (raise RuntimeError on malformed shape)
    try:
        if not isinstance(seven_proof_channels_results, dict):
            raise RuntimeError("seven_proof_channels_results must be dict")

        required_channels = [
            "text_extraction",
            "geometry",
            "page_section",
            "typography_style",
            "header_footer_watermark",
            "source_traceability",
            "visual_qa_rollup",
        ]

        for channel_name in required_channels:
            if channel_name not in seven_proof_channels_results:
                raise RuntimeError(f"missing required channel: {channel_name}")

            channel_result = seven_proof_channels_results[channel_name]
            if not isinstance(channel_result, dict):
                raise RuntimeError(f"{channel_name} result must be dict")

            required_fields = [
                "proof_status",
                "failure_reasons",
                "pdf_generation_performed",
                "file_write_performed",
                "renderer_behavior_changed",
                "dashboard_behavior_changed",
                "delivery_workflow_changed",
                "certification_automation_changed",
            ]
            for field in required_fields:
                if field not in channel_result:
                    raise RuntimeError(f"{channel_name} result missing field: {field}")

            # Validate signal field name (e.g., text_extraction_signal)
            signal_field_name = f"{channel_name}_signal"
            if signal_field_name not in channel_result:
                raise RuntimeError(f"{channel_name} result missing {signal_field_name}")

            # Validate field types
            if not isinstance(channel_result["proof_status"], str):
                raise RuntimeError(f"{channel_name}.proof_status must be str")
            if channel_result["proof_status"] not in ["passed", "failed_closed"]:
                raise RuntimeError(
                    f"{channel_name}.proof_status must be 'passed' or 'failed_closed'"
                )
            if not isinstance(channel_result["failure_reasons"], list):
                raise RuntimeError(f"{channel_name}.failure_reasons must be list")
            if not isinstance(channel_result[signal_field_name], str):
                raise RuntimeError(f"{channel_name}.{signal_field_name} must be str")
            if channel_result[signal_field_name] not in [
                "clear",
                "detected",
                "unavailable",
            ]:
                raise RuntimeError(
                    f"{channel_name}.{signal_field_name} must be 'clear', 'detected', or 'unavailable'"
                )

    except RuntimeError:
        result["stack_signal"] = "unavailable"
        result["failure_reasons"].append("invalid_channel_result_shape")
        return result

    # Collect channel signals and failure reasons
    has_unavailable = False
    has_detected = False

    for channel_name in required_channels:
        channel_result = seven_proof_channels_results[channel_name]
        signal_field_name = f"{channel_name}_signal"
        channel_signal = channel_result[signal_field_name]

        # Record channel signal
        result["channel_signals"][channel_name] = channel_signal

        # Record channel failure reasons
        result["channel_failure_reasons"][channel_name] = channel_result.get(
            "failure_reasons", []
        )

        # Aggregate failure reasons
        for reason in channel_result.get("failure_reasons", []):
            result["failure_reasons"].append(reason)

        # Track signal states
        if channel_signal == "unavailable":
            has_unavailable = True
        elif channel_signal == "detected":
            has_detected = True

    # Determine stack signal (priority: unavailable > detected > clear)
    if has_unavailable:
        result["stack_signal"] = "unavailable"
    elif has_detected:
        result["stack_signal"] = "detected"
    else:
        result["stack_signal"] = "clear"

    # Determine proof status
    if result["stack_signal"] == "clear":
        result["proof_status"] = "passed"
    else:
        result["proof_status"] = "failed_closed"

    return result
