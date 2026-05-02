import os
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader

from operator_dashboard.prf_report_export import write_pdf_report


class PremiumReportExportTests(unittest.TestCase):
    def _build_report_obj(self) -> dict:
        return {
            "event_id": "ares_fc_39",
            "event_name": "ARES FC 39",
            "matchup_id": "prf_q_test_visual",
            "fighter_a": "Alpha Fighter",
            "fighter_b": "Beta Fighter",
            "report_quality_status": "customer_ready",
            "operator_approval_state": True,
            "analysis_source_type": "linked_analysis",
            "generated_at": "2026-05-02T12:00:00Z",
            "populated_sections": [
                "headline_prediction",
                "executive_summary",
                "matchup_snapshot",
                "scenario_tree",
            ],
            "missing_engine_outputs": ["collapse_trigger_engine"],
            "section_source_map": {
                "headline_prediction": {
                    "source_type": "linked_analysis",
                    "contributing_engines": [
                        "tactical_keys_engine",
                        "round_band_projection_engine",
                    ],
                },
                "scenario_tree": {
                    "source_type": "linked_analysis",
                    "contributing_engines": ["scenario_tree_method_pathways_engine"],
                },
            },
        }

    def _build_sections(self) -> dict:
        return {
            "cover_page": "Operator-approved premium report for visual layout verification.",
            "headline_prediction": "Projected winner: Alpha Fighter via decision at 68% confidence.",
            "executive_summary": "Alpha should control range and tempo while Beta must force clinch entries.",
            "matchup_snapshot": "Alpha owns the cleaner jab and distance management profile.",
            "decision_structure": "If Alpha keeps center cage, decision equity rises materially.",
            "energy_use": "Alpha is projected to spend cleaner in rounds one and two.",
            "fatigue_failure_points": "Beta shows historical slowdown after reactive scrambling exchanges.",
            "mental_condition": "Alpha has the calmer late-round decision tree.",
            "collapse_triggers": "Beta becomes vulnerable if the jab forces rushed level changes.",
            "deception_and_unpredictability": "Beta can still flip sequences with sudden stance changes.",
            "round_by_round_control_shifts": "Round 1 Alpha range control. Round 2 even. Round 3 Alpha edge.",
            "scenario_tree": "Primary path: Alpha decision. Contingency path: Beta scramble-heavy upset.",
            "risk_warnings": "Risk warning: Beta's volatility remains live if pressure chains connect.",
            "operator_notes": "Maintain deterministic section ordering during export validation.",
        }

    def _extract_pdf_text(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def test_write_pdf_report_uses_visual_layout_when_flag_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"AI_RISA_PRF_VISUAL_INTELLIGENCE_LAYOUT": "1"}, clear=False):
                result = write_pdf_report(self._build_report_obj(), self._build_sections(), tmpdir)

            self.assertTrue(result.get("ok"))
            self.assertTrue(os.path.exists(result.get("file_path")))

            pdf_text = self._extract_pdf_text(result.get("file_path"))
            self.assertIn("Premium Cover", pdf_text)
            self.assertIn("Executive Intelligence", pdf_text)
            self.assertIn("Combat Dynamics", pdf_text)
            self.assertIn("Scenario and Control", pdf_text)
            self.assertIn("Traceability Appendix", pdf_text)
            self.assertIn("Section Source Map", pdf_text)
            self.assertIn("Missing Engine Outputs", pdf_text)

            self.assertLess(pdf_text.find("Headline Prediction"), pdf_text.find("Executive Summary"))
            self.assertLess(pdf_text.find("Executive Summary"), pdf_text.find("Matchup Snapshot"))
            self.assertLess(pdf_text.find("Round-by-Round Control Shifts"), pdf_text.find("Scenario Tree / Method Pathways"))

    def test_write_pdf_report_uses_legacy_layout_when_flag_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"AI_RISA_PRF_VISUAL_INTELLIGENCE_LAYOUT": "0"}, clear=False):
                result = write_pdf_report(self._build_report_obj(), self._build_sections(), tmpdir)

            self.assertTrue(result.get("ok"))
            self.assertTrue(os.path.exists(result.get("file_path")))

            pdf_text = self._extract_pdf_text(result.get("file_path"))
            self.assertIn("1. Cover Page", pdf_text)
            self.assertIn("14. Operator Notes", pdf_text)
            self.assertNotIn("Traceability Appendix", pdf_text)


if __name__ == "__main__":
    unittest.main()