import hashlib
import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

from operator_dashboard import official_source_approved_apply_guard
from operator_dashboard.official_source_approved_apply_guard import (
    evaluate_official_source_approved_apply_guard,
)
from operator_dashboard.official_source_approved_apply_token import (
    issue_official_source_approved_apply_token,
)


class OfficialSourceApprovedApplyGuardTest(unittest.TestCase):
    def _valid_request_payload(self):
        return {
            "mode": "official_source_approved_apply",
            "lookup_intent": "apply_write",
            "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
            "approval_granted": True,
            "approval_token": "placeholder",
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
                "reason_code": "accepted_preview_write_eligible",
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

    def _authoritative_preview_result(self):
        payload = self._valid_request_payload()
        return {
            "ok": True,
            "mode": "official_source_one_record",
            "phase": "lookup_preview",
            "selected_key": payload["selected_key"],
            "approval_required": True,
            "approval_granted": False,
            "mutation_performed": False,
            "external_lookup_performed": True,
            "bulk_lookup_performed": False,
            "scoring_semantics_changed": False,
            "manual_review_required": payload["preview_snapshot"]["manual_review_required"],
            "reason_code": payload["preview_snapshot"]["reason_code"],
            "source_citation": dict(payload["preview_snapshot"]["source_citation"]),
            "acceptance_gate": dict(payload["preview_snapshot"]["acceptance_gate"]),
            "audit": dict(payload["preview_snapshot"]["audit"]),
        }

    def _with_token(self, payload, now_epoch=1700000000, ttl_seconds=120):
        issued = issue_official_source_approved_apply_token(
            payload["approval_binding"],
            now_epoch=now_epoch,
            ttl_seconds=ttl_seconds,
        )
        self.assertTrue(issued.get("ok"))
        payload["approval_token"] = issued.get("token")
        return payload, issued

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

    def _assert_non_mutation_flags(self, result):
        self.assertFalse(result.get("mutation_performed"))
        self.assertFalse(result.get("write_performed"))
        self.assertFalse(result.get("bulk_lookup_performed"))
        self.assertFalse(result.get("scoring_semantics_changed"))

    def test_module_imports_without_flask_or_app(self):
        source = inspect.getsource(official_source_approved_apply_guard)
        self.assertNotIn("flask", source.lower())
        self.assertNotIn("operator_dashboard.app", source)

    def test_schema_invalid_denies_before_token_gate(self):
        payload = self._valid_request_payload()
        payload.pop("mode")
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "invalid_apply_mode")
        self.assertEqual(result.get("token_status"), "not_evaluated")
        self._assert_non_mutation_flags(result)

    def test_token_invalid_denies(self):
        payload = self._valid_request_payload()
        payload["approval_token"] = "bad.token"
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "malformed_field_type")
        self._assert_non_mutation_flags(result)

    def test_selected_key_binding_mismatch_denies(self):
        payload, _issued = self._with_token(self._valid_request_payload())
        payload["selected_key"] = "different|row"
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "selected_key_binding_mismatch")

    def test_citation_fingerprint_binding_mismatch_denies(self):
        payload = self._valid_request_payload()
        payload["approval_binding"]["citation_fingerprint"] = "different"
        payload, _issued = self._with_token(payload)
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "citation_binding_mismatch")

    def test_source_url_binding_mismatch_denies(self):
        payload = self._valid_request_payload()
        payload["approval_binding"]["source_url"] = "https://onefc.com/events/other"
        payload, _issued = self._with_token(payload)
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "source_url_binding_mismatch")

    def test_source_date_binding_mismatch_denies(self):
        payload = self._valid_request_payload()
        payload["approval_binding"]["source_date"] = "2026-04-21"
        payload, _issued = self._with_token(payload)
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "source_date_binding_mismatch")

    def test_extracted_winner_binding_mismatch_denies(self):
        payload = self._valid_request_payload()
        payload["approval_binding"]["extracted_winner"] = "Beta"
        payload, _issued = self._with_token(payload)
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "extracted_winner_binding_mismatch")

    def test_record_identity_binding_mismatch_denies(self):
        payload = self._valid_request_payload()
        payload["approval_binding"]["record_fight_id"] = "different_fight"
        payload, _issued = self._with_token(payload)
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "record_identity_binding_mismatch")

    def test_preview_snapshot_mismatch_denies(self):
        payload, _issued = self._with_token(self._valid_request_payload())
        authoritative = self._authoritative_preview_result()
        authoritative["source_citation"]["source_date"] = "2026-05-01"
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=authoritative,
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "preview_snapshot_mismatch")

    def test_acceptance_gate_manual_review_denies(self):
        payload = self._valid_request_payload()
        payload["preview_snapshot"]["reason_code"] = "source_conflict"
        payload["preview_snapshot"]["manual_review_required"] = True
        payload["preview_snapshot"]["acceptance_gate"]["state"] = "manual_review"
        payload["preview_snapshot"]["acceptance_gate"]["write_eligible"] = False
        payload["preview_snapshot"]["acceptance_gate"]["reason_code"] = "source_conflict"

        payload, _issued = self._with_token(payload)
        authoritative = self._authoritative_preview_result()
        authoritative["reason_code"] = "source_conflict"
        authoritative["manual_review_required"] = True
        authoritative["acceptance_gate"]["state"] = "manual_review"
        authoritative["acceptance_gate"]["write_eligible"] = False
        authoritative["acceptance_gate"]["reason_code"] = "source_conflict"

        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=authoritative,
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "source_conflict")

    def test_acceptance_gate_rejected_denies(self):
        payload = self._valid_request_payload()
        payload["preview_snapshot"]["reason_code"] = "identity_conflict"
        payload["preview_snapshot"]["manual_review_required"] = True
        payload["preview_snapshot"]["acceptance_gate"]["state"] = "rejected"
        payload["preview_snapshot"]["acceptance_gate"]["write_eligible"] = False
        payload["preview_snapshot"]["acceptance_gate"]["reason_code"] = "identity_conflict"

        payload, _issued = self._with_token(payload)
        authoritative = self._authoritative_preview_result()
        authoritative["reason_code"] = "identity_conflict"
        authoritative["manual_review_required"] = True
        authoritative["acceptance_gate"]["state"] = "rejected"
        authoritative["acceptance_gate"]["write_eligible"] = False
        authoritative["acceptance_gate"]["reason_code"] = "identity_conflict"

        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=authoritative,
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "identity_conflict")

    def test_acceptance_gate_not_write_eligible_denies(self):
        payload, _issued = self._with_token(self._valid_request_payload())
        with patch("operator_dashboard.official_source_approved_apply_guard.evaluate_official_source_acceptance_gate") as mock_gate:
            mock_gate.return_value = {
                "state": "write_eligible",
                "write_eligible": False,
                "reason_code": "accepted_preview_write_eligible",
                "reasons": ["accepted_preview_write_eligible"],
                "checks": {},
                "selected_key": payload["selected_key"],
                "citation_fingerprint": payload["approval_binding"]["citation_fingerprint"],
            }
            result = evaluate_official_source_approved_apply_guard(
                payload,
                authoritative_preview_result=self._authoritative_preview_result(),
                now_epoch=1700000001,
            )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "acceptance_gate_not_write_eligible")

    def test_valid_request_token_binding_and_gate_allows_guard(self):
        payload, _issued = self._with_token(self._valid_request_payload())
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertTrue(result.get("guard_allowed"))
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "accepted_preview_write_eligible")
        self.assertTrue(result.get("request_valid"))
        self.assertTrue(result.get("token_valid"))
        self.assertTrue(result.get("approval_binding_valid"))
        self.assertFalse(result.get("manual_review_required"))
        self._assert_non_mutation_flags(result)

    def test_every_deny_path_has_non_mutation_flags(self):
        deny_results = []

        payload = self._valid_request_payload()
        payload.pop("mode")
        deny_results.append(
            evaluate_official_source_approved_apply_guard(
                payload,
                authoritative_preview_result=self._authoritative_preview_result(),
                now_epoch=1700000001,
            )
        )

        payload = self._valid_request_payload()
        payload["approval_token"] = "bad.token"
        deny_results.append(
            evaluate_official_source_approved_apply_guard(
                payload,
                authoritative_preview_result=self._authoritative_preview_result(),
                now_epoch=1700000001,
            )
        )

        payload = self._valid_request_payload()
        payload["selected_key"] = "different|row"
        payload, _issued = self._with_token(payload)
        deny_results.append(
            evaluate_official_source_approved_apply_guard(
                payload,
                authoritative_preview_result=self._authoritative_preview_result(),
                now_epoch=1700000001,
            )
        )

        for idx, result in enumerate(deny_results):
            with self.subTest(idx=idx):
                self.assertFalse(result.get("guard_allowed"))
                self._assert_non_mutation_flags(result)

    def test_guard_tests_do_not_modify_actual_results_files(self):
        before = self._actual_results_file_hashes()

        payload, _issued = self._with_token(self._valid_request_payload())
        _ = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )

        payload = self._valid_request_payload()
        payload.pop("mode")
        _ = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )

        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    def test_guard_module_does_not_import_operator_dashboard_app(self):
        source = inspect.getsource(official_source_approved_apply_guard)
        self.assertNotIn("operator_dashboard.app", source)

    def test_guard_module_does_not_call_upsert_single_manual_actual_result(self):
        source = inspect.getsource(official_source_approved_apply_guard)
        self.assertNotIn("_upsert_single_manual_actual_result", source)


    def test_guard_allowed_surfaces_token_id(self):
        payload, issued = self._with_token(self._valid_request_payload())
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertTrue(result.get("guard_allowed"))
        self.assertIn("token_id", result)
        self.assertEqual(result.get("token_id"), issued.get("token_id"))
        self.assertEqual(len(result.get("token_id") or ""), 32)
        self.assertIn("operation_id", result)
        self.assertIsNone(result.get("operation_id"))

    def test_guard_allowed_surfaces_normalized_operation_id(self):
        payload, _issued = self._with_token(self._valid_request_payload())
        payload["operation_id"] = "  op_retry_20260430_abcdef  "
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertTrue(result.get("guard_allowed"))
        self.assertEqual(result.get("operation_id"), "op_retry_20260430_abcdef")

    def test_guard_schema_deny_has_no_token_id(self):
        payload = self._valid_request_payload()
        payload.pop("mode")
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertIn("token_id", result)
        self.assertIsNone(result.get("token_id"))
        self.assertIn("operation_id", result)
        self.assertIsNone(result.get("operation_id"))

    def test_guard_token_deny_has_no_token_id(self):
        payload = self._valid_request_payload()
        payload["approval_token"] = "bad.token"
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertIn("token_id", result)
        self.assertIsNone(result.get("token_id"))
        self.assertIn("operation_id", result)
        self.assertIsNone(result.get("operation_id"))

    def test_operation_id_absent_does_not_change_guard_allow_result(self):
        payload_without, _issued = self._with_token(self._valid_request_payload())
        payload_with = self._valid_request_payload()
        payload_with["operation_id"] = "op_retry_20260430_abcdef"
        payload_with, _issued2 = self._with_token(payload_with)

        result_without = evaluate_official_source_approved_apply_guard(
            payload_without,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        result_with = evaluate_official_source_approved_apply_guard(
            payload_with,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )

        self.assertTrue(result_without.get("guard_allowed"))
        self.assertTrue(result_with.get("guard_allowed"))
        self.assertEqual(result_without.get("reason_code"), result_with.get("reason_code"))
        self.assertIsNone(result_without.get("operation_id"))
        self.assertEqual(result_with.get("operation_id"), "op_retry_20260430_abcdef")
        self._assert_non_mutation_flags(result_without)
        self._assert_non_mutation_flags(result_with)

    def test_operation_id_absent_does_not_change_guard_deny_result(self):
        payload_without = self._valid_request_payload()
        payload_without.pop("mode")

        payload_with = self._valid_request_payload()
        payload_with.pop("mode")
        payload_with["operation_id"] = "op_retry_20260430_abcdef"

        result_without = evaluate_official_source_approved_apply_guard(
            payload_without,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        result_with = evaluate_official_source_approved_apply_guard(
            payload_with,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )

        self.assertFalse(result_without.get("guard_allowed"))
        self.assertFalse(result_with.get("guard_allowed"))
        self.assertEqual(result_without.get("reason_code"), result_with.get("reason_code"))
        self.assertIsNone(result_without.get("operation_id"))
        self.assertEqual(result_with.get("operation_id"), "op_retry_20260430_abcdef")
        self._assert_non_mutation_flags(result_without)
        self._assert_non_mutation_flags(result_with)

    def test_guard_post_token_deny_surfaces_token_id(self):
        # After token validates, binding mismatch path must surface token_id
        payload, issued = self._with_token(self._valid_request_payload())
        payload["selected_key"] = "different|row"
        result = evaluate_official_source_approved_apply_guard(
            payload,
            authoritative_preview_result=self._authoritative_preview_result(),
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("guard_allowed"))
        self.assertEqual(result.get("reason_code"), "selected_key_binding_mismatch")
        self.assertIn("token_id", result)
        self.assertEqual(result.get("token_id"), issued.get("token_id"))
        self.assertEqual(len(result.get("token_id") or ""), 32)
        self.assertIn("operation_id", result)
        self.assertIsNone(result.get("operation_id"))


if __name__ == "__main__":
    unittest.main()
