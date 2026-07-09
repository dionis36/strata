"""
Requirement 16 & 21: Modernization Decision Engine
Automatically recommends Option A (Incremental), Option B (Strangler Fig), or Option C (Rewrite)
based on the multi-dimensional Modernization Score.
"""

class RecommendationEngine:
    @staticmethod
    def recommend(score: float, metrics: dict) -> dict:
        if score >= 70:
            strategy = "Option A Incremental"
            description = "The architecture is relatively modern. Safely decouple modules in-place and upgrade framework versions."
            icon = ""
        elif score >= 40:
            strategy = "Option B Strangler Fig"
            description = "Mixed legacy state. Build an API facade around the monolith and extract bounded contexts one by one."
            icon = ""
        else:
            strategy = "Option C Full Rewrite"
            description = "High technical debt and tight coupling. Freeze new features, maintain security, and rebuild the core domain."
            icon = ""
            
        # Refine recommendation based on specific technical profile
        risks = []
        if metrics.get("db_layer") == "Mixed (Raw SQL & Abstraction)":
            risks.append("Prioritize isolating DB access behind a Repository pattern before extraction.")
        if metrics.get("auth_layer") == "Legacy (Session-based / Homemade)":
            risks.append("First extraction target: Standardize Authentication to JWT/OAuth2 to decouple session state.")
            
        return {
            "strategy": strategy,
            "description": description,
            # "icon": icon,
            "tactical_advice": risks
        }
