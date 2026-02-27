import pytest
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType
from domain.models.graph_model import GraphModel

def test_graph_model_creation():
    graph = GraphModel()
    
    node1 = Node(id="ClassA", name="ClassA", node_type=NodeType.CLASS, methods=["method1"])
    node2 = Node(id="ClassB", name="ClassB", node_type=NodeType.CLASS, methods=["method2"])
    
    edge = Edge(source_id="ClassA", target_id="ClassB", edge_type=EdgeType.METHOD_CALL)
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge(edge)
    
    assert graph.get_node_count() == 2
    assert graph.get_class_count() == 2
    assert graph.get_edge_count() == 1
    
    json_data = graph.to_json_dict()
    assert "nodes" in json_data
    assert "links" in json_data
    assert len(json_data["nodes"]) == 2
    assert len(json_data["links"]) == 1
