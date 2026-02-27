import os
import re
from typing import List, Tuple
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType

class ParserBridge:
    def __init__(self):
        # We use a string-level regex parser for Phase 1 as it requires strictly 
        # structural logic without complex dependencies
        self.class_pattern = re.compile(r'class\s+([A-Za-z0-9_]+)')
        self.method_pattern = re.compile(r'function\s+([A-Za-z0-9_]+)')
        self.call_pattern = re.compile(r'([A-Za-z0-9_]+)::[A-Za-z0-9_]+|new\s+([A-Za-z0-9_]+)')

    def parse_files(self, file_paths: List[str]) -> Tuple[List[Node], List[Edge]]:
        nodes = []
        edges = []

        for path in file_paths:
            if not os.path.exists(path):
                continue
                
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    classes_found = self.class_pattern.findall(content)
                    methods_found = self.method_pattern.findall(content)
                    calls_found = self.call_pattern.findall(content)
                    
                    for cls in classes_found:
                        node = Node(
                            id=cls,
                            name=cls,
                            node_type=NodeType.CLASS,
                            file_path=path,
                            methods=methods_found
                        )
                        nodes.append(node)
                        
                        for call_tuple in calls_found:
                            target_cls = call_tuple[0] if call_tuple[0] else call_tuple[1]
                            if target_cls and target_cls != cls:
                                edge = Edge(
                                    source_id=cls,
                                    target_id=target_cls,
                                    edge_type=EdgeType.METHOD_CALL
                                )
                                edges.append(edge)
            except Exception as e:
                # In Phase 1 we ignore individual file read errors but they won't crash the whole run
                pass
                            
        return nodes, edges

class FileScanner:
    @staticmethod
    def scan(root_path: str) -> List[str]:
        php_files = []
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith('.php'):
                    php_files.append(os.path.join(root, file))
                    
        # Phase 1 constraint: Support only 3-5 PHP files.
        return php_files[:5]
