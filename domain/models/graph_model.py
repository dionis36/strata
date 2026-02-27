import networkx as nx
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType

class GraphModel:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node: Node):
        """Adds a node to the graph if it doesn't exist."""
        if not self.graph.has_node(node.id):
            self.graph.add_node(
                node.id, 
                name=node.name, 
                type=node.node_type.value,
                file_path=node.file_path,
                methods=node.methods
            )

    def add_edge(self, edge: Edge):
        """Adds a directed edge between two nodes only if both exist."""
        if self.graph.has_node(edge.source_id) and self.graph.has_node(edge.target_id):
            self.graph.add_edge(
                edge.source_id, 
                edge.target_id, 
                type=edge.edge_type.value
            )
        
    def get_node_count(self) -> int:
        return self.graph.number_of_nodes()
        
    def get_edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_class_count(self) -> int:
        return sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == NodeType.CLASS.value)

    def to_json_dict(self) -> dict:
        """Serializes the graph to a JSON-compatible dictionary."""
        return nx.node_link_data(self.graph)
