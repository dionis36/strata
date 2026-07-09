"""
Phase 4.5: Explanation Domain Models
Pydantic contracts for the output of the Rule-Based Explanation Engine.
"""
from pydantic import BaseModel
from typing import List


class ExplanationItem(BaseModel):
    """A single rule-triggered explanation for a component's risk."""
    type: str          # Rule name, e.g. 'high_criticality'
    category: str      # 'structural' | 'behavioral' | 'combined'
    severity: str      # 'high' | 'medium' | 'low'
    weight: float      # 0.0-1.0 for ranking; higher = more important
    message: str       # Human-readable, value-interpolated explanation sentence


class ComponentExplanation(BaseModel):
    """Full explainability payload for a single component."""
    component_name: str
    risk_level: str        # LOW / MEDIUM / HIGH / CRITICAL
    final_risk: float      # Phase 4 amplified risk [0.0, 1.0]
    explanations: List[ExplanationItem]  # Sorted by weight DESC, max 5
    evidence: dict         # Metrics + graph dependents + source file path
