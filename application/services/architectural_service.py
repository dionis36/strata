from typing import List, Dict, Any
from domain.models.node import Node, NodeType

class ArchitecturalService:
    """
    Phase 4 Service: Automatically identifies architectural roles in the monolith.
    Uses structural patterns and behavioral side-effects.
    """

    def __init__(self, graph_model: Any):
        self.graph_model = graph_model

    def identify_roles(self) -> Dict[str, str]:
        """
        Analyzes every class and assigns a role.
        Returns: {node_id: role_name}
        """
        roles = {}
        for node_id, data in self.graph_model.graph.nodes(data=True):
            if data.get('type') != NodeType.CLASS.value:
                continue

            role = self._classify_node(node_id, data)
            roles[node_id] = role
        return roles

    def _classify_node(self, node_id: str, data: Dict[str, Any]) -> str:
        fqn = data.get('fqn', '').lower()
        methods = data.get('methods_data', []) # We'll need to update graph persistence to include this
        
        # 1. Heuristic: Namespace/Name match
        if 'controller' in fqn or 'action' in fqn:
            return 'Controller'
        if 'repository' in fqn or 'dao' in fqn:
            return 'Repository'
        if 'service' in fqn or 'manager' in fqn:
            return 'Service'
        if 'entity' in fqn or 'model' in fqn or 'dto' in fqn:
            return 'DataModel'

        # 2. Behavioral side-effect match
        has_db = any('DB' in m.get('side_effects', []) for m in methods)
        has_net = any('NET' in m.get('side_effects', []) for m in methods)
        
        if has_db and not has_net:
            return 'Repository'
        if has_db and has_net:
            return 'Service (External Integration)'
        
        return 'Component'
