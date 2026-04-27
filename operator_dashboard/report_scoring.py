"""
Report Scoring System for AI-RISA Premium Reports

Scores 18 report segments against actual fight outcomes using a rubric-based model.
All percentages are confidence-based, not objective truth.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import re


REPORT_SEGMENTS = [
    "executive_summary",
    "matchup_snapshot",
    "decision_structure",
    "tactical_edges",
    "energy_use",
    "fatigue_failure_points",
    "mental_condition",
    "collapse_triggers",
    "deception_unpredictability",
    "fight_control",
    "fight_turns",
    "scenario_tree",
    "round_by_round_outlook",
    "risk_factors",
    "what_could_flip",
    "corner_notes",
    "final_projection",
    "confidence_explanation",
]


class ScoringRubric:
    """Rubric-based scoring model for report segments"""
    
    CORRECT_WINNER = 40  # Correct winner prediction
    CORRECT_METHOD = 30  # Correct method (decision/KO/submission/etc)
    CORRECT_ROUND = 15   # Correct round/timing direction (early/mid/late)
    CORRECT_CONTROL = 10 # Correct control pattern (grappling/striking/pace)
    CORRECT_FATIGUE = 5  # Correct fatigue trajectory
    
    @staticmethod
    def score_executive_summary(report_text: str, actual_winner: str, actual_method: str, actual_round: int) -> Tuple[int, str]:
        """Score executive summary: does it predict the correct winner and method?"""
        score = 0
        reasons = []
        
        # Winner detection
        if actual_winner.lower() in report_text.lower():
            score += ScoringRubric.CORRECT_WINNER
            reasons.append("Predicted correct winner")
        else:
            reasons.append("Missed winner prediction")
        
        # Method detection
        method_keywords = {"decision": ["decision", "scorecard", "judges"],
                          "knockout": ["knockout", "ko", "tko", "knocked out"],
                          "submission": ["submission", "tap", "choke", "crank"]}
        method_lower = actual_method.lower()
        if method_lower in method_keywords:
            keywords = method_keywords[method_lower]
            if any(kw in report_text.lower() for kw in keywords):
                score += ScoringRubric.CORRECT_METHOD
                reasons.append("Predicted correct method direction")
            else:
                reasons.append("Missed method prediction")
        
        return min(score, 100), "; ".join(reasons)
    
    @staticmethod
    def score_matchup_snapshot(report_text: str, fighter_a: str, fighter_b: str, actual_winner: str) -> Tuple[int, str]:
        """Score matchup snapshot: does it characterize both fighters correctly?"""
        score = 50  # Base credit for existing characterization
        reasons = ["Snapshot characterization exists"]
        
        if actual_winner.lower() in report_text.lower():
            score += 25
            reasons.append("Identifies likely winner")
        else:
            reasons.append("Unclear on winner")
        
        return min(score, 100), "; ".join(reasons)
    
    @staticmethod
    def score_decision_structure(report_text: str, actual_winner: str, actual_method: str) -> Tuple[int, str]:
        """Score decision structure: does it predict a path to the actual winner?"""
        score = 0
        reasons = []
        
        if actual_winner.lower() in report_text.lower():
            score += ScoringRubric.CORRECT_WINNER
            reasons.append("Winner path identified")
        else:
            reasons.append("Missed winner path")
        
        # Method pathway
        if actual_method.lower() in report_text.lower():
            score += ScoringRubric.CORRECT_METHOD
            reasons.append("Method path identified")
        
        return min(score, 100), "; ".join(reasons)
    
    @staticmethod
    def score_tactical_edges(report_text: str, control_pattern: str) -> Tuple[int, str]:
        """Score tactical edges: does it identify the actual control pattern?"""
        score = 0
        reasons = []
        
        control_keywords = {
            "grappling": ["grappling", "wrestling", "clinch", "takedown", "submission"],
            "striking": ["striking", "punching", "kicking", "boxing", "muay thai"],
            "movement": ["movement", "footwork", "circling", "distance"],
            "pressure": ["pressure", "pace", "intensity", "output"],
        }
        
        pattern_keywords = control_keywords.get(control_pattern.lower(), [])
        if any(kw in report_text.lower() for kw in pattern_keywords):
            score += ScoringRubric.CORRECT_CONTROL
            reasons.append(f"Identified {control_pattern} pattern")
        else:
            reasons.append(f"Missed {control_pattern} pattern")
        
        score += 50  # Base credit for tactical analysis
        reasons.append("Tactical analysis present")
        
        return min(score, 100), "; ".join(reasons)
    
    @staticmethod
    def score_generic_segment(report_text: str, actual_element: str) -> Tuple[int, str]:
        """Generic scoring for other segments"""
        if not report_text or not report_text.strip():
            return 0, "No content"
        
        score = 60  # Base credit for having content
        reasons = ["Segment present"]
        
        if actual_element and actual_element.lower() in report_text.lower():
            score = 85
            reasons = ["Content aligned with actual outcome"]
        
        return min(score, 100), "; ".join(reasons)
    
    @staticmethod
    def score_final_projection(report_text: str, actual_winner: str, actual_method: str, actual_round: int) -> Tuple[int, str]:
        """Score final projection: accuracy of winner, method, and round prediction"""
        score = 0
        reasons = []
        
        # Winner
        if actual_winner.lower() in report_text.lower():
            score += ScoringRubric.CORRECT_WINNER
            reasons.append("Winner prediction accurate")
        else:
            reasons.append("Winner prediction missed")
        
        # Method
        if actual_method.lower() in report_text.lower():
            score += ScoringRubric.CORRECT_METHOD
            reasons.append("Method prediction accurate")
        else:
            reasons.append("Method prediction missed")
        
        # Round/timing
        round_keywords = {
            "early": ["round 1", "round 2", "early", "first round"],
            "mid": ["round 3", "round 4", "middle", "mid-fight"],
            "late": ["round 5", "late", "championship rounds"],
        }
        timing = "early" if actual_round <= 2 else ("mid" if actual_round <= 4 else "late")
        timing_keywords = round_keywords.get(timing, [])
        if any(kw in report_text.lower() for kw in timing_keywords):
            score += ScoringRubric.CORRECT_ROUND
            reasons.append("Round/timing aligned")
        
        return min(score, 100), "; ".join(reasons)


class ReportScorer:
    """Scores a complete premium report against actual fight outcome"""
    
    def __init__(self, ai_risa_data_path: str = "c:/ai_risa_data"):
        self.ai_risa_data_path = Path(ai_risa_data_path)
        self.scoring_ledger_path = self.ai_risa_data_path / "reports" / "scoring_ledger.jsonl"
    
    def score_report(
        self,
        report_dict: Dict[str, str],
        actual_winner: str,
        actual_method: str,
        actual_round: int,
        fighter_a: str,
        fighter_b: str,
        control_pattern: str = "grappling",
    ) -> Dict[str, Any]:
        """
        Score a complete report against actual outcome.
        
        Returns: {
            'fight_id': str,
            'timestamp': str,
            'segments': {segment: {'score': int, 'reason': str}},
            'metrics': {
                'winner_accuracy': int,
                'method_accuracy': int,
                'round_accuracy': int,
                'total_score': int,
            },
            'summary': str,
        }
        """
        segments_scored = {}
        
        # Score each segment
        rubric = ScoringRubric()
        
        for segment in REPORT_SEGMENTS:
            segment_text = report_dict.get(segment, "")
            
            if segment == "executive_summary":
                score, reason = rubric.score_executive_summary(segment_text, actual_winner, actual_method, actual_round)
            elif segment == "matchup_snapshot":
                score, reason = rubric.score_matchup_snapshot(segment_text, fighter_a, fighter_b, actual_winner)
            elif segment == "decision_structure":
                score, reason = rubric.score_decision_structure(segment_text, actual_winner, actual_method)
            elif segment == "tactical_edges":
                score, reason = rubric.score_tactical_edges(segment_text, control_pattern)
            elif segment == "final_projection":
                score, reason = rubric.score_final_projection(segment_text, actual_winner, actual_method, actual_round)
            else:
                score, reason = rubric.score_generic_segment(segment_text, actual_winner)
            
            segments_scored[segment] = {
                "score": score,
                "reason": reason,
            }
        
        # Calculate overall metrics
        all_scores = [s["score"] for s in segments_scored.values()]
        total_score = sum(all_scores) // len(all_scores) if all_scores else 0
        
        # Winner accuracy
        exec_summary = report_dict.get("executive_summary", "")
        winner_accuracy = 100 if actual_winner.lower() in exec_summary.lower() else 0
        
        # Method accuracy
        method_accuracy = 100 if actual_method.lower() in exec_summary.lower() else 0
        
        # Round accuracy
        round_keywords = {
            "early": ["round 1", "round 2", "early"],
            "mid": ["round 3", "round 4", "middle"],
            "late": ["round 5", "late", "championship"],
        }
        timing = "early" if actual_round <= 2 else ("mid" if actual_round <= 4 else "late")
        round_accuracy = 100 if any(kw in exec_summary.lower() for kw in round_keywords.get(timing, [])) else 0
        
        result = {
            "fight_id": f"{fighter_a}_vs_{fighter_b}",
            "timestamp": datetime.utcnow().isoformat(),
            "segments": segments_scored,
            "metrics": {
                "winner_accuracy": winner_accuracy,
                "method_accuracy": method_accuracy,
                "round_accuracy": round_accuracy,
                "total_report_score": total_score,
            },
            "summary": f"Overall: {total_score}% | Winner: {winner_accuracy}% | Method: {method_accuracy}% | Round: {round_accuracy}%",
        }
        
        # Persist to ledger
        self._persist_score(result)
        
        return result
    
    def _persist_score(self, score_result: Dict[str, Any]):
        """Append score to ledger"""
        self.scoring_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.scoring_ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(score_result) + "\n")
    
    def get_rolling_success_rate(self) -> Dict[str, Any]:
        """Calculate rolling AI-RISA success rate from ledger"""
        if not self.scoring_ledger_path.exists():
            return {
                "total_fights_scored": 0,
                "average_report_score": 0,
                "rolling_success_rate": 0,
            }
        
        scores = []
        with open(self.scoring_ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    result = json.loads(line.strip())
                    scores.append(result.get("metrics", {}).get("total_report_score", 0))
                except:
                    pass
        
        if not scores:
            return {
                "total_fights_scored": 0,
                "average_report_score": 0,
                "rolling_success_rate": 0,
            }
        
        avg = sum(scores) // len(scores)
        return {
            "total_fights_scored": len(scores),
            "average_report_score": avg,
            "rolling_success_rate": avg,
        }
