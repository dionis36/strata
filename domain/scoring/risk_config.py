"""
Phase 3: Risk Model Configuration
Config-driven weights and thresholds — overridable by Phase 6 ablation studies.
"""

# Default risk model weights (must sum to 1.0)
RISK_WEIGHTS = {
    "criticality": 0.35,   # betweenness × blast_radius — chokepoint signal
    "instability": 0.25,   # out / (in + out) — change sensitivity
    "coupling":    0.20,   # normalized in + out — integration density
    "cycle":       0.20,   # binary: participates in circular dependency
}

# Risk classification thresholds (lower bound inclusive)
RISK_THRESHOLDS = {
    "CRITICAL": 0.75,
    "HIGH":     0.50,
    "MEDIUM":   0.25,
    "LOW":      0.0,
}
