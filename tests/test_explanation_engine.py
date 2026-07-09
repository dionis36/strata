"""
Phase 4.5: Explanation Engine Unit Tests
Validates the RiskReasoner, rule correctness, and EvidenceBuilder.
"""
from domain.explanation.reasoner import RiskReasoner, MAX_EXPLANATIONS
from domain.explanation.rules import RULES, THRESHOLDS
from domain.explanation.evidence_builder import EvidenceBuilder


# ── Fixture Data ──────────────────────────────────────────────────────────────

CRITICAL_COMPONENT = {
    "criticality_index": 0.85,
    "instability": 0.70,
    "cycle_flag": 1,
    "scc_size": 4,
    "blast_radius": 0.80,
    "coupling_pressure": 0.65,
    "write_intensity": 0.60,
    "table_dependencies": 5,
    "behavioral_factor": 0.50,
    "final_risk": 0.95,
}

ZERO_RISK_COMPONENT = {
    "criticality_index": 0.0,
    "instability": 0.0,
    "cycle_flag": 0,
    "scc_size": 1,
    "blast_radius": 0.0,
    "coupling_pressure": 0.0,
    "write_intensity": 0.0,
    "table_dependencies": 0,
    "behavioral_factor": 0.0,
    "final_risk": 0.0,
}

MOCK_GRAPH = {
    "nodes": [
        {"id": "TargetClass", "type": "class", "file_path": "app/TargetClass.php", "scc_id": 2},
        {"id": "CallerA",     "type": "class", "file_path": "app/CallerA.php",     "scc_id": 2},
        {"id": "CallerB",     "type": "class", "file_path": "app/CallerB.php",     "scc_id": 1},
    ],
    "links": [
        {"source": "CallerA", "target": "TargetClass", "type": "method_call"},
        {"source": "CallerB", "target": "TargetClass", "type": "instantiation"},
    ]
}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_rule_engine_fires_correctly():
    """High-risk component must trigger high_criticality and cycle_risk at minimum."""
    reasoner = RiskReasoner()
    results = reasoner.explain(CRITICAL_COMPONENT)
    types = {r.type for r in results}
    assert "high_criticality" in types, "Expected high_criticality rule to fire"
    assert "cycle_risk" in types, "Expected cycle_risk rule to fire"


def test_no_high_explanations_for_zero_risk():
    """A component with all-zero metrics must not trigger any high-severity rules."""
    reasoner = RiskReasoner()
    results = reasoner.explain(ZERO_RISK_COMPONENT)
    high_ones = [r for r in results if r.severity == "high"]
    assert len(high_ones) == 0, f"Expected no high-severity explanations, got: {high_ones}"


def test_explanation_count_capped_at_max():
    """Even if all 8 rules fire, the output is capped at MAX_EXPLANATIONS (5)."""
    reasoner = RiskReasoner()
    results = reasoner.explain(CRITICAL_COMPONENT)
    assert len(results) <= MAX_EXPLANATIONS, (
        f"Expected max {MAX_EXPLANATIONS} explanations, got {len(results)}"
    )


def test_explanations_sorted_by_weight_desc():
    """Explanations must come out ordered by weight descending."""
    reasoner = RiskReasoner()
    results = reasoner.explain(CRITICAL_COMPONENT)
    weights = [r.weight for r in results]
    assert weights == sorted(weights, reverse=True), (
        f"Explanations not sorted by weight: {weights}"
    )


def test_template_substitution():
    """Message templates must interpolate metric values correctly."""
    reasoner = RiskReasoner()
    results = reasoner.explain(CRITICAL_COMPONENT)
    for r in results:
        assert "{" not in r.message, (
            f"Unrendered template placeholder found in: '{r.message}'"
        )


def test_determinism():
    """Same input must produce identical output across multiple calls."""
    reasoner = RiskReasoner()
    result1 = reasoner.explain(CRITICAL_COMPONENT)
    result2 = reasoner.explain(CRITICAL_COMPONENT)
    result3 = reasoner.explain(CRITICAL_COMPONENT)
    assert result1 == result2 == result3, "Explanation engine is not deterministic"


def test_evidence_builder_extracts_dependents():
    """EvidenceBuilder must correctly identify components with edges pointing TO the target."""
    evidence = EvidenceBuilder.build("TargetClass", CRITICAL_COMPONENT, MOCK_GRAPH)
    dependents = evidence["graph"]["dependent_components"]
    assert "CallerA" in dependents, "Expected CallerA in dependents"
    assert "CallerB" in dependents, "Expected CallerB in dependents"
    assert "TargetClass" not in dependents, "Target must not appear as its own dependent"


def test_evidence_builder_extracts_file_path():
    """EvidenceBuilder must extract the file path from the graph node."""
    evidence = EvidenceBuilder.build("TargetClass", CRITICAL_COMPONENT, MOCK_GRAPH)
    assert evidence["code"]["file_path"] == "app/TargetClass.php"


def test_evidence_builder_handles_missing_graph():
    """EvidenceBuilder must return clean empty evidence when graph is None."""
    evidence = EvidenceBuilder.build("AnyClass", ZERO_RISK_COMPONENT, None)
    assert evidence["graph"]["dependent_components"] == []
    assert evidence["code"]["file_path"] is None


if __name__ == "__main__":
    test_rule_engine_fires_correctly()
    test_no_high_explanations_for_zero_risk()
    test_explanation_count_capped_at_max()
    test_explanations_sorted_by_weight_desc()
    test_template_substitution()
    test_determinism()
    test_evidence_builder_extracts_dependents()
    test_evidence_builder_extracts_file_path()
    test_evidence_builder_handles_missing_graph()
    print("\n All Phase 4.5 Explanation Engine tests passed!")
