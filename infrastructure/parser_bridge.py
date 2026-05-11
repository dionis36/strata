
import os
import re
import json
import subprocess
from typing import List, Tuple, Optional, Dict, Any
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType

# ... (regex patterns remain for fallback if needed, but we will focus on AST)

class PHPRuntime:
    """Manages the PHP subprocess for AST extraction."""
    
    def __init__(self, script_path: str = "infrastructure/php/parser.php"):
        self.script_path = script_path
        self._process: Optional[subprocess.Popen] = None

    def start(self):
        if self._process is None:
            self._process = subprocess.Popen(
                ["php", self.script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

    def stop(self):
        if self._process:
            self._process.terminate()
            self._process = None

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        self.start()
        if not self._process or not self._process.stdin:
            return {"status": "error", "message": "PHP process not started"}
        
        self._process.stdin.write(f"{file_path}\n")
        self._process.stdin.flush()
        
        line = self._process.stdout.readline()
        if not line:
            return {"status": "error", "message": "No output from PHP process"}
        
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return {"status": "error", "message": f"Invalid JSON: {line}"}

def _qualify(name: str, namespace: Optional[str], file_path: str, root_path: str) -> str:
    """Build a fully-qualified, collision-resistant node ID.

    Priority order:
      1. If the raw name already contains a backslash it is already qualified.
      2. If a namespace was declared, use Namespace\\ClassName.
      3. Fallback: relative_dir/ClassName using the file path relative to root.
    """
    name = name.strip()
    if '\\' in name:
        return name  # already fully qualified
    if namespace:
        return f"{namespace}\\{name}"
    # Fallback: use directory relative to root as namespace-like prefix
    rel = os.path.relpath(os.path.dirname(file_path), root_path)
    if rel == '.':
        return name
    return rel.replace(os.sep, '\\') + '\\' + name


class ParserBridge:
    """Parses PHP source files into typed Nodes and Edges.

    Phase A upgrade:
      - Namespace-aware fully-qualified IDs (collision-proof).
      - Typed edges: INHERITS, IMPLEMENTS, USES_TRAIT, INSTANTIATION, METHOD_CALL.
    """

    def parse_files(
        self,
        file_paths: List[str],
        root_path: str = '/data'
    ) -> Tuple[List[Node], List[Edge]]:

        nodes: List[Node] = []
        edges: List[Edge] = []
        runtime = PHPRuntime()
        from domain.utils.id_generator import generate_deterministic_id
        
        try:
            for path in file_paths:
                if not os.path.exists(path):
                    continue
                
                result = runtime.parse_file(path)
                if result.get("status") != "success":
                    continue
                
                metadata = result.get("metadata", {})
                
                # --- Process Classes ---
                classes = metadata.get("classes", {})
                if isinstance(classes, list): classes = {}
                for fqn, data in classes.items():
                    node_id = generate_deterministic_id(fqn, NodeType.CLASS.value)
                    node = Node(
                        id=node_id,
                        name=data["name"],
                        fqn=fqn,
                        namespace=fqn.rsplit('\\', 1)[0] if '\\' in fqn else None,
                        node_type=NodeType.CLASS,
                        file_path=path,
                        methods=[m["name"] for m in data.get("methods", [])]
                    )
                    nodes.append(node)
                    
                    # INHERITS edges
                    if data.get("extends"):
                        target_fqn = data["extends"]
                        edges.append(Edge(
                            source_id=node_id,
                            target_id=generate_deterministic_id(target_fqn, NodeType.CLASS.value),
                            edge_type=EdgeType.INHERITS
                        ))
                    
                    # IMPLEMENTS edges
                    for iface in data.get("implements", []):
                        edges.append(Edge(
                            source_id=node_id,
                            target_id=generate_deterministic_id(iface, NodeType.CLASS.value),
                            edge_type=EdgeType.INHERITS # SCS: inherits covers implements
                        ))

                # --- Process Calls (Edges) ---
                for call in metadata.get("calls", []):
                    source_fqn = call.get("source")
                    if not source_fqn:
                        continue
                        
                    source_node_id = generate_deterministic_id(source_fqn, NodeType.CLASS.value)
                    target_id = None
                    edge_type = None
                    
                    if call["type"] == "static_call" or call["type"] == "instantiation":
                        target_fqn = call.get("class")
                        target_id = generate_deterministic_id(target_fqn, NodeType.CLASS.value)
                        edge_type = EdgeType.CALLS if call["type"] == "static_call" else EdgeType.CALLS # SCS: calls covers both
                    
                    if target_id and edge_type:
                        edges.append(Edge(
                            source_id=source_node_id,
                            target_id=target_id,
                            edge_type=edge_type
                        ))

        finally:
            runtime.stop()

        return nodes, edges


class FileScanner:
    @staticmethod
    def scan(root_path: str, max_files: Optional[int] = None) -> List[str]:
        """Walk `root_path` and collect PHP files.

        Args:
            root_path: Directory to scan.
            max_files: Optional cap on number of files returned.
                       None means no limit (Phase A+).
        """
        php_files = []
        for root, _, files in os.walk(root_path):
            for file in sorted(files):   # sorted = deterministic ordering
                if file.endswith('.php'):
                    php_files.append(os.path.join(root, file))

        if max_files is not None:
            return php_files[:max_files]
        return php_files

