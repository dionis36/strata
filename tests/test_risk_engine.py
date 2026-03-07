"""
Phase 3: Risk Engine Unit Tests
Validates all 6 exit criteria before tagging v0.4-risk-framework.
"""
from domain.scoring.feature_normalizer import FeatureNormalizer
from domain.scoring.structural_features import engineer_features
from domain.scoring.risk_model import RiskModel
from domain.scoring.risk_classifier import RiskClassifier


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_metrics(n=5):
    """Create a synthetic list of component metrics for testing."""
    return [
        {"component_name": "ClassA", "component_type": "class",
         "betweenness": 0.9, "blast_radius": 10, "in_degree": 0, "out_degree": 5, "scc_size": 1},
        {"component_name": "ClassB", "component_type": "class",
         "betweenness": 0.5, "blast_radius": 5,  "in_degree": 2, "out_degree": 2, "scc_size": 2},
        {"component_name": "ClassC", "component_type": "class",
         "betweenness": 0.1, "blast_radius": 2,  "in_degree": 3, "out_degree": 1, "scc_size": 1},
        {"component_name": "ClassD", "component_type": "class",
         "betweenness": 0.0, "blast_radius": 0,  "in_degree": 0, "out_degree": 0, "scc_size": 1},
        {"component_name": "ClassE", "component_type": "class",
         "betweenness": 0.8, "blast_radius": 8,  "in_degree": 1, "out_degree": 4, "scc_size": 3},
    ]


def _compute_risk_for_metrics(metrics, weight_overrides=None):
    """Helper: run the full pipeline, return list of (name, risk_score, risk_level)."""
    normalizer = FeatureNormalizer().fit(metrics)
    model = RiskModel(weight_overrides=weight_overrides)
    classifier = RiskClassifier()
    results = []
    for m in metrics:
        norm = normalizer.normalize(m)
        features = engineer_features(norm, m)
        score = model.score(features)
        level = classifier.classify(score)
        results.append({"name": m["component_name"], "risk_score": score, "risk_level": level})
    return results


# ── Exit Criterion 1: Risk ∈ [0, 1] ──────────────────────────────────────────

def test_risk_score_bounds():
    """Exit criterion 1: All risk scores must be in [0.0, 1.0]."""
    metrics = _make_metrics()
    results = _compute_risk_for_metrics(metrics)
    for r in results:
        assert 0.0 <= r["risk_score"] <= 1.0, (
            f"{r['name']}: risk_score={r['risk_score']} is out of bounds [0, 1]"
        )


# ── Exit Criterion 2: Determinism ────────────────────────────────────────────

def test_risk_determinism():
    """Exit criterion 2: Running the same metrics produces identical scores every time."""
    metrics = _make_metrics()
    results_a = _compute_risk_for_metrics(metrics)
    results_b = _compute_risk_for_metrics(metrics)
    for a, b in zip(results_a, results_b):
        assert a["risk_score"] == b["risk_score"], (
            f"{a['name']}: non-deterministic score: {a['risk_score']} != {b['risk_score']}"
        )


# ── Exit Criterion 3: High-risk matches graph intuition ──────────────────────

def test_high_risk_components_match_intuition():
    """Exit criterion 3: ClassA (high betweenness+blast_radius) must outrank ClassD (isolated)."""
    metrics = _make_metrics()
    results = {r["name"]: r["risk_score"] for r in _compute_risk_for_metrics(metrics)}
    assert results["ClassA"] > results["ClassD"], (
        f"ClassA (central+high blast) should be riskier than ClassD (isolated): "
        f"ClassA={results['ClassA']}, ClassD={results['ClassD']}"
    )


# ── Exit Criterion 4: Weight override changes scores (Phase 6 readiness) ─────

def test_weight_override_changes_scores():
    """Exit criterion 4: Passing weight_overrides changes scores without crashing."""
    metrics = _make_metrics()
    default_results = _compute_risk_for_metrics(metrics)
    # Heavily weight cycle — ClassE (scc_size=3) and ClassB (scc_size=2) should dominate
    cycle_heavy = {"criticality": 0.10, "instability": 0.10, "coupling": 0.10, "cycle": 0.70}
    overridden_results = _compute_risk_for_metrics(metrics, weight_overrides=cycle_heavy)

    default_scores = {r["name"]: r["risk_score"] for r in default_results}
    override_scores = {r["name"]: r["risk_score"] for r in overridden_results}

    # Scores must be valid
    for r in overridden_results:
        assert 0.0 <= r["risk_score"] <= 1.0

    # At least one score must differ (override must have an effect)
    diffs = [abs(default_scores[n] - override_scores[n]) for n in default_scores]
    assert max(diffs) > 0.0, "Weight override produced no change in any score"


# ── Exit Criterion 5: cycle_flag set for scc_size > 1 ────────────────────────

def test_cycle_flag_set_for_scc_gt_1():
    """Exit criterion 5: Components with scc_size > 1 must have cycle_flag = 1."""
    metrics = _make_metrics()
    normalizer = FeatureNormalizer().fit(metrics)
    for m in metrics:
        norm = normalizer.normalize(m)
        features = engineer_features(norm, m)
        expected_flag = 1 if m["scc_size"] > 1 else 0
        assert features["cycle_flag"] == expected_flag, (
            f"{m['component_name']}: scc_size={m['scc_size']} "
            f"but cycle_flag={features['cycle_flag']} (expected {expected_flag})"
        )


# ── Exit Criterion 6: Degenerate graph (all-zero) doesn't crash ──────────────

def test_normalizer_handles_all_zero_run():
    """Exit criterion 6: Normalizer must not raise ZeroDivisionError on degenerate graphs."""
    all_zero = [
        {"component_name": f"Class{i}", "component_type": "class",
         "betweenness": 0.0, "blast_radius": 0, "in_degree": 0, "out_degree": 0, "scc_size": 1}
        for i in range(3)
    ]
    results = _compute_risk_for_metrics(all_zero)
    for r in results:
        assert r["risk_score"] == 0.0, (
            f"All-zero graph component should have risk_score=0.0, got {r['risk_score']}"
        )
        assert r["risk_level"] == "LOW"
