import unittest
import json
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch
from app import app, _build_structural_signal_backfill_planner

class DashboardBackendTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _sha256_or_none(self, path: Path):
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI-RISA Local Operator Dashboard', resp.data)

    def test_run_local_ai_invalid(self):
        resp = self.client.post('/run_local_ai', json={'request_type': 'invalid'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid request type', resp.data)

    def test_open_file_invalid(self):
        resp = self.client.get('/open_file?file=not_a_file')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid file type', resp.data)

    def test_accuracy_comparison_summary_contract(self):
        resp = self.client.get('/api/accuracy/comparison-summary')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('compared_results', data)
        self.assertIn('waiting_for_results', data)
        self.assertIn('summary_metrics', data)
        self.assertIsInstance(data.get('compared_results'), list)
        self.assertIsInstance(data.get('waiting_for_results'), list)
        self.assertIsInstance(data.get('summary_metrics'), dict)

    def test_operator_waiting_queue_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Waiting For Real Results', resp.data)
        self.assertIn(b'/api/accuracy/comparison-summary', resp.data)

    def test_index_command_center_uses_intent_endpoint(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/operator/intent', resp.data)
        self.assertNotIn(b'/api/operator/mode', resp.data)

    def test_index_compare_handler_targets_compare_endpoint(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-compare-btn', resp.data)
        self.assertIn(b"operatorCompareBtn.addEventListener('click'", resp.data)
        self.assertIn(b'/api/operator/compare-with-result', resp.data)

    def test_compare_endpoint_not_called_on_page_load(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        # Compare endpoint must stay behind explicit operator action.
        self.assertIn("operatorCompareBtn.addEventListener('click'", page)
        self.assertIn("/api/operator/compare-with-result", page)

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 500]
        self.assertNotIn('/api/operator/compare-with-result', dom_ready_slice)
        self.assertNotIn('/api/operator/web-trigger-scout', dom_ready_slice)

    def test_index_no_automatic_queue_wide_lookup_copy_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Bulk lookup for waiting records does not run automatically.', resp.data)

    def test_advanced_dashboard_has_interactive_summary_chips(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'summary-chip-health', resp.data)
        self.assertIn(b'summary-chip-accuracy', resp.data)
        self.assertIn(b'summary-chip-backfill', resp.data)
        self.assertIn(b'summary-chip-queue', resp.data)

    def test_advanced_summary_chip_click_wiring_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"chipHealth && chipHealth.addEventListener('click'", resp.data)
        self.assertIn(b"chipAccuracy && chipAccuracy.addEventListener('click'", resp.data)
        self.assertIn(b"chipBackfill && chipBackfill.addEventListener('click'", resp.data)
        self.assertIn(b"chipQueue && chipQueue.addEventListener('click'", resp.data)
        self.assertIn(b'_focusDashboardNode(', resp.data)

    def test_dry_run_preview_endpoint_contract(self):
        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('mode'), 'dry_run_preview')
        self.assertIn('waiting_count', data)
        self.assertIn('preview_limit', data)
        self.assertIn('preview_rows', data)
        self.assertIn('required_fields', data)
        self.assertIn('missing_by_row', data)
        self.assertIs(data.get('mutation_performed'), False)
        self.assertIs(data.get('external_lookup_performed'), False)
        self.assertIs(data.get('bulk_lookup_performed'), False)
        self.assertLessEqual(len(data.get('preview_rows') or []), 10)

    def test_dry_run_preview_limit_capped(self):
        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview?limit=999')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('preview_limit'), 10)
        self.assertLessEqual(len(data.get('preview_rows') or []), 10)

    def test_dry_run_preview_does_not_mutate_actual_results_files(self):
        root = Path(__file__).resolve().parent.parent
        accuracy_dir = root / 'ops' / 'accuracy'
        targets = [
            accuracy_dir / 'actual_results.json',
            accuracy_dir / 'actual_results_manual.json',
            accuracy_dir / 'actual_results_unresolved.json',
        ]
        before = {str(p): self._sha256_or_none(p) for p in targets}

        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIs(data.get('mutation_performed'), False)

        after = {str(p): self._sha256_or_none(p) for p in targets}
        self.assertEqual(before, after)

    def test_advanced_dashboard_has_dry_run_preview_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-dry-run-preview-btn', resp.data)
        self.assertIn(b'operator-dry-run-preview-output', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/dry-run-preview', resp.data)
        self.assertIn(b'No web lookup or result write is performed by this preview.', resp.data)

    def test_advanced_dry_run_preview_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 900]
        self.assertNotIn('/api/operator/actual-result-lookup/dry-run-preview', dom_ready_slice)

    def test_manual_review_empty_state_message_present(self):
        expected = b'External result lookup is not connected for automatic queue resolution yet. Manual review required.'
        index_resp = self.client.get('/')
        self.assertEqual(index_resp.status_code, 200)
        self.assertIn(expected, index_resp.data)

        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(expected, advanced_resp.data)

    def test_web_trigger_scout_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Find Fight Results', resp.data)
        self.assertIn(b'/api/operator/web-trigger-scout', resp.data)

    def test_web_trigger_scout_endpoint_contract(self):
        resp = self.client.post(
            '/api/operator/web-trigger-scout',
            json={
                'query': 'check Jafel Filho vs Cody Durden result',
                'mode': 'official_first',
                'targets': [],
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('results', data)
        self.assertIn('blocked_actions', data)
        self.assertIsInstance(data.get('results'), list)
        self.assertIsInstance(data.get('blocked_actions'), list)
        if data['results']:
            row = data['results'][0]
            for key in (
                'trigger_type',
                'fighter_or_event_name',
                'result_found',
                'winner',
                'method',
                'round_time',
                'official_source_url',
                'source_confidence',
                'recommended_action',
            ):
                self.assertIn(key, row)

    def test_signal_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/signal-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('breakdown', data)
        self.assertIn('has_data', data)
        self.assertIsInstance(data.get('breakdown'), list)
        buckets = [b['bucket'] for b in data['breakdown']]
        self.assertIn('0.00–0.10', buckets)
        self.assertIn('0.11–0.20', buckets)
        self.assertIn('0.21–0.30', buckets)
        self.assertIn('0.31+', buckets)

    def test_signal_breakdown_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/signal-breakdown', resp.data)

    def test_method_round_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/method-round-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('method_accuracy', data)
        self.assertIn('round_accuracy', data)
        self.assertIn('stoppage_propensity_buckets', data)
        self.assertIn('round_finish_tendency_buckets', data)
        m = data['method_accuracy']
        for key in ('total_available', 'method_hits', 'method_misses', 'method_accuracy_pct'):
            self.assertIn(key, m)
        r = data['round_accuracy']
        for key in ('total_available', 'round_hits', 'round_misses', 'round_accuracy_pct'):
            self.assertIn(key, r)
        # Each propensity list should have 4 buckets
        self.assertEqual(len(data['stoppage_propensity_buckets']), 4)
        self.assertEqual(len(data['round_finish_tendency_buckets']), 4)
        buckets = [b['bucket'] for b in data['stoppage_propensity_buckets']]
        for expected in ('0.00–0.25', '0.26–0.50', '0.51–0.75', '0.76–1.00'):
            self.assertIn(expected, buckets)

    def test_method_round_panels_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/method-round-breakdown', resp.data)

    def test_confidence_calibration_contract(self):
        resp = self.client.get('/api/accuracy/confidence-calibration')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('calibration', data)
        self.assertIsInstance(data['calibration'], list)
        self.assertEqual(len(data['calibration']), 5)
        buckets = [b['bucket'] for b in data['calibration']]
        for expected in ('0.50–0.60', '0.61–0.70', '0.71–0.80', '0.81–0.90', '0.91–1.00'):
            self.assertIn(expected, buckets)
        for b in data['calibration']:
            for key in ('total_compared', 'predicted_confidence_avg', 'actual_win_rate', 'calibration_gap'):
                self.assertIn(key, b)

    def test_confidence_calibration_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/confidence-calibration', resp.data)

    def test_error_patterns_contract(self):
        resp = self.client.get('/api/accuracy/error-patterns')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('total_misses', data)
        self.assertIn('top_failure_patterns', data)
        self.assertIn('miss_breakdowns', data)
        bd = data['miss_breakdowns']
        for key in ('by_signal_gap', 'by_confidence', 'by_method', 'by_round_range'):
            self.assertIn(key, bd)
            self.assertIsInstance(bd[key], list)
        self.assertIsInstance(data['top_failure_patterns'], list)
        self.assertIsInstance(data['total_misses'], int)

    def test_failure_patterns_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/error-patterns', resp.data)

    def test_signal_coverage_contract(self):
        resp = self.client.get('/api/accuracy/signal-coverage')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('coverage', data)
        cov = data['coverage']
        for bucket in ('overall', 'resolved', 'unresolved'):
            self.assertIn(bucket, cov)
            b = cov[bucket]
            self.assertIn('total_predictions', b)
            for field in ('signal_gap_coverage_pct', 'stoppage_propensity_coverage_pct',
                          'round_finish_tendency_coverage_pct', 'predicted_method_coverage_pct',
                          'predicted_round_coverage_pct'):
                self.assertIn(field, b)

    def test_signal_coverage_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/signal-coverage', resp.data)

    def test_structural_signal_backfill_planner_contract(self):
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('planner', data)
        planner = data['planner']
        for key in ('total_predictions', 'predictions_needing_backfill', 'structural_fields', 'summary', 'priority_queue'):
            self.assertIn(key, planner)
        summary = planner['summary']
        for key in ('unresolved_needing_backfill', 'resolved_needing_backfill', 'resolved_miss_needing_backfill'):
            self.assertIn(key, summary)
        # backwards-compat: eligibility_counts must now also be present
        self.assertIn('eligibility_counts', summary)
        self.assertIsInstance(planner['priority_queue'], list)
        if planner['priority_queue']:
            row = planner['priority_queue'][0]
            for key in ('fight_id', 'missing_signals', 'missing_count', 'priority_score', 'priority_tier'):
                self.assertIn(key, row)

    def test_planner_queue_rows_have_eligibility_fields(self):
        """Every queue entry must carry all four eligibility fields."""
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        queue = data['planner']['priority_queue']
        for row in queue:
            for key in ('eligibility_class', 'eligibility_reason', 'source_value_status',
                        'source_values_found', 'recommended_action'):
                self.assertIn(key, row, f"Missing key '{key}' in queue row for {row.get('fight_id')}")

    def test_planner_eligibility_counts_keys_present(self):
        """Summary must contain all four eligibility class counters."""
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        ec = data['planner']['summary']['eligibility_counts']
        for cls in ('READY_FOR_BACKFILL', 'BLOCKED_NEEDS_SOURCE_VALUES',
                    'REQUIRES_ENGINE_RERUN', 'UNRESOLVED_RESULT_PENDING'):
            self.assertIn(cls, ec)

    def test_structural_signal_backfill_planner_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/structural-signal-backfill-planner', resp.data)


# ---------------------------------------------------------------------------
# Unit tests for planner eligibility classification logic
# These tests inject a synthetic ledger directly to isolate classification.
# ---------------------------------------------------------------------------

def _make_ledger(tmp_path: Path, rows: list) -> Path:
    p = tmp_path / "ops" / "accuracy"
    p.mkdir(parents=True, exist_ok=True)
    ledger = p / "accuracy_ledger.json"
    ledger.write_text(json.dumps(rows), encoding="utf-8")
    return ledger


class TestPlannerEligibilityClassification(unittest.TestCase):

    def _run_planner(self, rows):
        """Run the planner against a synthetic ledger in a temp directory."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = _make_ledger(tmp_path, rows)
            # Patch _load_accuracy_ledger_rows to read from tmp ledger
            # and patch the root so source_file paths are resolved safely.
            from app import _load_accuracy_ledger_rows as real_loader
            def fake_loader(path):
                return real_loader(ledger)
            with patch("app._load_accuracy_ledger_rows", side_effect=fake_loader):
                # Also patch the root used inside the function for prediction_path checks
                with patch("app.Path") as mock_path_cls:
                    # Allow Path to work normally except when resolving repo root
                    import pathlib
                    original_path = pathlib.Path

                    class PatchedPath(pathlib.Path):
                        _flavour = pathlib.Path(".")._flavour

                    # Simpler approach: just call the real function and trust fake_loader
                    mock_path_cls.side_effect = original_path
                    return _build_structural_signal_backfill_planner()

    def _run_planner_direct(self, rows):
        """Inject rows directly via monkeypatching _load_accuracy_ledger_rows."""
        with patch("app._load_accuracy_ledger_rows", return_value=rows):
            return _build_structural_signal_backfill_planner()

    def _intermediate_row(self, fight_id, resolved=True, hit_winner=True):
        return {
            "fight_id": fight_id,
            "schema_variant": "intermediate",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": resolved,
            "hit_winner": hit_winner,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": "UNKNOWN",
        }

    def _resolved_capable_row(self, fight_id, hit_winner=True):
        return {
            "fight_id": fight_id,
            "schema_variant": "prediction_record_v1",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": True,
            "hit_winner": hit_winner,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": "2026-01-01",
        }

    def _unresolved_row(self, fight_id):
        return {
            "fight_id": fight_id,
            "schema_variant": "prediction_record_v1",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": False,
            "hit_winner": None,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": None,
        }

    def test_intermediate_schema_classifies_as_blocked(self):
        """Intermediate-schema narrative records must classify as BLOCKED_NEEDS_SOURCE_VALUES."""
        rows = [self._intermediate_row("bentley_vs_saavedra_prediction")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'BLOCKED_NEEDS_SOURCE_VALUES')
        self.assertFalse(queue[0]['source_values_found'])
        self.assertEqual(queue[0]['recommended_action'], 'requires_source_values_or_engine_rerun')

    def test_all_five_batch1_fights_classify_as_blocked(self):
        """All five Batch 1 intermediate fights must classify as BLOCKED_NEEDS_SOURCE_VALUES."""
        fight_ids = [
            "bentley_vs_saavedra_prediction",
            "goodman_vs_ruiz_prediction",
            "pat_brown_vs_vasil_ducar_prediction",
            "riley_vs_masternak_prediction",
            "wilder_vs_chisora_prediction",
        ]
        rows = [self._intermediate_row(fid) for fid in fight_ids]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        self.assertTrue(result['has_data'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 5)
        for row in queue:
            self.assertEqual(row['eligibility_class'], 'BLOCKED_NEEDS_SOURCE_VALUES',
                             f"{row['fight_id']} should be BLOCKED_NEEDS_SOURCE_VALUES")
            self.assertFalse(row['source_values_found'])
        ec = result['planner']['summary']['eligibility_counts']
        self.assertEqual(ec['BLOCKED_NEEDS_SOURCE_VALUES'], 5)
        self.assertEqual(ec['READY_FOR_BACKFILL'], 0)

    def test_null_structural_without_source_values_not_ready(self):
        """Records with null structural fields and no source values must not be READY_FOR_BACKFILL."""
        rows = [self._intermediate_row("some_fight")]
        result = self._run_planner_direct(rows)
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertNotEqual(queue[0]['eligibility_class'], 'READY_FOR_BACKFILL')

    def test_unresolved_result_classifies_as_unresolved_pending(self):
        """Records with unresolved fight results must classify as UNRESOLVED_RESULT_PENDING."""
        rows = [self._unresolved_row("future_fight")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'UNRESOLVED_RESULT_PENDING')
        self.assertEqual(queue[0]['recommended_action'], 'wait_for_result_resolution')

    def test_capable_schema_resolved_classifies_as_requires_engine_rerun(self):
        """Resolved v1 records with missing structural values classify as REQUIRES_ENGINE_RERUN."""
        rows = [self._resolved_capable_row("some_v1_fight")]
        result = self._run_planner_direct(rows)
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'REQUIRES_ENGINE_RERUN')
        self.assertEqual(queue[0]['recommended_action'], 'requires_engine_rerun_with_approval')

    def test_planner_returns_200_ok_true_has_data(self):
        """Planner must return ok:true and has_data:true when rows are present."""
        rows = [self._intermediate_row("any_fight")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        self.assertTrue(result['has_data'])

    def test_existing_summary_keys_backwards_compatible(self):
        """Pre-existing summary keys must still be present alongside eligibility_counts."""
        rows = [self._intermediate_row("a"), self._unresolved_row("b")]
        result = self._run_planner_direct(rows)
        summary = result['planner']['summary']
        for key in ('unresolved_needing_backfill', 'resolved_needing_backfill',
                    'resolved_miss_needing_backfill', 'eligibility_counts'):
            self.assertIn(key, summary, f"Missing backwards-compat key: {key}")

if __name__ == '__main__':
    unittest.main()
