import time
import pytest
import networkx as nx
from domain.services.metric_calculator import MetricCalculator, MAX_NODES_FOR_BETWEENNESS

def test_performance_ceiling_200_nodes():
    """Phase E: Prove that MetricCalculator completes within 5 seconds
    on a 200-node, 1000-edge synthetic random graph.

    This establishes the SLA for the structural intelligence engine.
    """
    # Build a deterministic random graph for reproducibility
    G = nx.gnm_random_graph(200, 1000, seed=42, directed=True)
    assert G.number_of_nodes() == 200

    start = time.monotonic()
    calculator = MetricCalculator(G)
    results = calculator.calculate_all_metrics()
    elapsed = time.monotonic() - start

    print(f"\n[Performance] 200-node graph completed in {elapsed:.3f}s")

    # All nodes must have entries
    assert len(results) == 200

    # Assert within 5-second SLA
    assert elapsed < 5.0, (
        f"Performance ceiling exceeded: {elapsed:.2f}s > 5.0s SLA. "
        "Consider reducing MAX_NODES_FOR_BETWEENNESS or optimizing."
    )


def test_timeout_guard_triggers():
    """Verify that the timeout guard raises RuntimeError when the computation
    takes longer than the allowed timeout."""
    from unittest.mock import patch
    import time

    G = nx.complete_graph(5, create_using=nx.DiGraph())
    calculator = MetricCalculator(G)

    # Monkeypatch _compute to sleep for 3s, triggering a 1s timeout
    def slow_compute():
        time.sleep(3)
        return {}

    with patch.object(calculator, '_compute', side_effect=slow_compute):
        with pytest.raises(RuntimeError, match="timeout"):
            calculator.calculate_all_metrics(timeout=1)


def test_betweenness_skipped_for_large_graph():
    """Graph exceeding MAX_NODES_FOR_BETWEENNESS should get -1.0 betweenness."""
    # Build a graph with MAX + 1 nodes but minimal edges
    n = MAX_NODES_FOR_BETWEENNESS + 1
    G = nx.path_graph(n, create_using=nx.DiGraph())
    calculator = MetricCalculator(G)
    results = calculator._compute()

    # All betweenness values should be -1.0 (skipped)
    for node_id, metrics in results.items():
        assert metrics['betweenness'] == -1.0, (
            f"Expected -1.0 betweenness for oversized graph, got {metrics['betweenness']}"
        )
