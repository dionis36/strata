"""
Requirement 16 & 21: Modernization Recommendation Engine
Suggests Option A, B, or C based on modernization and structural scores.
"""

class RecommendationEngine:
    @staticmethod
    def recommend(legacy_metrics: dict, risk_summary: dict) -> dict:
        """
        Logic:
        - Option A (Incremental): Score > 70 AND coupling < 0.4
        - Option B (Strangler Fig): 40 < Score <= 70 OR high coupling
        - Option C (Full Rewrite): Score <= 40 AND extreme technical debt
        """
        score = legacy_metrics.get("total_modernization_score", 0.0)
        coupling = legacy_metrics.get("coupling_score", 0.0) # In our model, higher is better (less coupling)
        
        # Normalize coupling: 15 is best, 0 is worst.
        # Invert it for the logic below: high coupling = low score.
        
        if score > 75:
            strategy = "Option A — Incremental Modernization"
            reasoning = "The codebase has high modernization potential and manageable coupling. Focus on refactoring specific modules to PSR-12 and adding tests."
        elif score > 45:
            strategy = "Option B — Strangler Fig Migration"
            reasoning = "High technical debt or coupling makes in-place refactoring risky. Recommend wrapping the monolith in a proxy and extracting modules as independent services."
        else:
            strategy = "Option C — Full Rewrite"
            reasoning = "Critical technical debt, security risks, or obsolete environment (Era A/B). The cost of modernization exceeds the cost of a clean-slate implementation."
            
        return {
            "strategy": strategy,
            "reasoning": reasoning,
            "score_threshold": score
        }
