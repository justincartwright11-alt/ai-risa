import unittest
from workflows.coverage_readiness import coverage_readiness
from workflows.report_readiness import report_readiness
from workflows.report_candidate_pack import report_candidate_pack
from workflows.scouting_input_pack import scouting_input_pack
from workflows.bout_dossier_pack import bout_dossier_pack
from workflows.report_brief_pack import report_brief_pack
from workflows.narrative_input_pack import narrative_input_pack
from workflows.report_skeleton_pack import report_skeleton_pack
from workflows.draft_report_pack import draft_report_pack

def make_bout(a, b, notes=None, weight_class=None, scheduled_rounds=None, is_title_fight=None):
    bout = {"fighter_a": a, "fighter_b": b}
    if notes is not None:
        bout["normalization_notes"] = notes
    if weight_class is not None:
        bout["weight_class"] = weight_class
    if scheduled_rounds is not None:
        bout["scheduled_rounds"] = scheduled_rounds
    if is_title_fight is not None:
        bout["is_title_fight"] = is_title_fight
    return bout

def make_event(event_name, bouts):
    return {
        "event_name": event_name,
        "discovered_bout_slots": bouts
    }

class TestDraftReportPack(unittest.TestCase):
    def test_fully_ready(self):
        event = make_event("E1", [make_bout("A", "B"), make_bout("C", "D")])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        self.assertEqual(draft["draft_report_pack_status"], "ready")
        self.assertEqual(draft["total_bouts"], 2)
        self.assertEqual(len(draft["ready_draft_reports"]), 2)
        self.assertEqual(len(draft["blocked_draft_reports"]), 0)
        for d in draft["ready_draft_reports"]:
            self.assertEqual(d["draft_report_status"], "ready")
            self.assertIn("fighter_a", d)
            self.assertIn("fighter_b", d)
            self.assertIn("report_skeleton_snapshot", d)
            self.assertIn("narrative_snapshot", d)
            self.assertEqual(d["event_name"], "E1")
            self.assertEqual(set(d["draft_sections"].keys()), {
                "headline", "matchup_summary", "fighter_a_section", "fighter_b_section", "tactical_section", "risk_flags", "readiness_notes"
            })

    def test_mixed_ready_blocked(self):
        event = make_event("E2", [
            make_bout("A", "B"),
            make_bout("", "D", notes=["fighters_invalid"]),
            make_bout(None, "E", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        self.assertEqual(draft["draft_report_pack_status"], "partial")
        self.assertEqual(draft["total_bouts"], 3)
        self.assertEqual(len(draft["ready_draft_reports"]), 1)
        self.assertEqual(len(draft["blocked_draft_reports"]), 2)
        # Ready draft
        ready_draft = draft["ready_draft_reports"][0]
        self.assertEqual(ready_draft["draft_report_status"], "ready")
        self.assertEqual(ready_draft["bout_index"], 0)
        # Blocked drafts
        for d in draft["blocked_draft_reports"]:
            self.assertEqual(d["draft_report_status"], "blocked")
            self.assertIn(d["bout_index"], [1, 2])
            self.assertIn("blocker_reason", d)
            self.assertIn("report_skeleton_snapshot", d)

    def test_fully_blocked(self):
        event = make_event("E3", [
            make_bout("", None, notes=["fighters_invalid"]),
            make_bout(None, "", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        self.assertEqual(draft["draft_report_pack_status"], "blocked")
        self.assertEqual(draft["total_bouts"], 2)
        self.assertEqual(len(draft["ready_draft_reports"]), 0)
        self.assertEqual(len(draft["blocked_draft_reports"]), 2)
        for d in draft["blocked_draft_reports"]:
            self.assertEqual(d["draft_report_status"], "blocked")
            self.assertIn("blocker_reason", d)
            self.assertIn("report_skeleton_snapshot", d)

    def test_stable_bout_index_routing(self):
        event = make_event("E4", [
            make_bout("A", "B"),
            make_bout("C", "D"),
            make_bout("", "E", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        indices = [d["bout_index"] for d in draft["ready_draft_reports"] + draft["blocked_draft_reports"]]
        self.assertEqual(indices, [0, 1, 2])

    def test_stable_blocker_carry_through(self):
        event = make_event("E5", [
            make_bout("A", "B"),
            make_bout("", "D", notes=["fighters_invalid"])
        ])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        blocked = draft["blocked_draft_reports"][0]
        self.assertEqual(blocked["blocker_reason"], "fighters_invalid")

    def test_stable_draft_section_shapes(self):
        event = make_event("E6", [make_bout("A", "B")])
        coverage = coverage_readiness(event)
        readiness = report_readiness(coverage)
        pack_summary, ready, blocked = report_candidate_pack(event, readiness)
        pack_result = {
            **pack_summary,
            "ready_report_candidates": ready,
            "blocked_report_candidates": blocked
        }
        scouting = scouting_input_pack(pack_result)
        dossier = bout_dossier_pack(scouting)
        brief = report_brief_pack(dossier)
        narrative = narrative_input_pack(brief)
        skeleton = report_skeleton_pack(narrative)
        draft = draft_report_pack(skeleton)
        sections = draft["ready_draft_reports"][0]["draft_sections"]
        self.assertEqual(set(sections.keys()), {
            "headline", "matchup_summary", "fighter_a_section", "fighter_b_section", "tactical_section", "risk_flags", "readiness_notes"
        })
