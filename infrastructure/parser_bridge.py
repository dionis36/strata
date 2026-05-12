import os
import json
import subprocess
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType

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
        
        try:
            self._process.stdin.write(f"{file_path}\n")
            self._process.stdin.flush()
            
            line = self._process.stdout.readline()
            if not line:
                # Check for errors in stderr
                stderr = self._process.stderr.read()
                return {"status": "error", "message": f"No output from PHP process. Stderr: {stderr}"}
            
            return json.loads(line)
        except BrokenPipeError:
            return {"status": "error", "message": "Broken Pipe: PHP process crashed."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ParserBridge:
    """Parses PHP source files into typed Nodes and Edges in parallel."""


    def _parse_chunk(self, file_paths: List[str], root_path: str) -> Tuple[List[Node], List[Edge]]:
        """Worker function to parse a chunk of files using a dedicated PHP runtime."""
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
                
                # --- Process File Node ---
                file_id = generate_deterministic_id(path, NodeType.FILE.value)
                nodes.append(Node(
                    id=file_id,
                    name=os.path.basename(path),
                    fqn=path,
                    node_type=NodeType.FILE,
                    file_path=path
                ))

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
                    
                    # File -> Class (Declares)
                    edges.append(Edge(
                        source_id=file_id,
                        target_id=node_id,
                        edge_type=EdgeType.DECLARES
                    ))

                    if data.get("extends"):
                        target_fqn = data["extends"]
                        edges.append(Edge(
                            source_id=node_id,
                            target_id=generate_deterministic_id(target_fqn, NodeType.CLASS.value),
                            edge_type=EdgeType.INHERITS,
                            target_fqn=target_fqn
                        ))
                    
                    for iface in data.get("implements", []):
                        edges.append(Edge(
                            source_id=node_id,
                            target_id=generate_deterministic_id(iface, NodeType.CLASS.value),
                            edge_type=EdgeType.INHERITS,
                            target_fqn=iface
                        ))

                # --- Process Includes (Requirement 3B) ---
                for inc in metadata.get("includes", []):
                    inc_path = inc.get("path")
                    if not inc_path: continue
                    
                    # Attempt simple resolution for relative includes
                    abs_inc_path = inc_path
                    if not os.path.isabs(inc_path):
                        abs_inc_path = os.path.normpath(os.path.join(os.path.dirname(path), inc_path))
                    
                    target_file_id = generate_deterministic_id(abs_inc_path, NodeType.FILE.value)
                    
                    # Determine source (Class or File)
                    source_id = file_id
                    if inc.get("source_class"):
                        source_id = generate_deterministic_id(inc["source_class"], NodeType.CLASS.value)
                    
                    edges.append(Edge(
                        source_id=source_id,
                        target_id=target_file_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        target_fqn=abs_inc_path
                    ))

                # --- Process Globals (Requirement 3C) ---
                for glob in metadata.get("globals", []):
                    var_name = glob.get("name")
                    if not var_name: continue
                    
                    global_node_id = generate_deterministic_id(var_name, NodeType.GLOBAL_VAR.value)
                    
                    source_id = file_id
                    if glob.get("source_class"):
                        source_id = generate_deterministic_id(glob["source_class"], NodeType.CLASS.value)
                    
                    edges.append(Edge(
                        source_id=source_id,
                        target_id=global_node_id,
                        edge_type=EdgeType.READS_FROM,
                        target_fqn=var_name
                    ))

                # --- Process Config/Constants (Requirement 14) ---
                for const in metadata.get("constants", []):
                    const_name = const.get("name")
                    if not const_name: continue
                    
                    const_node_id = generate_deterministic_id(const_name, NodeType.GLOBAL_VAR.value)
                    
                    source_id = file_id
                    if const.get("source_class"):
                        source_id = generate_deterministic_id(const["source_class"], NodeType.CLASS.value)
                    
                    # File/Class -> Constant (Writes/Defines)
                    edges.append(Edge(
                        source_id=source_id,
                        target_id=const_node_id,
                        edge_type=EdgeType.WRITES_TO,
                        target_fqn=const_name
                    ))

                # --- Process Calls (Edges) ---
                for call in metadata.get("calls", []):
                    source_fqn = call.get("source")
                    if not source_fqn:
                        # Procedural call? Use file as source
                        source_node_id = file_id
                    else:
                        source_node_id = generate_deterministic_id(source_fqn, NodeType.CLASS.value)
                        
                    target_id = None
                    edge_type = None
                    target_fqn = None
                    
                    if call["type"] == "static_call" or call["type"] == "instantiation":
                        target_fqn = call.get("class")
                        target_id = generate_deterministic_id(target_fqn, NodeType.CLASS.value)
                        edge_type = EdgeType.CALLS
                    
                    if target_id and edge_type:
                        edges.append(Edge(
                            source_id=source_node_id,
                            target_id=target_id,
                            edge_type=edge_type,
                            target_fqn=target_fqn
                        ))
                
                # --- Process Side Effects (Requirement 6, 11, 13) ---
                for fqn, data in classes.items():
                    class_node_id = generate_deterministic_id(fqn, NodeType.CLASS.value)
                    for method in data.get("methods", []):
                        for effect in method.get("side_effects", []):
                            # Create a virtual node for the sink type
                            sink_id = f"sink::{effect}"
                            edges.append(Edge(
                                source_id=class_node_id,
                                target_id=generate_deterministic_id(sink_id, NodeType.UNKNOWN.value),
                                edge_type=EdgeType.DEPENDS_ON,
                                target_fqn=sink_id
                            ))
                            
        finally:
            runtime.stop()
            
        return nodes, edges


    def parse_files(
        self,
        file_paths: List[str],
        root_path: str = '/data',
        workers: int = None
    ) -> Tuple[List[Node], List[Edge]]:

        if workers is None:
            workers = os.cpu_count() or 4
        
        # Divide files into chunks
        chunk_size = max(1, len(file_paths) // workers)
        chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]
        
        all_nodes: List[Node] = []
        all_edges: List[Edge] = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self._parse_chunk, chunk, root_path) for chunk in chunks]
            
            for future in as_completed(futures):
                nodes, edges = future.result()
                all_nodes.extend(nodes)
                all_edges.extend(edges)
                
        return all_nodes, all_edges

class FileScanner:
    @staticmethod
    def scan(root_path: str, max_files: Optional[int] = None) -> List[str]:
        php_files = []
        for root, _, files in os.walk(root_path):
            for file in sorted(files):
                if file.endswith('.php'):
                    php_files.append(os.path.join(root, file))

        if max_files is not None:
            return php_files[:max_files]
        return php_files
