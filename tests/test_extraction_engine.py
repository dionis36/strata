import pytest
import networkx as nx
from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType, ImpactMetrics
from domain.extraction.cluster_builder import ClusterBuilder
from domain.extraction.cluster_scorer import ClusterScorer
from domain.extraction.conflict_resolver import ConflictResolver
from domain.simulation.graph_simulator import GraphSimulator
from domain.simulation.impact_analyzer import ImpactAnalyzer
from domain.models.node import NodeType

@pytest.fixture
def mock_graph():
    G = nx.DiGraph()
    nodes = ["A", "B", "C", "D", "E"]
    for n in nodes:
        G.add_node(n, type=NodeType.CLASS.value)
        
    # SCC: A -> B -> C -> A
    G.add_edge("A", "B", type="CALLS")
    G.add_edge("B", "C", type="CALLS")
    G.add_edge("C", "A", type="CALLS")
    
    # External connection: C -> D -> E
    G.add_edge("C", "D", type="CALLS")
    G.add_edge("D", "E", type="CALLS")
    
    return G

def test_cluster_builder_scc(mock_graph):
    builder = ClusterBuilder(mock_graph)
    sccs = builder.build_scc_clusters()
    
    assert len(sccs) == 1
    assert set(sccs[0].nodes) == {"A", "B", "C"}
    assert sccs[0].type == ExtractionUnitType.CLUSTER

def test_cluster_scorer_and_conflict_resolver(mock_graph):
    builder = ClusterBuilder(mock_graph)
    scorer = ClusterScorer(mock_graph)
    
    candidates = builder.build_all_candidate_clusters()
    for c in candidates:
        scorer.score_cluster(c)
        
    resolver = ConflictResolver(mock_graph)
    units = resolver.resolve(candidates)
    
    # Ensure all nodes are present in exactly one unit
    all_nodes_in_units = set()
    for u in units:
        all_nodes_in_units.update(u.nodes)
        
    assert all_nodes_in_units == set(mock_graph.nodes())

def test_graph_simulator(mock_graph):
    unit = ExtractionUnit(
        label="TestModule",
        type=ExtractionUnitType.CLUSTER,
        nodes=["A", "B", "C"]
    )
    
    simulator = GraphSimulator(mock_graph)
    g_sim = simulator.simulate_extraction(unit)
    
    assert "A" not in g_sim
    assert "B" not in g_sim
    assert "C" not in g_sim
    
    proxy = "TestModule_Service"
    assert proxy in g_sim
    
    # Original C -> D edge should re-route to proxy -> D
    assert g_sim.has_edge(proxy, "D")
    
    # Network interface complexity of the proxy should be 1 outgoing
    assert g_sim.out_degree(proxy) == 1
    assert g_sim.in_degree(proxy) == 0

def test_impact_analyzer(mock_graph):
    unit = ExtractionUnit(
        label="TestModule",
        type=ExtractionUnitType.CLUSTER,
        nodes=["A", "B", "C"]
    )
    simulator = GraphSimulator(mock_graph)
    g_sim = simulator.simulate_extraction(unit)
    
    original_risk = {"A": 0.1, "B": 0.2, "C": 0.3, "D": 0.4, "E": 0.0}
    analyzer = ImpactAnalyzer(mock_graph, original_risk)
    impact = analyzer.analyze(unit, g_sim)
    
    assert impact.dependency_breaks == 1  # C -> D broke
    assert impact.interface_complexity == 1  # 1 edge crossing boundary
    assert impact.data_isolation_difficulty == 0  # no tables involved
