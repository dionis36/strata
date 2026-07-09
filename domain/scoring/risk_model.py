"""
Phase 3: Risk Composition Model
Combines 4 derived structural indicators into a single risk score ∈ [0, 1].
Weights are config-driven to support Phase 6 ablation experiments.
"""
from domain.scoring.risk_config import RISK_WEIGHTS


class RiskModel:
    """Weighted linear composition of structural indicators.

    Accepts optional weight overrides (for Phase 6 experiments).
    """

    def __init__(self, weight_overrides: dict = None):
        self.weights = dict(RISK_WEIGHTS)  # copy defaults
        if weight_overrides:
            self.weights.update(weight_overrides)

    def score(self, features: dict) -> float:
        """Compute a risk score from derived structural features.

        Args:
            features: Dict from structural_features.engineer_features().

        Returns:
            float in [0.0, 1.0]
        """
        base_risk = (
            self.weights["criticality"] * features.get("criticality_index", 0.0)
            + self.weights["instability"] * features.get("instability", 0.0)
            + self.weights["coupling"]    * features.get("coupling_pressure", 0.0)
            + self.weights["cycle"]       * float(features.get("cycle_flag", 0))
        )
        # Clamp to [0, 1] - cycle_flag can push sum above 1 on very coupled nodes
        return round(min(1.0, max(0.0, base_risk)), 6)
