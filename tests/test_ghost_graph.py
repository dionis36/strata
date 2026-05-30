import os
import json
import pytest
from application.services.simulation_service import SimulationService
from domain.models.node import NodeType
from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import ComponentRisk, GraphNode, GraphEdge

def test_get_ghost_graph_fallback(tmp_path):
    # Create a mock graph JSON file for fallback test
    graph_data = {
        "nodes": [
            {"id": "ClassOne", "name": "ClassOne", "fqn": "ClassOne", "type": "class", "file_path": "/app/src/ClassOne.php"},
            {"id": "ClassOne::methodOne", "name": "methodOne", "fqn": "ClassOne::methodOne", "type": "method", "file_path": "/app/src/ClassOne.php"},
            {"id": "ClassTwo", "name": "ClassTwo", "fqn": "ClassTwo", "type": "class", "file_path": "/app/src/ClassTwo.php"},
            {"id": "users_table", "name": "users_table", "fqn": "users_table", "type": "table"}
        ],
        "links": [
            {"source": "ClassOne", "target": "ClassOne::methodOne", "type": "DECLARES"},
            {"source": "ClassOne::methodOne", "target": "ClassTwo", "type": "CALLS"},
            {"source": "ClassTwo", "target": "users_table", "type": "WRITES_TO"}
        ]
    }
    
    data_dir = str(tmp_path)
    graph_file = os.path.join(data_dir, "graph_999.json")
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(graph_data, f)
        
    db = SessionLocal()
    try:
        db.query(ComponentRisk).filter(ComponentRisk.run_id == 999).delete()
        db.query(GraphNode).filter(GraphNode.run_id == 999).delete()
        db.query(GraphEdge).filter(GraphEdge.run_id == 999).delete()
        
        r1 = ComponentRisk(run_id=999, component_name="ClassOne", risk_score=0.1, risk_level="Low", final_risk=0.1, behavioral_factor=0.0, criticality_index=0.0, instability=0.0, cycle_flag=False, coupling_pressure=0.0)
        r2 = ComponentRisk(run_id=999, component_name="ClassTwo", risk_score=0.2, risk_level="Low", final_risk=0.2, behavioral_factor=0.0, criticality_index=0.0, instability=0.0, cycle_flag=False, coupling_pressure=0.0)
        db.add_all([r1, r2])
        db.commit()
    finally:
        db.close()
        
    service = SimulationService(data_dir=data_dir)
    res = service.get_ghost_graph(999, "/app/src/ClassOne.php")
    
    assert "error" not in res
    assert res["target"] == "/app/src/ClassOne.php"
    assert res["proxy_node"] == "ClassOne_Service"
    
    node_ids = {n["id"] for n in res["nodes"]}
    assert "ClassOne_Service" in node_ids
    assert "ClassTwo" in node_ids
    assert "ClassOne" not in node_ids

def test_get_ghost_graph_relational():
    # Test loading directly from database GraphNode and GraphEdge tables
    db = SessionLocal()
    try:
        db.query(ComponentRisk).filter(ComponentRisk.run_id == 888).delete()
        db.query(GraphNode).filter(GraphNode.run_id == 888).delete()
        db.query(GraphEdge).filter(GraphEdge.run_id == 888).delete()
        
        # Risk components
        r1 = ComponentRisk(run_id=888, component_name="ClassOne", risk_score=0.1, risk_level="Low", final_risk=0.1, behavioral_factor=0.0, criticality_index=0.0, instability=0.0, cycle_flag=False, coupling_pressure=0.0)
        r2 = ComponentRisk(run_id=888, component_name="ClassTwo", risk_score=0.2, risk_level="Low", final_risk=0.2, behavioral_factor=0.0, criticality_index=0.0, instability=0.0, cycle_flag=False, coupling_pressure=0.0)
        db.add_all([r1, r2])
        
        # Nodes
        n1 = GraphNode(id="ClassOne", run_id=888, name="ClassOne", fqn="ClassOne", node_type="class", file_path="/app/src/ClassOne.php", metadata_json="{}")
        n2 = GraphNode(id="ClassOne::methodOne", run_id=888, name="methodOne", fqn="ClassOne::methodOne", node_type="method", file_path="/app/src/ClassOne.php", metadata_json="{}")
        n3 = GraphNode(id="ClassTwo", run_id=888, name="ClassTwo", fqn="ClassTwo", node_type="class", file_path="/app/src/ClassTwo.php", metadata_json="{}")
        db.add_all([n1, n2, n3])
        
        # Edges
        e1 = GraphEdge(run_id=888, source_id="ClassOne", target_id="ClassOne::methodOne", edge_type="DECLARES")
        e2 = GraphEdge(run_id=888, source_id="ClassOne::methodOne", target_id="ClassTwo", edge_type="CALLS")
        db.add_all([e1, e2])
        
        db.commit()
    finally:
        db.close()
        
    service = SimulationService()
    res = service.get_ghost_graph(888, "/app/src/ClassOne.php")
    
    assert "error" not in res
    assert res["proxy_node"] == "ClassOne_Service"
    
    node_ids = {n["id"] for n in res["nodes"]}
    assert "ClassOne_Service" in node_ids
    assert "ClassTwo" in node_ids
    assert "ClassOne" not in node_ids
    
    # Assert there is no json file created for 888 (verifying it read purely from DB)
    assert not os.path.exists(f"/data/graph_888.json")


def test_query_graph_relations():
    from fastapi.testclient import TestClient
    from api.main import app
    
    # We populate the database for run 777
    db = SessionLocal()
    try:
        db.query(GraphNode).filter(GraphNode.run_id == 777).delete()
        db.query(GraphEdge).filter(GraphEdge.run_id == 777).delete()
        
        n1 = GraphNode(id="NodeA", run_id=777, name="NodeA", fqn="NodeA", node_type="class", namespace="App\\Services", file_path="/app/A.php", metadata_json="{}")
        n2 = GraphNode(id="NodeB", run_id=777, name="NodeB", fqn="NodeB", node_type="method", namespace="App\\Services", file_path="/app/A.php", metadata_json="{}")
        n3 = GraphNode(id="NodeC", run_id=777, name="NodeC", fqn="NodeC", node_type="table", namespace="", file_path=None, metadata_json="{}")
        db.add_all([n1, n2, n3])
        
        e1 = GraphEdge(run_id=777, source_id="NodeA", target_id="NodeB", edge_type="DECLARES")
        e2 = GraphEdge(run_id=777, source_id="NodeB", target_id="NodeC", edge_type="CALLS")
        db.add_all([e1, e2])
        
        db.commit()
    finally:
        db.close()
        
    client = TestClient(app)
    
    # Test query without filters
    response = client.get("/analysis/query-graph/777")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2
    
    # Test filtering by type
    response = client.get("/analysis/query-graph/777?node_type=class")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["id"] == "NodeA"
    
    # Test filtering by namespace
    response = client.get("/analysis/query-graph/777?namespace=App%5CServices")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert {n["id"] for n in data["nodes"]} == {"NodeA", "NodeB"}
