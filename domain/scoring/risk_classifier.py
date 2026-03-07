"""
Phase 3: Risk Classifier
Converts a numeric risk_score ∈ [0, 1] into a categorical risk level.
Thresholds are config-driven to support experimentation in Phase 6.
"""
from domain.scoring.risk_config import RISK_THRESHOLDS


class RiskClassifier:
    """Maps a float risk score to a human-readable risk level string."""

    def __init__(self, threshold_overrides: dict = None):
        self.thresholds = dict(RISK_THRESHOLDS)
        if threshold_overrides:
            self.thresholds.update(threshold_overrides)

    def classify(self, score: float) -> str:
        """
        Args:
            score: float in [0, 1]

        Returns:
            One of: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        """
        if score >= self.thresholds["CRITICAL"]:
            return "CRITICAL"
        if score >= self.thresholds["HIGH"]:
            return "HIGH"
        if score >= self.thresholds["MEDIUM"]:
            return "MEDIUM"
        return "LOW"
