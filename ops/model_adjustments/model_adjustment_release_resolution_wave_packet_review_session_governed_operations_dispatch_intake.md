# model_adjustment_release_resolution_wave_packet_review_session_governed_operations_dispatch_intake

Source artifact: `ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_routing_handoff.json`
Record count: 1

| Dispatch Intake ID | Source Routing-Handoff ID | Source Record Index |
|-------------------|--------------------------|---------------------|
| resolution-wave-packet-review-session-governed-operations-dispatch-intake-0001 | resolution-wave-packet-review-session-governed-operations-routing-handoff-0001 | 1 |

## resolution-wave-packet-review-session-governed-operations-dispatch-intake-0001
Source routing-handoff ID: resolution-wave-packet-review-session-governed-operations-routing-handoff-0001
Source record index: 1
Source artifact: `ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_routing_handoff.json`

```json
{
  "governed_operations_routing_handoff_id": "resolution-wave-packet-review-session-governed-operations-routing-handoff-0001",
  "source_governed_operations_routing_assessment_id": "resolution-wave-packet-review-session-governed-operations-routing-assessment-0001",
  "source_record_index": 1,
  "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_routing_assessment.json",
  "routing_assessment_record": {
    "governed_operations_routing_assessment_id": "resolution-wave-packet-review-session-governed-operations-routing-assessment-0001",
    "source_governed_operations_routing_intake_id": "resolution-wave-packet-review-session-governed-operations-routing-intake-0001",
    "source_record_index": 1,
    "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_routing_intake.json",
    "routing_intake_record": {
      "governed_operations_routing_intake_id": "resolution-wave-packet-review-session-governed-operations-routing-intake-0001",
      "source_governed_operations_receipt_handoff_id": "resolution-wave-packet-review-session-governed-operations-receipt-handoff-0001",
      "source_record_index": 1,
      "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_handoff.json",
      "receipt_handoff_record": {
        "governed_operations_receipt_handoff_id": "resolution-wave-packet-review-session-governed-operations-receipt-handoff-0001",
        "receipt_assessment_record": {
          "governed_operations_receipt_assessment_id": "resolution-wave-packet-review-session-governed-operations-receipt-assessment-0001",
          "receipt_intake_record": {
            "cadence_handoff_record": {
              "assessment_record": {
                "approval_requirement_trend": "provided_by_operator",
                "assessment_position": 1,
                "cadence_findings": [
                  "provided_by_operator"
                ],
                "deliverable_completion_trend": "provided_by_operator",
                "governance_reference": "resolution-wave-packet-review-session-operations-governance-handoff-0001",
                "governance_threshold_trend": "provided_by_operator",
                "governed_operations_cadence_assessment_id": "resolution-wave-packet-review-session-governed-operations-cadence-assessment-0001",
                "governed_operations_cadence_checkpoint_intake_id": "resolution-wave-packet-review-session-governed-operations-cadence-checkpoint-intake-0001",
                "incident_trend": "provided_by_operator",
                "intervention_trend": "provided_by_operator",
                "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_checkpoint_intake.json",
                "lineage_source_layer": "governed_operations_cadence_checkpoint_intake",
                "lineage_source_record_id": "resolution-wave-packet-review-session-governed-operations-cadence-checkpoint-intake-0001",
                "multi_cycle_stability_status": "provided_by_operator",
                "recommended_disposition": "provided_by_operator",
                "reviewed_cycle_references": [
                  "resolution-wave-packet-review-session-governed-operations-cycle-closeout-0001",
                  "resolution-wave-packet-review-session-governed-operations-cycle-2-closeout-0001",
                  "resolution-wave-packet-review-session-governed-operations-cycle-3-closeout-0001"
                ],
                "rollback_trend": "provided_by_operator"
              },
              "cadence_handoff_id": "resolution-wave-packet-review-session-governed-operations-cadence-handoff-0001",
              "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_assessment.json",
              "source_cadence_assessment_id": "resolution-wave-packet-review-session-governed-operations-cadence-assessment-0001",
              "source_record_index": 1
            },
            "governed_operations_receipt_intake_id": "resolution-wave-packet-review-session-governed-operations-receipt-intake-0001",
            "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_cadence_handoff.json",
            "source_governed_operations_cadence_handoff_id": "resolution-wave-packet-review-session-governed-operations-cadence-handoff-0001",
            "source_record_index": 1
          },
          "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_intake.json",
          "source_governed_operations_receipt_intake_id": "resolution-wave-packet-review-session-governed-operations-receipt-intake-0001",
          "source_record_index": 1
        },
        "source_artifact": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_receipt_assessment.json",
        "source_governed_operations_receipt_assessment_id": "resolution-wave-packet-review-session-governed-operations-receipt-assessment-0001",
        "source_record_index": 1
      }
    }
  }
}
```
