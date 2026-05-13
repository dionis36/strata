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
            
        # --- Pass 1: Parallel Parsing & Symbol Collection ---
        chunk_size = 50
        chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]
        
        raw_results = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(self._run_php_parser, chunk) for chunk in chunks]
            for future in futures:
                raw_results.extend(future.result())

        # --- Pass 2: Global Linker & Reference Resolution ---
        all_nodes = []
        all_edges = []
        
        # Symbol Map for Resolution: Name/FQN -> NodeID
        symbol_map = {}
        added_node_ids = set()

        def add_node_safe(node):
            if node.id not in added_node_ids:
                all_nodes.append(node)
                added_node_ids.add(node.id)

        # 1. First Collect all Definitions (Files, Classes, Functions, Namespaces)
        for data in raw_results:
            path = data.get("path")
            metadata = data.get("metadata", {})
            f_id = generate_deterministic_id(path, NodeType.FILE.value)
            
            from domain.services.file_classifier import FileClassifier
            f_role = FileClassifier.classify(path, root_path)
            
            # File Node
            file_node = Node(id=f_id, name=os.path.basename(path), node_type=f_role, file_path=path, fqn=path, metadata=metadata)
            add_node_safe(file_node)
            symbol_map[path] = f_id

            # Namespaces
            for ns in metadata.get("namespaces", []):
                ns_name = ns["name"]
                ns_id = generate_deterministic_id(ns_name, NodeType.NAMESPACE.value)
                add_node_safe(Node(id=ns_id, name=ns_name, node_type=NodeType.NAMESPACE, fqn=ns_name))
                all_edges.append(Edge(source_id=f_id, target_id=ns_id, edge_type=EdgeType.DECLARES))
                symbol_map[ns_name] = ns_id

            # Classes/Interfaces/Traits
            for c_type in ["classes", "interfaces", "traits"]:
                ntype = NodeType.CLASS if c_type == "classes" else (NodeType.INTERFACE if c_type == "interfaces" else NodeType.TRAIT)
                c_data_map = metadata.get(c_type, {})
                if isinstance(c_data_map, dict):
                    for fqn, cdata in c_data_map.items():
                        c_id = generate_deterministic_id(fqn, ntype.value)
                        add_node_safe(Node(
                            id=c_id, name=cdata["name"], node_type=ntype, fqn=fqn, file_path=path, metadata=cdata
                        ))
                        all_edges.append(Edge(source_id=f_id, target_id=c_id, edge_type=EdgeType.DECLARES))
                        symbol_map[fqn] = c_id
                        
                        # Methods inside classes
                        methods = cdata.get("methods", [])
                        if isinstance(methods, list):
                            for mdata in methods:
                                m_fqn = f"{fqn}::{mdata['name']}"
                                m_id = generate_deterministic_id(m_fqn, NodeType.METHOD.value)
                                add_node_safe(Node(id=m_id, name=mdata["name"], node_type=NodeType.METHOD, fqn=m_fqn, file_path=path))
                                all_edges.append(Edge(source_id=c_id, target_id=m_id, edge_type=EdgeType.DECLARES))
                                symbol_map[m_fqn] = m_id

            # Standalone Functions
            f_data_map = metadata.get("functions", {})
            if isinstance(f_data_map, dict):
                for f_fqn, fdata in f_data_map.items():
                    func_id = generate_deterministic_id(f_fqn, NodeType.FUNCTION.value)
                    add_node_safe(Node(id=func_id, name=fdata["name"], node_type=NodeType.FUNCTION, fqn=f_fqn, file_path=path))
                    all_edges.append(Edge(source_id=f_id, target_id=func_id, edge_type=EdgeType.DECLARES))
                    symbol_map[f_fqn] = func_id

        # 2. Second Pass: Resolve References & Calls
        for data in raw_results:
            path = data.get("path")
            metadata = data.get("metadata", {})
            f_id = symbol_map.get(path)
            
            # Globals
            for glob in metadata.get("globals", []):
                g_name = f"global::{glob['name']}"
                g_id = generate_deterministic_id(g_name, NodeType.GLOBAL_VAR.value)
                add_node_safe(Node(id=g_id, name=glob['name'], node_type=NodeType.GLOBAL_VAR, fqn=g_name))
                all_edges.append(Edge(source_id=f_id, target_id=g_id, edge_type=EdgeType.DEPENDS_ON))

            # Includes
            for inc in metadata.get("includes", []):
                if inc.get("path"):
                    abs_target = os.path.normpath(os.path.join(os.path.dirname(path), inc["path"]))
                    if abs_target in symbol_map:
                        all_edges.append(Edge(source_id=f_id, target_id=symbol_map[abs_target], edge_type=EdgeType.DEPENDS_ON))

            # Calls (The Core Linker)
            for call in metadata.get("calls", []):
                source_id = f_id
                if call.get("source"):
                    # Check if source class exists in map
                    source_id = symbol_map.get(call["source"], f_id)
                
                target_fqn = call.get("class") or call.get("method")
                if target_fqn and target_fqn in symbol_map:
                    all_edges.append(Edge(source_id=source_id, target_id=symbol_map[target_fqn], edge_type=EdgeType.CALLS))
        
        return all_nodes, all_edges

    def _run_php_parser(self, chunk: List[str]) -> List[dict]:
        results = []
        sidecar_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "php", "parser.php"))
        try:
            paths_input = "\n".join(chunk) + "\n"
            result = subprocess.run(["php", sidecar_path], input=paths_input, capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        if data.get("status") == "success":
                            results.append(data)
                    except: continue
        except Exception as e:
            logger.error(f"PHP Bridge Chunk Error: {e}")
        return results

class FileScanner:
    @staticmethod
    def scan(path: str) -> List[str]:
        target_extensions = (
            ".php", ".htaccess", ".sql", ".inc", 
            ".css", ".js", 
            ".json", ".xml", ".yml", ".yaml", 
            ".tpl", ".twig", ".blade.php"
        )
        
        discovered_files = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.lower().endswith(target_extensions):
                    discovered_files.append(os.path.join(root, file))
        return discovered_files
