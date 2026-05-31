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
        method_map = {} # bare_method_name -> [node_id, ...]
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
                        
                        # Methods inside classes
                        methods = cdata.get("methods", [])
                        method_names = []
                        if isinstance(methods, list):
                            for mdata in methods:
                                method_names.append(mdata["name"])
                                m_fqn = f"{fqn}::{mdata['name']}"
                                m_id = generate_deterministic_id(m_fqn, NodeType.METHOD.value)
                                add_node_safe(Node(id=m_id, name=mdata["name"], node_type=NodeType.METHOD, fqn=m_fqn, file_path=path))
                                all_edges.append(Edge(source_id=c_id, target_id=m_id, edge_type=EdgeType.DECLARES))
                                symbol_map[m_fqn.lower()] = m_id
                                
                                m_name = mdata["name"].lower()
                                if m_name not in method_map:
                                    method_map[m_name] = []
                                method_map[m_name].append(m_id)

                        add_node_safe(Node(
                            id=c_id, name=cdata["name"], node_type=ntype, fqn=fqn, file_path=path, metadata=cdata, methods=method_names
                        ))
                        all_edges.append(Edge(source_id=f_id, target_id=c_id, edge_type=EdgeType.DECLARES))
                        symbol_map[fqn.lower()] = c_id

            # Inheritance & Abstraction mapping
            for c_type in ["classes", "interfaces"]:
                c_map = metadata.get(c_type, {})
                if isinstance(c_map, dict):
                    for fqn, cdata in c_map.items():
                        c_id = symbol_map.get(fqn.lower())
                        if not c_id: continue
                        
                        extends = cdata.get("extends")
                        if extends:
                            if isinstance(extends, list):
                                for ext in extends:
                                    ext_id = symbol_map.get(ext.lower())
                                    if ext_id: all_edges.append(Edge(source_id=c_id, target_id=ext_id, edge_type=EdgeType.INHERITS))
                            else:
                                ext_id = symbol_map.get(extends.lower())
                                if ext_id: all_edges.append(Edge(source_id=c_id, target_id=ext_id, edge_type=EdgeType.INHERITS))
                                
                        if c_type == "classes":
                            implements = cdata.get("implements", [])
                            for imp in implements:
                                imp_id = symbol_map.get(imp.lower())
                                if imp_id: all_edges.append(Edge(source_id=c_id, target_id=imp_id, edge_type=EdgeType.INHERITS))

            # Standalone Functions
            f_data_map = metadata.get("functions", {})
            if isinstance(f_data_map, dict):
                for f_fqn, fdata in f_data_map.items():
                    func_id = generate_deterministic_id(f_fqn, NodeType.FUNCTION.value)
                    add_node_safe(Node(id=func_id, name=fdata["name"], node_type=NodeType.FUNCTION, fqn=f_fqn, file_path=path))
                    all_edges.append(Edge(source_id=f_id, target_id=func_id, edge_type=EdgeType.DECLARES))
                    symbol_map[f_fqn.lower()] = func_id

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
                
                # Link global to its source (Method, Function, or File)
                source_id = f_id
                if glob.get("sourceMethod") and glob.get("sourceClass"):
                    m_fqn = f"{glob['sourceClass']}::{glob['sourceMethod']}"
                    source_id = symbol_map.get(m_fqn, f_id)
                elif glob.get("sourceFunction"):
                    source_id = symbol_map.get(glob["sourceFunction"], f_id)
                
                all_edges.append(Edge(source_id=source_id, target_id=g_id, edge_type=EdgeType.DEPENDS_ON))

            # Includes
            for inc in metadata.get("includes", []):
                if inc.get("path"):
                    target_id = None
                    if inc.get("type") == "jf_import":
                        # jf_import 'jf/model/core' -> find file path ending in jf/model/core.php
                        p = inc["path"].replace("/", os.sep).lower()
                        for f_path in symbol_map:
                            if f_path.lower().endswith(f"{p}.php"):
                                target_id = symbol_map[f_path]
                                break
                    else:
                        abs_target = os.path.normpath(os.path.join(os.path.dirname(path), inc["path"]))
                        target_id = symbol_map.get(abs_target)

                    if target_id:
                        all_edges.append(Edge(source_id=f_id, target_id=target_id, edge_type=EdgeType.DEPENDS_ON))

            # Calls (The Core Linker)
            for call in metadata.get("calls", []):
                # Identify source of the call
                source_id = f_id
                source_class_id = None
                if call.get("sourceMethod") and call.get("source"):
                    m_fqn = f"{call['source']}::{call['sourceMethod']}".lower()
                    source_id = symbol_map.get(m_fqn, f_id)
                    source_class_id = symbol_map.get(call["source"].lower())
                elif call.get("sourceFunction"):
                    source_id = symbol_map.get(call["sourceFunction"].lower(), f_id)
                elif call.get("source"):
                    source_class_id = symbol_map.get(call["source"].lower())
                
                # Resolve target
                call_type = call.get("type", "method_call")

                # Helper to add edge for source_id and source_class_id
                def add_edge_safe(target_node_id, edge_type):
                    all_edges.append(Edge(source_id=source_id, target_id=target_node_id, edge_type=edge_type))
                    if source_class_id and source_class_id != source_id:
                        all_edges.append(Edge(source_id=source_class_id, target_id=target_node_id, edge_type=edge_type))
                
                if call_type == "method_call":
                    # Fuzzy match for dynamic method calls (Era 2/3 logic)
                    f_name = call.get("method", "").lower()
                    if f_name in method_map and f_name != "__construct":
                        # Add an edge to the first 5 potential matches to prevent graph explosion
                        # while still capturing the structural dependency
                        for target_m_id in method_map[f_name][:5]:
                            add_edge_safe(target_m_id, EdgeType.CALLS)
                            
                elif call_type == "static_call":
                    c_name = call.get("class", "").lower()
                    m_name = call.get("method", "").lower()
                    target_fqn = f"{c_name}::{m_name}"
                    if target_fqn in symbol_map:
                        add_edge_safe(symbol_map[target_fqn], EdgeType.STATIC_CALL)
                    elif c_name in symbol_map:
                        add_edge_safe(symbol_map[c_name], EdgeType.STATIC_CALL)
                    else:
                        orig_c = call.get("class")
                        if orig_c:
                            target_id = generate_deterministic_id(orig_c, NodeType.CLASS.value)
                            add_edge_safe(target_id, EdgeType.STATIC_CALL)
                        
                elif call_type == "instantiation":
                    c_name = call.get("class", "").lower()
                    if c_name in symbol_map:
                        add_edge_safe(symbol_map[c_name], EdgeType.INSTANTIATES)
                    else:
                        orig_c = call.get("class")
                        if orig_c:
                            target_id = generate_deterministic_id(orig_c, NodeType.CLASS.value)
                            add_edge_safe(target_id, EdgeType.INSTANTIATES)
                            
                elif call_type == "injection":
                    c_name = call.get("class", "").lower()
                    if c_name in symbol_map:
                        add_edge_safe(symbol_map[c_name], EdgeType.INJECTS)
                    else:
                        orig_c = call.get("class")
                        if orig_c:
                            target_id = generate_deterministic_id(orig_c, NodeType.CLASS.value)
                            add_edge_safe(target_id, EdgeType.INJECTS)
                
                else:
                    # Fallback for generic calls
                    target_fqn = (call.get("class") or call.get("method", "")).lower()
                    if target_fqn and target_fqn in symbol_map:
                        add_edge_safe(symbol_map[target_fqn], EdgeType.CALLS)
                    elif not call.get("class") and call.get("method"):
                        f_name = call["method"].lower()
                        if f_name in symbol_map:
                            add_edge_safe(symbol_map[f_name], EdgeType.CALLS)
        
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
