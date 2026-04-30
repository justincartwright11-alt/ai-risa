import hashlib
import inspect
import unittest
from pathlib import Path

from operator_dashboard import official_source_approved_apply_token_consume_helper
from operator_dashboard.official_source_approved_apply_token_consume_helper import (
    OfficialSourceApprovedApplyTokenConsumeHelper,
    REASON_CONFLICT,
    REASON_MALFORMED,
    REASON_STORE_UNAVAILABLE,
    STATE_CONSUMED,
    STATE_CONSUME_REGISTER_FAILED,
    STATE_NOT_CONSUMED,
)


class OfficialSourceApprovedApplyTokenConsumeHelperTest(unittest.TestCase):
    def setUp(self):
        self.helper = OfficialSourceApprovedApplyTokenConsumeHelper()

    def _register_payload(self):
        return {
            "token_id": "a" * 32,
            "operation_id": "op-123",
            "write_attempt_id": "attempt-456",
            "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
            "reason_code_at_consume": "official_source_write_applied",
            "binding_digest_expected": "b" * 64,
            "contract_version": "official_source_approved_apply_contract_v1",
            "endpoint_version": "official_source_approved_apply_endpoint_mutation_v1",
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

    def test_module_imports_without_flask_or_app(self):
        source = inspect.getsource(official_source_approved_apply_token_consume_helper)
        self.assertNotIn("flask", source.lower())
        self.assertNotIn("operator_dashboard.app", source)

    def test_lookup_missing_token_returns_not_consumed(self):
        result = self.helper.lookup("a" * 32)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("state"), STATE_NOT_CONSUMED)
        self.assertIsNone(result.get("record"))

    def test_lookup_requires_token_id(self):
        result = self.helper.lookup("")
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), REASON_MALFORMED)

    def test_register_consume_success(self):
        payload = self._register_payload()
        result = self.helper.register_consume(**payload)
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("token_consume_performed"))
        self.assertEqual(result.get("state"), STATE_CONSUMED)
        self.assertFalse(result.get("idempotent"))
        record = result.get("record") or {}
        self.assertEqual(record.get("token_id"), payload["token_id"])
        self.assertEqual(record.get("operation_id"), payload["operation_id"])

    def test_lookup_after_successful_consume_returns_record(self):
        payload = self._register_payload()
        self.helper.register_consume(**payload)
        result = self.helper.lookup(payload["token_id"])
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("state"), STATE_CONSUMED)
        self.assertEqual((result.get("record") or {}).get("operation_id"), payload["operation_id"])

    def test_lookup_by_operation_after_success(self):
        payload = self._register_payload()
        self.helper.register_consume(**payload)
        result = self.helper.lookup_by_operation(payload["operation_id"])
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("state"), STATE_CONSUMED)
        self.assertEqual(result.get("token_id"), payload["token_id"])

    def test_lookup_by_operation_missing_returns_not_consumed(self):
        result = self.helper.lookup_by_operation("op-missing")
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("state"), STATE_NOT_CONSUMED)

    def test_lookup_by_operation_requires_operation_id(self):
        result = self.helper.lookup_by_operation("")
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), REASON_MALFORMED)

    def test_register_consume_idempotent_same_operation(self):
        payload = self._register_payload()
        first = self.helper.register_consume(**payload)
        second = self.helper.register_consume(**payload)
        self.assertTrue(first.get("ok"))
        self.assertTrue(second.get("ok"))
        self.assertTrue(second.get("idempotent"))
        self.assertEqual((second.get("record") or {}).get("operation_id"), payload["operation_id"])

    def test_register_consume_conflict_on_different_operation_for_same_token(self):
        payload = self._register_payload()
        self.helper.register_consume(**payload)
        conflicted = dict(payload)
        conflicted["operation_id"] = "op-999"
        conflicted["write_attempt_id"] = "attempt-999"
        result = self.helper.register_consume(**conflicted)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), REASON_CONFLICT)
        self.assertFalse(result.get("token_consume_performed"))

    def test_register_consume_conflict_on_same_operation_different_token(self):
        payload = self._register_payload()
        self.helper.register_consume(**payload)
        conflicted = dict(payload)
        conflicted["token_id"] = "c" * 32
        conflicted["write_attempt_id"] = "attempt-999"
        result = self.helper.register_consume(**conflicted)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), REASON_CONFLICT)
        self.assertEqual(result.get("state"), STATE_CONSUME_REGISTER_FAILED)

    def test_register_consume_requires_required_fields(self):
        payload = self._register_payload()
        payload["binding_digest_expected"] = ""
        payload["contract_version"] = ""
        result = self.helper.register_consume(**payload)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), REASON_MALFORMED)
        errors = result.get("errors") or []
        self.assertTrue(any("binding_digest_expected" in item for item in errors))
        self.assertTrue(any("contract_version" in item for item in errors))

    def test_store_unavailable_affects_lookup_register_and_lookup_by_operation(self):
        payload = self._register_payload()
        self.helper.set_store_available(False)

        lookup = self.helper.lookup(payload["token_id"])
        register = self.helper.register_consume(**payload)
        lookup_op = self.helper.lookup_by_operation(payload["operation_id"])

        for result in (lookup, register, lookup_op):
            self.assertFalse(result.get("ok"))
            self.assertEqual(result.get("reason_code"), REASON_STORE_UNAVAILABLE)

    def test_store_unavailable_can_recover_and_register(self):
        payload = self._register_payload()
        self.helper.set_store_available(False)
        failed = self.helper.register_consume(**payload)
        self.assertFalse(failed.get("ok"))

        self.helper.set_store_available(True)
        success = self.helper.register_consume(**payload)
        self.assertTrue(success.get("ok"))
        self.assertTrue(success.get("token_consume_performed"))

    def test_helper_does_not_modify_actual_results_files(self):
        before = self._actual_results_file_hashes()

        payload = self._register_payload()
        _ = self.helper.lookup(payload["token_id"])
        _ = self.helper.lookup_by_operation(payload["operation_id"])
        _ = self.helper.register_consume(**payload)
        _ = self.helper.register_consume(**payload)

        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()