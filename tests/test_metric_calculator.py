import pytest
import networkx as nx
from domain.services.metric_calculator import MetricCalculator

def test_metric_calculator_basic_star_topology():
    graph = nx.DiGraph()
    # Star topology: Hub (A) calls Spokes (B, C, D)
    graph.add_edges_from([('A', 'B'), ('A', 'C'), ('A', 'D')])
    
    # B also calls D
    graph.add_edge('B', 'D')
    
    # D calls A (creating a cycle and SCC)
    graph.add_edge('D', 'A')

    calculator = MetricCalculator(graph)
    metrics = calculator.calculate_all_metrics()

    # Verify A metrics
    assert metrics['A']['out_degree'] == 3
    assert metrics['A']['in_degree'] == 1
    assert metrics['A']['total_degree'] == 4

    # Verify SCC size
    # A, B, D form an SCC because A->B->D->A. 
    # C is strictly an output of A, so it's not in the main SCC.
    assert metrics['A']['scc_size'] == 3
    assert metrics['B']['scc_size'] == 3
    assert metrics['D']['scc_size'] == 3
    assert metrics['C']['scc_size'] == 1

    # Verify Blast Radius (reachability)
    # A can reach B, C, D
    assert metrics['A']['blast_radius'] == 3
    
    # C can reach nothing (0)
    assert metrics['C']['blast_radius'] == 0
    
    # B can reach D, A, C (via A)
    assert metrics['B']['blast_radius'] == 3

    # Ensure Betweenness is calculated and deterministic [0,1]
    assert 0 <= metrics['A']['betweenness'] <= 1.0
    assert 0 <= metrics['B']['betweenness'] <= 1.0
