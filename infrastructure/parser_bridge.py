import json
import subprocess
import os
import logging
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType
from domain.utils.id_generator import generate_deterministic_id

logger = logging.getLogger(__name__)

class ParserBridge:
    def __init__(self, db_session):
        self.db = db_session

    def parse_files(self, file_paths: List[str], root_path: str) -> Tuple[List[Node], List[Edge]]:
        if not file_paths:
            return [], []
        chunk_size = 50
        chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]
        all_nodes = []
        all_edges = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(self._parse_chunk, chunk, root_path) for chunk in chunks]
            for future in futures:
                nodes, edges = future.result()
                all_nodes.extend(nodes)
                all_edges.extend(edges)
        return all_nodes, all_edges

    def _parse_chunk(self, chunk: List[str], root_path: str) -> Tuple[List[Node], List[Edge]]:
        nodes: List[Node] = []
        edges: List[Edge] = []
        sidecar_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "php", "parser.php"))
        try:
            paths_input = "\n".join(chunk) + "\n"
            result = subprocess.run(["php", sidecar_path], input=paths_input, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"DEBUG: PHP Error: {result.stderr}")
                return [], []
            
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    if data.get("status") != "success": continue
                    path = data.get("path")
                    metadata = data.get("metadata", {})
                    
                    f_id = generate_deterministic_id(path, NodeType.FILE.value)
                    nodes.append(Node(id=f_id, name=os.path.basename(path), node_type=NodeType.FILE, file_path=path, fqn=path, metadata=metadata))
                    
                    # To prevent duplicate sink nodes in the list, we track them for this file
                    added_sinks = set()
                    
                    # Side Effects & Requirements
                    for effect_data in metadata.get("file_side_effects", []):
                        sink_name = f"sink::{effect_data['type']}"
                        s_id = generate_deterministic_id(sink_name, NodeType.UNKNOWN.value)
                        if s_id not in added_sinks:
                            nodes.append(Node(id=s_id, name=sink_name, node_type=NodeType.UNKNOWN, fqn=sink_name, file_path=path))
                            added_sinks.add(s_id)
                        edges.append(Edge(source_id=f_id, target_id=s_id, edge_type=EdgeType.DEPENDS_ON, target_fqn=sink_name))
                    
                    for req in metadata.get("requirements", []):
                        sink_name = f"sink::{req['type']}"
                        s_id = generate_deterministic_id(sink_name, NodeType.UNKNOWN.value)
                        if s_id not in added_sinks:
                            nodes.append(Node(id=s_id, name=sink_name, node_type=NodeType.UNKNOWN, fqn=sink_name, file_path=path))
                            added_sinks.add(s_id)
                        edges.append(Edge(source_id=f_id, target_id=s_id, edge_type=EdgeType.DEPENDS_ON, target_fqn=sink_name))

                    # Classes
                    classes = metadata.get("classes", {})
                    for fqn, cdata in classes.items():
                        c_id = generate_deterministic_id(fqn, NodeType.CLASS.value)
                        nodes.append(Node(
                            id=c_id, 
                            name=cdata["name"], 
                            node_type=NodeType.CLASS, 
                            namespace=fqn.rsplit("\\", 1)[0] if "\\" in fqn else None, 
                            fqn=fqn, 
                            file_path=path, # Critical for caching
                            metadata=cdata
                        ))
                        edges.append(Edge(source_id=f_id, target_id=c_id, edge_type=EdgeType.CONTAINS))
                        for method in cdata.get("methods", []):
                            for effect in method.get("side_effects", []):
                                sink_name = f"sink::{effect}"
                                s_id = generate_deterministic_id(sink_name, NodeType.UNKNOWN.value)
                                if s_id not in added_sinks:
                                    nodes.append(Node(id=s_id, name=sink_name, node_type=NodeType.UNKNOWN, fqn=sink_name, file_path=path))
                                    added_sinks.add(s_id)
                                edges.append(Edge(source_id=c_id, target_id=s_id, edge_type=EdgeType.DEPENDS_ON, target_fqn=sink_name))

                    # Globals (Requirement 3C)
                    for glob in metadata.get("globals", []):
                        g_name = f"global::{glob['name']}"
                        # Append the type if it's a mutation so we can tell the difference in reachability
                        if glob.get("type") == "mutation":
                            g_name += " (Mutated)"
                        
                        g_id = generate_deterministic_id(g_name, NodeType.UNKNOWN.value)
                        if g_id not in added_sinks:
                            nodes.append(Node(id=g_id, name=g_name, node_type=NodeType.UNKNOWN, fqn=g_name, file_path=path))
                            added_sinks.add(g_id)
                        edges.append(Edge(source_id=f_id, target_id=g_id, edge_type=EdgeType.DEPENDS_ON, target_fqn=g_name))

                    # Includes
                    for inc in metadata.get("includes", []):
                        if inc.get("path"):
                            abs_target = os.path.abspath(os.path.join(os.path.dirname(path), inc["path"]))
                            t_id = generate_deterministic_id(abs_target, NodeType.FILE.value)
                            edges.append(Edge(source_id=f_id, target_id=t_id, edge_type=EdgeType.DEPENDS_ON, target_fqn=abs_target))

                except Exception as e:
                    print(f"DEBUG: Parse error on line: {e}")
            print(f"DEBUG: Chunk processed. Nodes: {len(nodes)}, Edges: {len(edges)}")
        except Exception as e:
            print(f"DEBUG: Bridge fatal error: {e}")
        return nodes, edges

class FileScanner:
    @staticmethod
    def scan(path: str) -> List[str]:
        php_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".php"):
                    php_files.append(os.path.join(root, file))
                elif file == ".htaccess":
                    php_files.append(os.path.join(root, file))
        return php_files
