import hashlib
import unittest
from pathlib import Path

from operator_dashboard.official_source_approved_apply_token import (
    build_official_source_approved_apply_binding_digest,
    issue_official_source_approved_apply_token,
    parse_official_source_approved_apply_token,
    validate_official_source_approved_apply_token,
)


class OfficialSourceApprovedApplyTokenTest(unittest.TestCase):
    def _valid_binding(self):
        return {
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

    def test_token_helper_module_imports_without_flask_or_app(self):
        self.assertTrue(callable(build_official_source_approved_apply_binding_digest))
        self.assertTrue(callable(issue_official_source_approved_apply_token))
        self.assertTrue(callable(parse_official_source_approved_apply_token))
        self.assertTrue(callable(validate_official_source_approved_apply_token))

    def test_valid_binding_builds_deterministic_digest(self):
        one = build_official_source_approved_apply_binding_digest(self._valid_binding())
        two = build_official_source_approved_apply_binding_digest(self._valid_binding())
        self.assertTrue(one.get("ok"))
        self.assertTrue(two.get("ok"))
        self.assertEqual(one.get("binding_digest"), two.get("binding_digest"))
        self.assertEqual(len(one.get("binding_digest") or ""), 64)

    def test_nullable_binding_fields_normalize_to_empty_string(self):
        binding = self._valid_binding()
        binding["record_fight_id"] = None
        binding["selected_row_identity"]["fight_id"] = None
        result = build_official_source_approved_apply_binding_digest(binding)
        self.assertTrue(result.get("ok"))
        fields = result.get("binding_fields") or {}
        self.assertEqual(fields.get("record_fight_id"), "")
        self.assertEqual((fields.get("selected_row_identity") or {}).get("fight_id"), "")

    def test_same_normalized_binding_produces_same_digest(self):
        base = self._valid_binding()
        spaced = self._valid_binding()
        spaced["selected_key"] = f"  {spaced['selected_key']}  "
        spaced["selected_row_identity"]["fight_name"] = f" {spaced['selected_row_identity']['fight_name']} "
        one = build_official_source_approved_apply_binding_digest(base)
        two = build_official_source_approved_apply_binding_digest(spaced)
        self.assertEqual(one.get("binding_digest"), two.get("binding_digest"))

    def test_changed_selected_key_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["selected_key"] = "different|row"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_changed_citation_fingerprint_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["citation_fingerprint"] = "other_fingerprint"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_changed_source_url_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["source_url"] = "https://onefc.com/events/test-card"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_changed_source_date_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["source_date"] = "2026-04-21"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_changed_extracted_winner_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["extracted_winner"] = "Beta"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_changed_selected_row_identity_fight_name_changes_digest(self):
        a = build_official_source_approved_apply_binding_digest(self._valid_binding())
        b = self._valid_binding()
        b["selected_row_identity"]["fight_name"] = "Gamma vs Delta"
        c = build_official_source_approved_apply_binding_digest(b)
        self.assertNotEqual(a.get("binding_digest"), c.get("binding_digest"))

    def test_issue_token_creates_osat1_token_and_envelope(self):
        result = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        self.assertTrue(result.get("ok"))
        token = result.get("token") or ""
        self.assertTrue(token.startswith("osat1."))
        self.assertFalse(result.get("consumed"))
        self.assertEqual(result.get("issued_at_epoch"), 1700000000)
        self.assertEqual(result.get("expires_at_epoch"), 1700000120)
        self.assertEqual(len(result.get("token_id") or ""), 32)

    def test_ttl_seconds_capped_at_300(self):
        result = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=999)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("expires_at_epoch"), 1700000300)

    def test_invalid_ttl_is_rejected(self):
        for ttl in (0, -1, "300"):
            with self.subTest(ttl=ttl):
                result = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=ttl)  # type: ignore[arg-type]
                self.assertFalse(result.get("ok"))

    def test_parse_valid_token_succeeds(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        parsed = parse_official_source_approved_apply_token(issued.get("token"))
        self.assertTrue(parsed.get("ok"))
        self.assertEqual(parsed.get("token_status"), "valid")

    def test_missing_token_rejected(self):
        parsed = parse_official_source_approved_apply_token("")
        self.assertFalse(parsed.get("ok"))
        self.assertEqual(parsed.get("token_status"), "missing")

    def test_malformed_token_rejected(self):
        parsed = parse_official_source_approved_apply_token("bad.token")
        self.assertFalse(parsed.get("ok"))
        self.assertEqual(parsed.get("token_status"), "malformed")

    def test_approval_granted_false_rejected(self):
        token = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120).get("token")
        result = validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000001, approval_granted=False)
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("reason_code"), "approval_required")
        self._assert_invariant_flags(result)

    def test_expired_token_rejected(self):
        token = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=1).get("token")
        result = validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000005)
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("token_status"), "expired")
        self.assertEqual(result.get("reason_code"), "approval_expired")

    def test_future_issued_token_rejected(self):
        token = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000100, ttl_seconds=100).get("token")
        result = validate_official_source_approved_apply_token(
            token,
            self._valid_binding(),
            now_epoch=1700000000,
            allowed_clock_skew_seconds=5,
        )
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("token_status"), "future_issued")
        self.assertEqual(result.get("reason_code"), "approval_future_issued")

    def test_replayed_token_rejected_using_simulated_set(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        token = issued.get("token")
        token_id = issued.get("token_id")
        result = validate_official_source_approved_apply_token(
            token,
            self._valid_binding(),
            now_epoch=1700000001,
            replayed_token_ids={token_id},
        )
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("token_status"), "replayed")
        self.assertEqual(result.get("reason_code"), "approval_replayed")

    def test_consumed_token_rejected_using_simulated_set(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        token = issued.get("token")
        token_id = issued.get("token_id")
        result = validate_official_source_approved_apply_token(
            token,
            self._valid_binding(),
            now_epoch=1700000001,
            consumed_token_ids={token_id},
        )
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("token_status"), "consumed")
        self.assertEqual(result.get("reason_code"), "approval_token_consumed")

    def test_binding_mismatch_rejected(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        changed = self._valid_binding()
        changed["source_date"] = "2026-04-21"
        result = validate_official_source_approved_apply_token(
            issued.get("token"),
            changed,
            now_epoch=1700000001,
        )
        self.assertFalse(result.get("token_valid"))
        self.assertEqual(result.get("token_status"), "binding_mismatch")
        self.assertEqual(result.get("reason_code"), "approval_binding_mismatch")

    def test_valid_token_validates_successfully(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        result = validate_official_source_approved_apply_token(
            issued.get("token"),
            self._valid_binding(),
            now_epoch=1700000001,
        )
        self.assertTrue(result.get("token_valid"))
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("token_status"), "valid")
        self.assertEqual(result.get("reason_code"), "valid_token")
        self._assert_invariant_flags(result)

    def test_every_invalid_validation_result_has_invariant_false_flags(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=60)
        token = issued.get("token")
        token_id = issued.get("token_id")

        invalid_results = [
            validate_official_source_approved_apply_token("", self._valid_binding(), now_epoch=1700000001),
            validate_official_source_approved_apply_token("bad.token", self._valid_binding(), now_epoch=1700000001),
            validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000001, approval_granted=False),
            validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000700),
            validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000001, replayed_token_ids={token_id}),
            validate_official_source_approved_apply_token(token, self._valid_binding(), now_epoch=1700000001, consumed_token_ids={token_id}),
        ]

        changed_binding = self._valid_binding()
        changed_binding["selected_key"] = "different|row"
        invalid_results.append(
            validate_official_source_approved_apply_token(token, changed_binding, now_epoch=1700000001)
        )

        for idx, result in enumerate(invalid_results):
            with self.subTest(idx=idx):
                self.assertFalse(result.get("token_valid"))
                self._assert_invariant_flags(result)

    def test_helper_calls_do_not_modify_actual_results_files(self):
        before = self._actual_results_file_hashes()

        binding = self._valid_binding()
        _ = build_official_source_approved_apply_binding_digest(binding)
        issued = issue_official_source_approved_apply_token(binding, now_epoch=1700000000, ttl_seconds=120)
        _ = parse_official_source_approved_apply_token(issued.get("token"))
        _ = validate_official_source_approved_apply_token(issued.get("token"), binding, now_epoch=1700000001)
        _ = validate_official_source_approved_apply_token("bad.token", binding, now_epoch=1700000001)

        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)


    def test_validate_valid_token_surfaces_token_id_matching_issued(self):
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        result = validate_official_source_approved_apply_token(
            issued.get("token"),
            self._valid_binding(),
            now_epoch=1700000001,
        )
        self.assertTrue(result.get("token_valid"))
        self.assertIn("token_id", result)
        self.assertEqual(result.get("token_id"), issued.get("token_id"))
        self.assertEqual(len(result.get("token_id") or ""), 32)

    def test_validate_pre_parse_deny_has_no_token_id(self):
        # Missing token (pre-parse) and malformed token (pre-parse) must return token_id=None
        missing_result = validate_official_source_approved_apply_token(
            "", self._valid_binding(), now_epoch=1700000001
        )
        malformed_result = validate_official_source_approved_apply_token(
            "bad.token", self._valid_binding(), now_epoch=1700000001
        )
        self.assertFalse(missing_result.get("token_valid"))
        self.assertIsNone(missing_result.get("token_id"))
        self.assertFalse(malformed_result.get("token_valid"))
        self.assertIsNone(malformed_result.get("token_id"))

    def test_validate_post_parse_deny_surfaces_token_id(self):
        # expired, replayed, consumed, binding_mismatch all have a parseable token_id
        issued = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=1)
        token = issued.get("token")
        token_id = issued.get("token_id")

        expired = validate_official_source_approved_apply_token(
            token, self._valid_binding(), now_epoch=1700000010
        )
        replayed = validate_official_source_approved_apply_token(
            token, self._valid_binding(), now_epoch=1700000000,
            replayed_token_ids={token_id},
        )
        issued2 = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        consumed = validate_official_source_approved_apply_token(
            issued2.get("token"), self._valid_binding(), now_epoch=1700000001,
            consumed_token_ids={issued2.get("token_id")},
        )
        issued3 = issue_official_source_approved_apply_token(self._valid_binding(), now_epoch=1700000000, ttl_seconds=120)
        changed = self._valid_binding()
        changed["source_date"] = "2026-04-21"
        binding_mismatch = validate_official_source_approved_apply_token(
            issued3.get("token"), changed, now_epoch=1700000001
        )

        for label, result, expected_id in [
            ("expired", expired, token_id),
            ("replayed", replayed, token_id),
            ("consumed", consumed, issued2.get("token_id")),
            ("binding_mismatch", binding_mismatch, issued3.get("token_id")),
        ]:
            with self.subTest(label=label):
                self.assertFalse(result.get("token_valid"))
                self.assertIn("token_id", result)
                self.assertEqual(result.get("token_id"), expected_id)


if __name__ == "__main__":
    unittest.main()
