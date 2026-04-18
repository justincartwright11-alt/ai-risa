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
from workflows.final_report_pack import final_report_pack
from workflows.report_release_pack import report_release_pack

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

class TestReportReleasePack(unittest.TestCase):
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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        self.assertEqual(release["report_release_pack_status"], "ready")
        self.assertEqual(release["total_bouts"], 2)
        self.assertEqual(len(release["ready_release_reports"]), 2)
        self.assertEqual(len(release["blocked_release_reports"]), 0)
        for r in release["ready_release_reports"]:
            self.assertEqual(r["report_release_status"], "ready")
            self.assertIn("fighter_a", r)
            self.assertIn("fighter_b", r)
            self.assertIn("final_report_snapshot", r)
            self.assertIn("draft_report_snapshot", r)
            self.assertEqual(r["event_name"], "E1")
            self.assertEqual(set(r["release_sections"].keys()), {
                "headline", "release_summary", "fighter_a_release", "fighter_b_release", "matchup_release", "risk_flags", "release_notes"
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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        self.assertEqual(release["report_release_pack_status"], "partial")
        self.assertEqual(release["total_bouts"], 3)
        self.assertEqual(len(release["ready_release_reports"]), 1)
        self.assertEqual(len(release["blocked_release_reports"]), 2)
        # Ready release
        ready_release = release["ready_release_reports"][0]
        self.assertEqual(ready_release["report_release_status"], "ready")
        self.assertEqual(ready_release["bout_index"], 0)
        # Blocked releases
        for r in release["blocked_release_reports"]:
            self.assertEqual(r["report_release_status"], "blocked")
            self.assertIn(r["bout_index"], [1, 2])
            self.assertIn("blocker_reason", r)
            self.assertIn("final_report_snapshot", r)

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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        self.assertEqual(release["report_release_pack_status"], "blocked")
        self.assertEqual(release["total_bouts"], 2)
        self.assertEqual(len(release["ready_release_reports"]), 0)
        self.assertEqual(len(release["blocked_release_reports"]), 2)
        for r in release["blocked_release_reports"]:
            self.assertEqual(r["report_release_status"], "blocked")
            self.assertIn("blocker_reason", r)
            self.assertIn("final_report_snapshot", r)

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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        indices = [r["bout_index"] for r in release["ready_release_reports"] + release["blocked_release_reports"]]
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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        blocked = release["blocked_release_reports"][0]
        self.assertEqual(blocked["blocker_reason"], "fighters_invalid")

    def test_stable_release_section_shapes(self):
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
        final = final_report_pack(draft)
        release = report_release_pack(final)
        sections = release["ready_release_reports"][0]["release_sections"]
        self.assertEqual(set(sections.keys()), {
            "headline", "release_summary", "fighter_a_release", "fighter_b_release", "matchup_release", "risk_flags", "release_notes"
        })
