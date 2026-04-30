import hashlib
import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from operator_dashboard import official_source_approved_apply_mutation_adapter
from operator_dashboard.official_source_approved_apply_mutation_adapter import (
    apply_official_source_approved_apply_mutation,
)


class OfficialSourceApprovedApplyMutationAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.accuracy_dir = Path(self.temp_dir.name)
        self.target_path = self.accuracy_dir / "actual_results_manual.json"
        self._write_rows([])

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_rows(self, rows):
        self.target_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _read_rows(self):
        return json.loads(self.target_path.read_text(encoding="utf-8"))

    def _file_hash(self):
        return hashlib.sha256(self.target_path.read_bytes()).hexdigest()

    def _guard_result(self):
        return {
            "guard_allowed": True,
            "reason_code": "accepted_preview_write_eligible",
            "token_valid": True,
            "approval_binding_valid": True,
            "manual_review_required": False,
            "token_id": "a" * 32,
            "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
            "binding_digest_expected": "b" * 64,
            "acceptance_gate": {
                "state": "write_eligible",
                "write_eligible": True,
                "reason_code": "accepted_preview_write_eligible",
                "selected_key": "alpha_vs_beta|predictions_alpha_vs_beta_prediction_json",
                "citation_fingerprint": "abc123fingerprint",
            },
        }

    def _preview_snapshot(self):
        return {
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
                "extracted_method": "Decision",
                "extracted_round": "3",
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
                "fight_name": "Alpha vs Beta",
                "event_name": "UFC Test Card",
            },
        }

    def _apply(self, *, guard_result=None, preview_snapshot=None, consumed_token_ids=None, lock_timeout_seconds=1):
        return apply_official_source_approved_apply_mutation(
            guard_result=guard_result or self._guard_result(),
            preview_snapshot=preview_snapshot or self._preview_snapshot(),
            accuracy_dir=self.accuracy_dir,
            consumed_token_ids=consumed_token_ids if consumed_token_ids is not None else set(),
            lock_timeout_seconds=lock_timeout_seconds,
            operation_id="op-123",
            write_attempt_id="attempt-456",
            contract_version="official_source_approved_apply_contract_v1",
            endpoint_version="approved_apply_v1",
        )

    def test_module_imports_without_flask_or_app(self):
        source = inspect.getsource(official_source_approved_apply_mutation_adapter)
        self.assertNotIn("flask", source.lower())
        self.assertNotIn("operator_dashboard.app", source)
        self.assertNotIn("_upsert_single_manual_actual_result", source)

    def test_precondition_guard_not_allowed_denies_before_atomic_write(self):
        guard_result = self._guard_result()
        guard_result["guard_allowed"] = False
        before_hash = self._file_hash()
        with patch("operator_dashboard.official_source_approved_apply_mutation_adapter._atomic_write_single_record") as mock_write:
            result = self._apply(guard_result=guard_result)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "precondition_guard_not_allowed")
        self.assertFalse(result.get("write_performed"))
        self.assertEqual(before_hash, self._file_hash())
        mock_write.assert_not_called()

    def test_precondition_token_id_missing_denies_before_atomic_write(self):
        guard_result = self._guard_result()
        guard_result["token_id"] = ""
        with patch("operator_dashboard.official_source_approved_apply_mutation_adapter._atomic_write_single_record") as mock_write:
            result = self._apply(guard_result=guard_result)
        self.assertEqual(result.get("reason_code"), "precondition_token_id_missing")
        self.assertFalse(result.get("write_performed"))
        mock_write.assert_not_called()

    def test_critical_field_missing_denies_on_blank_fight_id(self):
        preview_snapshot = self._preview_snapshot()
        preview_snapshot["audit"]["record_fight_id"] = ""
        result = self._apply(preview_snapshot=preview_snapshot)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "critical_field_missing")
        self.assertIn("missing required field: fight_id", result.get("errors"))
        self.assertFalse(result.get("write_performed"))

    def test_noncritical_fields_fallback_to_unknown(self):
        preview_snapshot = self._preview_snapshot()
        preview_snapshot["source_citation"]["extracted_method"] = ""
        preview_snapshot["source_citation"]["extracted_round"] = None
        preview_snapshot["source_citation"]["source_title"] = "UFC Test Card"
        preview_snapshot["audit"]["event_name"] = ""
        result = self._apply(preview_snapshot=preview_snapshot)
        self.assertTrue(result.get("ok"))
        write_row = result.get("proposed_write") or {}
        self.assertEqual(write_row.get("actual_method"), "UNKNOWN")
        self.assertEqual(write_row.get("actual_round"), "UNKNOWN")
        self.assertEqual(write_row.get("event_name"), "UFC Test Card")

    def test_success_insert_writes_record_and_audit_fields(self):
        result = self._apply()
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("write_performed"))
        self.assertEqual(result.get("reason_code"), "official_source_write_applied")
        self.assertEqual(result.get("before_row_count"), 0)
        self.assertEqual(result.get("after_row_count"), 1)
        self.assertIsNotNone(result.get("pre_write_file_sha256"))
        self.assertIsNotNone(result.get("post_write_file_sha256"))
        rows = self._read_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("fight_id"), "alpha_vs_beta")
        self.assertEqual(rows[0].get("approval_token_id"), "a" * 32)
        self.assertEqual(rows[0].get("operation_id"), "op-123")
        self.assertEqual(rows[0].get("write_attempt_id"), "attempt-456")

    def test_success_update_existing_row_keeps_row_count(self):
        self._write_rows([
            {
                "fight_id": "alpha_vs_beta",
                "actual_winner": "Beta",
                "source": "old_source",
            }
        ])
        result = self._apply()
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("before_row_count"), 1)
        self.assertEqual(result.get("after_row_count"), 1)
        rows = self._read_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("actual_winner"), "Alpha")
        self.assertEqual(rows[0].get("source"), "official_source_manual_approved")

    def test_contention_timeout_denies_without_write(self):
        before_hash = self._file_hash()
        with patch(
            "operator_dashboard.official_source_approved_apply_mutation_adapter._acquire_mutation_lock",
            return_value={
                "ok": False,
                "lock": None,
                "reason_code": "contention_timeout",
                "errors": ["mutation lock timed out"],
            },
        ):
            result = self._apply()
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "contention_timeout")
        self.assertFalse(result.get("write_performed"))
        self.assertEqual(before_hash, self._file_hash())

    def test_atomic_replace_error_rolls_back_exact_previous_bytes(self):
        self._write_rows([{"fight_id": "existing", "actual_winner": "Gamma"}])
        before_bytes = self.target_path.read_bytes()
        real_replace = os.replace
        call_count = {"count": 0}

        def flaky_replace(src, dst):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise OSError("replace failed")
            return real_replace(src, dst)

        with patch("operator_dashboard.official_source_approved_apply_mutation_adapter.os.replace", side_effect=flaky_replace):
            result = self._apply()

        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "atomic_replace_error")
        self.assertTrue(result.get("rollback_attempted"))
        self.assertTrue(result.get("rollback_succeeded"))
        self.assertEqual(before_bytes, self.target_path.read_bytes())
        self.assertEqual(result.get("post_rollback_file_sha256"), hashlib.sha256(before_bytes).hexdigest())

    def test_post_write_hash_mismatch_rolls_back_exact_previous_bytes(self):
        self._write_rows([{"fight_id": "existing", "actual_winner": "Gamma"}])
        before_bytes = self.target_path.read_bytes()
        real_read = official_source_approved_apply_mutation_adapter._read_file_bytes
        call_count = {"count": 0}

        def fake_read(path):
            call_count["count"] += 1
            if call_count["count"] == 2:
                return b"corrupted-after-write"
            return real_read(path)

        with patch("operator_dashboard.official_source_approved_apply_mutation_adapter._read_file_bytes", side_effect=fake_read):
            result = self._apply()

        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "post_write_hash_mismatch")
        self.assertTrue(result.get("rollback_attempted"))
        self.assertTrue(result.get("rollback_succeeded"))
        self.assertEqual(before_bytes, self.target_path.read_bytes())
        self.assertEqual(result.get("post_rollback_file_sha256"), hashlib.sha256(before_bytes).hexdigest())

    def test_rollback_failed_terminal_escalates(self):
        before_bytes = self.target_path.read_bytes()

        with patch(
            "operator_dashboard.official_source_approved_apply_mutation_adapter.os.replace",
            side_effect=OSError("replace failed everywhere"),
        ):
            result = self._apply()

        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "rollback_failed_terminal")
        self.assertTrue(result.get("rollback_attempted"))
        self.assertFalse(result.get("rollback_succeeded"))
        self.assertEqual(result.get("rollback_terminal_state"), "rollback_failed_terminal")
        self.assertTrue(result.get("escalation_required"))
        self.assertEqual(result.get("operator_escalation_action"), "manual_file_recovery_required")
        self.assertEqual(before_bytes, self.target_path.read_bytes())

    def test_consumed_token_ids_are_not_mutated(self):
        consumed_token_ids = {"already-consumed-token"}
        before = set(consumed_token_ids)
        result = self._apply(consumed_token_ids=consumed_token_ids)
        self.assertTrue(result.get("ok"))
        self.assertEqual(before, consumed_token_ids)
        self.assertFalse(result.get("token_consume_performed"))

    def test_cross_filesystem_write_error_is_fail_closed(self):
        before_hash = self._file_hash()
        real_stat = os.stat

        def fake_stat(path, *args, **kwargs):
            stat_result = real_stat(path, *args, **kwargs)
            path_text = str(path)
            if path_text.endswith(".tmp"):
                return os.stat_result((stat_result.st_mode, stat_result.st_ino, stat_result.st_dev + 1, stat_result.st_nlink, stat_result.st_uid, stat_result.st_gid, stat_result.st_size, stat_result.st_atime, stat_result.st_mtime, stat_result.st_ctime))
            return stat_result

        with patch("operator_dashboard.official_source_approved_apply_mutation_adapter.os.stat", side_effect=fake_stat):
            result = self._apply()

        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason_code"), "cross_filesystem_write_error")
        self.assertFalse(result.get("write_performed"))
        self.assertEqual(before_hash, self._file_hash())

    def test_adapter_tests_do_not_modify_repo_actual_results_files(self):
        root = Path(__file__).resolve().parent.parent
        targets = [
            root / "ops" / "accuracy" / "actual_results.json",
            root / "ops" / "accuracy" / "actual_results_manual.json",
            root / "ops" / "accuracy" / "actual_results_unresolved.json",
        ]
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in targets if path.exists()}
        _ = self._apply()
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in targets if path.exists()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()