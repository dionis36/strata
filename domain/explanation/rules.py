"""
Phase 4.5: Explanation Rule Set
Single source of truth for all explainability rules.

Design rules:
- All threshold values live in THRESHOLDS dict only — never hardcoded inside lambdas.
- Each rule's 'condition' receives the full component_data dict.
- 'message_template' uses {value:.2f} placeholders rendered at evaluation time.
- 'weight' controls ranking; explanations are sorted DESC by weight before cap is applied.
"""

# ── Configurable Thresholds ──────────────────────────────────────────────────
THRESHOLDS = {
    # Structural
    "criticality_high":       0.70,
    "criticality_moderate":   0.40,
    "instability_high":       0.60,
    "coupling_high":          0.60,
    # Behavioral
    "write_intensity_high":   0.50,
    "table_deps_multi":       3,
    # Combined
    "behavioral_factor_notable": 0.30,
}

# ── Rule Set ─────────────────────────────────────────────────────────────────
RULES = [
    {
        "name": "high_criticality",
        "category": "structural",
        "condition": lambda x: x.get("criticality_index", 0.0) > THRESHOLDS["criticality_high"],
        "severity": "high",
        "weight": 0.95,
        "message_template": (
            "Central dependency hub (criticality {criticality_index:.2f}) with high propagation impact "
            "(blast radius {blast_radius:.0f} components)"
        ),
    },
    {
        "name": "cycle_risk",
        "category": "structural",
        "condition": lambda x: x.get("cycle_flag", 0) == 1,
        "severity": "high",
        "weight": 0.90,
        "message_template": (
            "Participates in cyclic dependency group (SCC size {scc_size}) — "
            "changes cascade unpredictably within the cycle"
        ),
    },
    {
        "name": "moderate_criticality",
        "category": "structural",
        "condition": lambda x: (
            THRESHOLDS["criticality_moderate"] < x.get("criticality_index", 0.0)
            <= THRESHOLDS["criticality_high"]
        ),
        "severity": "medium",
        "weight": 0.60,
        "message_template": (
            "Moderate structural centrality (criticality {criticality_index:.2f}) — "
            "sits on several dependency paths"
        ),
    },
    {
        "name": "high_instability",
        "category": "structural",
        "condition": lambda x: x.get("instability", 0.0) > THRESHOLDS["instability_high"],
        "severity": "medium",
        "weight": 0.70,
        "message_template": (
            "High outward dependency ratio (instability {instability:.2f}) — "
            "sensitive to changes in its dependencies"
        ),
    },
    {
        "name": "high_coupling",
        "category": "structural",
        "condition": lambda x: x.get("coupling_pressure", 0.0) > THRESHOLDS["coupling_high"],
        "severity": "medium",
        "weight": 0.65,
        "message_template": (
            "High coupling pressure ({coupling_pressure:.2f}) — "
            "strong bidirectional dependency concentration"
        ),
    },
    {
        "name": "data_mutation_heavy",
        "category": "behavioral",
        "condition": lambda x: x.get("write_intensity", 0.0) > THRESHOLDS["write_intensity_high"],
        "severity": "medium",
        "weight": 0.75,
        "message_template": (
            "Frequent database write activity (intensity {write_intensity:.2f}) — "
            "mutations increase state-change blast radius"
        ),
    },
    {
        "name": "multi_table_dependency",
        "category": "behavioral",
        "condition": lambda x: x.get("table_dependencies", 0) >= THRESHOLDS["table_deps_multi"],
        "severity": "medium",
        "weight": 0.70,
        "message_template": (
            "Writes to {table_dependencies} shared database tables — "
            "broad data coupling increases coordination risk"
        ),
    },
    {
        "name": "behavioral_amplification",
        "category": "combined",
        "condition": lambda x: x.get("behavioral_factor", 0.0) > THRESHOLDS["behavioral_factor_notable"],
        "severity": "medium",
        "weight": 0.80,
        "message_template": (
            "Behavioral activity amplifies structural risk "
            "(factor {behavioral_factor:.2f} → final risk {final_risk:.2f})"
        ),
    },
]
