import copy
import hashlib
import unittest
from pathlib import Path

from operator_dashboard.official_source_approved_apply_schema import (
    build_official_source_approved_apply_schema_response,
    validate_official_source_approved_apply_request,
)


class OfficialSourceApprovedApplySchemaTest(unittest.TestCase):
    def _valid_payload(self):
        return {
            "mode": "official_source_approved_apply",
            "lookup_intent": "apply_write",
            "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
            "approval_granted": True,
            "approval_token": "token_123",
            "approval_binding": {
                "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
                "citation_fingerprint": "abc123fingerprint",
                "source_url": "https://ufc.com/event/test-card",
                "source_date": "2026-04-20",
                "extracted_winner": "Alpha",
                "record_fight_id": "alpha_vs_beta",
                "selected_row_identity": {
                    "fight_name": "Alpha vs Beta",
                    "fight_id": "alpha_vs_beta",
                },
            },
            "preview_snapshot": {
                "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
                "manual_review_required": False,
                "source_citation": {
                    "source_url": "https://ufc.com/event/test-card",
                    "source_title": "UFC Test Card",
                    "source_date": "2026-04-20",
                    "publisher_host": "ufc.com",
                    "source_confidence": "tier_a0",
                    "confidence_score": 0.85,
                    "citation_fingerprint": "abc123fingerprint",
                    "extracted_winner": "Alpha",
                },
                "acceptance_gate": {
                    "state": "write_eligible",
                    "write_eligible": True,
                    "reason_code": "accepted_preview_write_eligible",
                    "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
                    "citation_fingerprint": "abc123fingerprint",
                },
                "audit": {
                    "record_fight_id": "alpha_vs_beta",
                    "provider_attempted": True,
                    "attempted_sources": ["https://ufc.com/event/test-card"],
                },
            },
        }

    def _sha256_or_none(self, path: Path):
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _actual_results_file_hashes(self):
        root = Path(__file__).resolve().parent.parent
        accuracy_dir = root / "ops" / "accuracy"
        targets = [
            accuracy_dir / "actual_results.json",
            accuracy_dir / "actual_results_manual.json",
            accuracy_dir / "actual_results_unresolved.json",
        ]
        return {str(path): self._sha256_or_none(path) for path in targets}

    def _assert_invariant_flags(self, result):
        self.assertFalse(result.get("mutation_performed"))
        self.assertFalse(result.get("bulk_lookup_performed"))
        self.assertFalse(result.get("scoring_semantics_changed"))
        self.assertFalse(result.get("write_performed"))

    def test_valid_minimal_payload_returns_request_valid_true(self):
        result = validate_official_source_approved_apply_request(self._valid_payload())
        self.assertTrue(result.get("request_valid"))
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "valid_schema")
        self.assertEqual(result.get("mode"), "official_source_approved_apply")
        self.assertEqual(result.get("phase"), "approved_apply")
        self.assertTrue(result.get("approval_required"))
        self.assertTrue(result.get("approval_granted"))
        self.assertFalse(result.get("manual_review_required"))
        self.assertIsNone(result.get("operation_id"))
        self._assert_invariant_flags(result)

    def test_valid_payload_with_operation_id_is_valid(self):
        payload = self._valid_payload()
        payload["operation_id"] = "op_retry_20260430_abcdef"
        result = validate_official_source_approved_apply_request(payload)
        self.assertTrue(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "valid_schema")
        self.assertEqual(result.get("operation_id"), "op_retry_20260430_abcdef")

    def test_operation_id_is_normalized_and_stripped(self):
        payload = self._valid_payload()
        payload["operation_id"] = "  op_retry_20260430_abcdef  "
        result = validate_official_source_approved_apply_request(payload)
        self.assertTrue(result.get("request_valid"))
        self.assertEqual(result.get("operation_id"), "op_retry_20260430_abcdef")

    def test_operation_id_non_string_rejected_with_malformed_field_type(self):
        payload = self._valid_payload()
        payload["operation_id"] = 12345
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "malformed_field_type")
        self._assert_invariant_flags(result)

    def test_operation_id_format_invalid_cases_rejected(self):
        invalid_values = [
            "short-id",
            "a" * 129,
            "operation id with spaces",
            "operation/id/with/slash",
            "operation\\id\\with\\backslash",
            "................",
        ]
        for value in invalid_values:
            with self.subTest(operation_id=value):
                payload = self._valid_payload()
                payload["operation_id"] = value
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertEqual(result.get("reason_code"), "operation_id_format_invalid")
                self._assert_invariant_flags(result)

    def test_build_response_helper_has_required_envelope(self):
        result = build_official_source_approved_apply_schema_response(
            request_valid=False,
            reason_code="invalid_request_body",
            errors=["payload malformed"],
            selected_key=None,
            approval_granted=False,
        )
        self.assertFalse(result.get("ok"))
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "invalid_request_body")
        self.assertEqual(result.get("mode"), "official_source_approved_apply")
        self.assertEqual(result.get("phase"), "approved_apply")
        self.assertTrue(result.get("approval_required"))
        self.assertTrue(result.get("manual_review_required"))
        self._assert_invariant_flags(result)

    def test_missing_mode_is_rejected(self):
        payload = self._valid_payload()
        payload.pop("mode")
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "invalid_apply_mode")
        self._assert_invariant_flags(result)

    def test_mode_mismatch_is_rejected(self):
        payload = self._valid_payload()
        payload["mode"] = "official_source_one_record"
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "invalid_apply_mode")

    def test_lookup_intent_mismatch_is_rejected(self):
        payload = self._valid_payload()
        payload["lookup_intent"] = "preview_only"
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "invalid_lookup_intent")

    def test_selected_key_missing_is_rejected(self):
        payload = self._valid_payload()
        payload.pop("selected_key")
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "selected_key_type_invalid")

    def test_selected_key_array_is_rejected(self):
        payload = self._valid_payload()
        payload["selected_key"] = ["one", "two"]
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertIn(result.get("reason_code"), {"single_record_required", "selected_key_type_invalid"})

    def test_approval_granted_false_is_rejected(self):
        payload = self._valid_payload()
        payload["approval_granted"] = False
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "approval_granted_required_true")

    def test_approval_token_missing_or_empty_is_rejected(self):
        for token_value in (None, "", "   "):
            with self.subTest(token_value=token_value):
                payload = self._valid_payload()
                payload["approval_token"] = token_value
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertEqual(result.get("reason_code"), "approval_token_missing")

    def test_approval_binding_missing_is_rejected(self):
        payload = self._valid_payload()
        payload.pop("approval_binding")
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "approval_binding_missing")

    def test_approval_binding_non_object_is_rejected(self):
        payload = self._valid_payload()
        payload["approval_binding"] = "bad"
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "approval_binding_type_invalid")

    def test_each_required_approval_binding_field_omission_is_rejected(self):
        required_fields = (
            "selected_key",
            "citation_fingerprint",
            "source_url",
            "source_date",
            "extracted_winner",
        )
        for field in required_fields:
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload["approval_binding"].pop(field)
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertEqual(result.get("reason_code"), "approval_binding_field_missing")

    def test_selected_row_identity_shape_is_enforced(self):
        payload = self._valid_payload()
        payload["approval_binding"]["selected_row_identity"] = "bad"
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "malformed_field_type")

        payload = self._valid_payload()
        payload["approval_binding"]["selected_row_identity"].pop("fight_name")
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "approval_binding_field_missing")

    def test_preview_snapshot_missing_is_rejected(self):
        payload = self._valid_payload()
        payload.pop("preview_snapshot")
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "preview_snapshot_missing")

    def test_preview_snapshot_non_object_is_rejected(self):
        payload = self._valid_payload()
        payload["preview_snapshot"] = "bad"
        result = validate_official_source_approved_apply_request(payload)
        self.assertFalse(result.get("request_valid"))
        self.assertEqual(result.get("reason_code"), "preview_snapshot_type_invalid")

    def test_each_required_preview_snapshot_field_omission_is_rejected(self):
        for field in ("selected_key", "manual_review_required", "source_citation", "acceptance_gate", "audit"):
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload["preview_snapshot"].pop(field)
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertIn(result.get("reason_code"), {"preview_snapshot_field_missing", "malformed_field_type"})

    def test_each_required_preview_source_citation_field_omission_is_rejected(self):
        for field in (
            "source_url",
            "source_title",
            "source_date",
            "publisher_host",
            "source_confidence",
            "confidence_score",
            "citation_fingerprint",
            "extracted_winner",
        ):
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload["preview_snapshot"]["source_citation"].pop(field)
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertIn(result.get("reason_code"), {"preview_snapshot_field_missing", "malformed_field_type"})

    def test_each_required_preview_acceptance_gate_field_omission_is_rejected(self):
        for field in ("state", "write_eligible", "reason_code", "selected_key", "citation_fingerprint"):
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload["preview_snapshot"]["acceptance_gate"].pop(field)
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertIn(result.get("reason_code"), {"preview_snapshot_field_missing", "malformed_field_type"})

    def test_each_required_preview_audit_field_omission_is_rejected(self):
        for field in ("record_fight_id", "provider_attempted", "attempted_sources"):
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload["preview_snapshot"]["audit"].pop(field)
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertIn(result.get("reason_code"), {"preview_snapshot_field_missing", "malformed_field_type"})

    def test_each_forbidden_batch_field_is_rejected(self):
        forbidden = [
            "selected_keys",
            "targets",
            "batch_size",
            "execution_token",
            "apply_all",
            "queue_wide",
            "queue_scope",
        ]
        for field in forbidden:
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload[field] = True
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertEqual(result.get("reason_code"), "batch_field_not_allowed")

    def test_each_unsafe_override_field_is_rejected(self):
        forbidden = [
            "force_write",
            "skip_validation",
            "bypass_gate",
            "bypass_approval",
            "write_target_override",
            "scoring_override",
        ]
        for field in forbidden:
            with self.subTest(field=field):
                payload = self._valid_payload()
                payload[field] = True
                result = validate_official_source_approved_apply_request(payload)
                self.assertFalse(result.get("request_valid"))
                self.assertEqual(result.get("reason_code"), "mutation_override_not_allowed")

    def test_every_invalid_result_has_invariant_false_mutation_flags(self):
        invalid_payloads = []

        payload = self._valid_payload()
        payload["mode"] = "bad"
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["lookup_intent"] = "bad"
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["selected_key"] = ["bad"]
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["approval_granted"] = False
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["approval_token"] = ""
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["approval_binding"] = "bad"
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["preview_snapshot"] = "bad"
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["selected_keys"] = ["bad"]
        invalid_payloads.append(payload)

        payload = self._valid_payload()
        payload["force_write"] = True
        invalid_payloads.append(payload)

        for idx, invalid_payload in enumerate(invalid_payloads):
            with self.subTest(index=idx):
                result = validate_official_source_approved_apply_request(invalid_payload)
                self.assertFalse(result.get("request_valid"))
                self._assert_invariant_flags(result)

    def test_schema_tests_do_not_modify_actual_results_files(self):
        before_hashes = self._actual_results_file_hashes()

        _ = validate_official_source_approved_apply_request(self._valid_payload())

        payload = self._valid_payload()
        payload["mode"] = "invalid"
        _ = validate_official_source_approved_apply_request(payload)

        payload = self._valid_payload()
        payload["selected_keys"] = ["x"]
        _ = validate_official_source_approved_apply_request(payload)

        payload = self._valid_payload()
        payload["force_write"] = True
        _ = validate_official_source_approved_apply_request(payload)

        after_hashes = self._actual_results_file_hashes()
        self.assertEqual(before_hashes, after_hashes)


if __name__ == "__main__":
    unittest.main()
