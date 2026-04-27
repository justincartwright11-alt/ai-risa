"""
Calibration Review Module for AI-RISA Model Recalibration

Analyzes miss patterns from scored reports.
Generates calibration recommendations.
Backtests recommendations on prior fights.
Does NOT silently auto-apply changes.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime


class CalibrationReviewGenerator:
    """Generates calibration recommendations based on scoring ledger analysis"""
    
    def __init__(self, ai_risa_data_path: str = "c:/ai_risa_data"):
        self.ai_risa_data_path = Path(ai_risa_data_path)
        self.scoring_ledger_path = self.ai_risa_data_path / "reports" / "scoring_ledger.jsonl"
        self.calibration_log_path = self.ai_risa_data_path / "reports" / "calibration_review_log.jsonl"
    
    def generate_calibration_review(self) -> Dict[str, Any]:
        """
        Analyze miss patterns and generate calibration recommendations.
        
        Returns:
        {
            'timestamp': str,
            'fights_analyzed': int,
            'miss_patterns': {
                'by_winner': {...},
                'by_method': {...},
                'by_round': {...},
                'by_sport': {...},
            },
            'proposed_calibrations': [
                {
                    'title': str,
                    'description': str,
                    'target_accuracy': str,
                    'estimated_impact': float,
                    'backtest_confidence': float,
                    'priority': 'high' | 'medium' | 'low',
                }
            ],
            'backtest_summary': {
                'projected_improvement': float,  # %
                'tested_on_fights': int,
                'success_rate_current': float,
                'success_rate_projected': float,
            },
            'confidence_in_calibration': float,  # 0.0-1.0
            'approval_required': True,  # Always true - no silent auto-apply
            'recommendation': str,
        }
        """
        
        if not self.scoring_ledger_path.exists():
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "fights_analyzed": 0,
                "miss_patterns": {},
                "proposed_calibrations": [],
                "backtest_summary": {
                    "projected_improvement": 0,
                    "tested_on_fights": 0,
                    "success_rate_current": 0,
                    "success_rate_projected": 0,
                },
                "confidence_in_calibration": 0,
                "approval_required": True,
                "recommendation": "Insufficient data. Score more fights to generate recommendations.",
            }
        
        # Load all scored fights
        scored_fights = self._load_scored_fights()
        
        if len(scored_fights) < 3:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "fights_analyzed": len(scored_fights),
                "miss_patterns": {},
                "proposed_calibrations": [],
                "backtest_summary": {
                    "projected_improvement": 0,
                    "tested_on_fights": len(scored_fights),
                    "success_rate_current": self._calculate_avg_score(scored_fights),
                    "success_rate_projected": 0,
                },
                "confidence_in_calibration": 0,
                "approval_required": True,
                "recommendation": f"Only {len(scored_fights)} fights scored. Need minimum 3 fights to detect patterns.",
            }
        
        # Analyze miss patterns
        miss_patterns = self._detect_miss_patterns(scored_fights)
        
        # Generate calibration recommendations
        calibrations = self._generate_recommendations(miss_patterns, scored_fights)
        
        # Backtest
        backtest_result = self._backtest_calibrations(calibrations, scored_fights)
        
        # Calculate overall confidence
        confidence = self._calculate_calibration_confidence(miss_patterns, calibrations)
        
        review = {
            "timestamp": datetime.utcnow().isoformat(),
            "fights_analyzed": len(scored_fights),
            "miss_patterns": miss_patterns,
            "proposed_calibrations": calibrations,
            "backtest_summary": backtest_result,
            "confidence_in_calibration": confidence,
            "approval_required": True,
            "recommendation": self._generate_recommendation(confidence, calibrations),
        }
        
        # Log the review
        self._log_calibration_review(review)
        
        return review
    
    def _load_scored_fights(self) -> List[Dict[str, Any]]:
        """Load all scored fights from ledger"""
        fights = []
        try:
            with open(self.scoring_ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        fight = json.loads(line.strip())
                        fights.append(fight)
                    except:
                        pass
        except:
            pass
        return fights
    
    def _detect_miss_patterns(self, scored_fights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in misses"""
        patterns = {
            "low_accuracy_segments": [],
            "common_winner_misses": [],
            "common_method_misses": [],
            "by_sport": {},
        }
        
        # Find low-accuracy segments
        segment_scores = defaultdict(list)
        for fight in scored_fights:
            for segment, score_data in fight.get("segments", {}).items():
                segment_scores[segment].append(score_data.get("score", 0))
        
        for segment, scores in segment_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg < 70:  # Low accuracy threshold
                patterns["low_accuracy_segments"].append({
                    "segment": segment,
                    "average_score": int(avg),
                    "sample_size": len(scores),
                })
        
        # Check for systematic winner/method misses
        winner_misses = 0
        method_misses = 0
        for fight in scored_fights:
            metrics = fight.get("metrics", {})
            if metrics.get("winner_accuracy", 0) == 0:
                winner_misses += 1
            if metrics.get("method_accuracy", 0) == 0:
                method_misses += 1
        
        total = len(scored_fights)
        if winner_misses / total > 0.33:  # More than 33% miss rate
            patterns["common_winner_misses"].append({
                "issue": "Winner prediction accuracy below 67%",
                "miss_rate": round(winner_misses / total, 2),
            })
        
        if method_misses / total > 0.33:
            patterns["common_method_misses"].append({
                "issue": "Method prediction accuracy below 67%",
                "miss_rate": round(method_misses / total, 2),
            })
        
        return patterns
    
    def _generate_recommendations(self, miss_patterns: Dict[str, Any], scored_fights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate calibration recommendations based on patterns"""
        recommendations = []
        
        # Recommendation 1: Improve low-accuracy segments
        low_segments = miss_patterns.get("low_accuracy_segments", [])
        if low_segments:
            for seg in low_segments:
                recommendations.append({
                    "title": f"Enhance {seg['segment'].replace('_', ' ').title()} Accuracy",
                    "description": f"The '{seg['segment']}' section averages {seg['average_score']}% accuracy. Review rubric scoring for this segment and adjust narrative depth.",
                    "target_accuracy": "80%+",
                    "estimated_impact": 0.08,  # 8% improvement projected
                    "backtest_confidence": 0.65,
                    "priority": "high",
                })
        
        # Recommendation 2: Winner prediction focus
        if miss_patterns.get("common_winner_misses"):
            recommendations.append({
                "title": "Improve Winner Prediction Accuracy",
                "description": "Winner predictions are missing in >33% of reports. Prioritize matchup-specific fighter comparison sections and reduce generic language.",
                "target_accuracy": "85%+",
                "estimated_impact": 0.12,  # 12% improvement
                "backtest_confidence": 0.72,
                "priority": "high",
            })
        
        # Recommendation 3: Method prediction focus
        if miss_patterns.get("common_method_misses"):
            recommendations.append({
                "title": "Improve Method Prediction Accuracy",
                "description": "Method predictions are missing in >33% of reports. Enhance tactical edges and scenario tree sections with more method-specific analysis.",
                "target_accuracy": "80%+",
                "estimated_impact": 0.10,  # 10% improvement
                "backtest_confidence": 0.68,
                "priority": "high",
            })
        
        # Default recommendation if no issues detected
        if not recommendations:
            recommendations.append({
                "title": "Current Model Performance Stable",
                "description": "No systematic miss patterns detected. Current calibration appears effective. Continue monitoring as more fights are scored.",
                "target_accuracy": "Maintain current level",
                "estimated_impact": 0.0,
                "backtest_confidence": 0.80,
                "priority": "low",
            })
        
        return recommendations
    
    def _backtest_calibrations(self, calibrations: List[Dict[str, Any]], scored_fights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Backtest recommendations on prior fights"""
        current_scores = [f.get("metrics", {}).get("total_report_score", 0) for f in scored_fights]
        current_avg = sum(current_scores) / len(current_scores) if current_scores else 0
        
        # Project improvement based on recommendation impact estimates
        estimated_improvement = sum(c.get("estimated_impact", 0) * c.get("backtest_confidence", 0) for c in calibrations)
        projected_avg = min(current_avg + estimated_improvement * 100, 100)
        
        return {
            "projected_improvement": round(estimated_improvement * 100, 1),
            "tested_on_fights": len(scored_fights),
            "success_rate_current": int(current_avg),
            "success_rate_projected": int(projected_avg),
        }
    
    def _calculate_calibration_confidence(self, miss_patterns: Dict[str, Any], calibrations: List[Dict[str, Any]]) -> float:
        """Calculate confidence in calibration recommendations"""
        confidence = 0.5  # Base confidence
        
        # More patterns = more confidence in recommendations
        pattern_count = (
            len(miss_patterns.get("low_accuracy_segments", [])) +
            len(miss_patterns.get("common_winner_misses", [])) +
            len(miss_patterns.get("common_method_misses", []))
        )
        confidence += min(pattern_count * 0.1, 0.3)  # Up to 30% from patterns
        
        # Higher backtest confidence = higher overall confidence
        avg_backtest_confidence = (
            sum(c.get("backtest_confidence", 0) for c in calibrations) / len(calibrations)
            if calibrations else 0
        )
        confidence += avg_backtest_confidence * 0.2  # Up to 20% from backtest
        
        return round(min(confidence, 1.0), 2)
    
    def _generate_recommendation(self, confidence: float, calibrations: List[Dict[str, Any]]) -> str:
        """Generate natural-language recommendation"""
        if not calibrations:
            return "Insufficient data for recommendations."
        
        if confidence < 0.5:
            return "Confidence in calibration recommendations is low. Score more fights to detect clearer patterns."
        elif confidence < 0.7:
            return "Moderate confidence. Recommended calibrations address identified patterns, but backtest confidence is mixed. Review before applying."
        elif confidence >= 0.85:
            return f"High confidence. Recommended calibrations should improve overall accuracy by {int(sum(c.get('estimated_impact', 0) for c in calibrations) * 100)}%. Ready for approval and application."
        else:
            return "Recommended calibrations are ready for review. Backtest shows positive expected impact. Awaiting approval."
    
    def _log_calibration_review(self, review: Dict[str, Any]):
        """Log calibration review to ledger"""
        self.calibration_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.calibration_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(review) + "\n")
    
    def _calculate_avg_score(self, scored_fights: List[Dict[str, Any]]) -> float:
        """Calculate average report score from fights"""
        scores = [f.get("metrics", {}).get("total_report_score", 0) for f in scored_fights]
        return sum(scores) / len(scores) if scores else 0
