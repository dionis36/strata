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
                fqn=node.fqn,
                type=node.node_type.value,
                file_path=node.file_path,
                methods=node.methods,
                metadata=node.metadata or {}
            )

    def add_edge(self, edge: Edge):
        """Adds a directed edge between two nodes. Creates target node if missing (Ghost Node)."""
        if edge.source_id == edge.target_id:
            return  # Reject self-loops

        if self.graph.has_node(edge.source_id):
            # Ensure target node exists (as a Ghost Node if necessary)
            if not self.graph.has_node(edge.target_id):
                target_name = edge.target_fqn.rsplit('\\', 1)[-1] if edge.target_fqn else "Unknown"
                self.graph.add_node(
                    edge.target_id,
                    name=target_name,
                    fqn=edge.target_fqn or "Unknown",
                    type=NodeType.CLASS.value,
                    is_external=True  # Mark as external component
                )

            if self.graph.has_edge(edge.source_id, edge.target_id):
                # Increment weight for duplicate calls
                self.graph[edge.source_id][edge.target_id]['weight'] += 1
            else:
                self.graph.add_edge(
                    edge.source_id, 
                    edge.target_id, 
                    type=edge.edge_type.value,
                    weight=1
                )
        
    def get_node_count(self) -> int:
        return self.graph.number_of_nodes()
        
    def get_edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_class_count(self) -> int:
        return sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == NodeType.CLASS.value)

    def get_method_count(self) -> int:
        return sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == NodeType.METHOD.value)

    def get_function_count(self) -> int:
        return sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == NodeType.FUNCTION.value)

    def get_namespace_count(self) -> int:
        return sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == NodeType.NAMESPACE.value)

    def to_json_dict(self) -> dict:
        """Serializes the graph to a JSON-compatible dictionary Deterministically."""
        data = nx.node_link_data(self.graph)
        # Sort nodes and links mathematically to guarantee deterministic JSON output
        data["nodes"] = sorted(data["nodes"], key=lambda k: k["id"])
        data["links"] = sorted(data["links"], key=lambda k: (k["source"], k["target"]))
        return data
