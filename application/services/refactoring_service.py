import json
import subprocess
import os
from typing import Optional, Dict, Any

class PHPTransformer:
    """Manages the PHP transformation subprocess."""
    
    def __init__(self, script_path: str = "infrastructure/php/transformer.php"):
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
                bufsize=1
            )

    def stop(self):
        if self._process:
            self._process.terminate()
            self._process = None

    def transform(self, command: Dict[str, Any]) -> Dict[str, Any]:
        self.start()
        if not self._process or not self._process.stdin:
            return {"status": "error", "message": "PHP Transformer not started"}
        
        self._process.stdin.write(json.dumps(command) + "\n")
        self._process.stdin.flush()
        
        line = self._process.stdout.readline()
        if not line:
            return {"status": "error", "message": "No output from PHP Transformer"}
        
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return {"status": "error", "message": f"Invalid JSON response: {line}"}

class RefactoringService:
    def __init__(self, output_root: str = "/data/refactored"):
        self.transformer = PHPTransformer()
        self.output_root = output_root


    def extract_class(self, file_path: str, class_name: str, new_namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Surgically extracts a class and immediately validates the result.
        """
        command = {
            "action": "EXTRACT_CLASS",
            "file_path": file_path,
            "target": class_name,
            "new_namespace": new_namespace
        }
        
        result = self.transformer.transform(command)
        
        if result.get("status") == "success":
            sub_dir = new_namespace.replace("\\", "/") if new_namespace else "extracted"
            target_dir = os.path.join(self.output_root, sub_dir)
            os.makedirs(target_dir, exist_ok=True)
            
            target_file = os.path.join(target_dir, f"{class_name}.php")
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(result["code"])
            
            # --- Module A.3: Safety Validation ---
            validation = self.validate_extraction(target_dir)
            
            return {
                "status": "success",
                "extracted_file": target_file,
                "class_name": class_name,
                "namespace": new_namespace,
                "safety_check": validation
            }
        
        return result

    def validate_extraction(self, directory: str) -> Dict[str, Any]:
        """
        Runs a micro-analysis on the refactored directory to ensure structural integrity.
        """
        from application.services.analysis_service import AnalysisService
        from infrastructure.persistence.database import SessionLocal
        
        # We use a temporary analysis run to validate the code
        db = SessionLocal()
        try:
            # We bypass full persistence for validation to keep it fast
            analysis = AnalysisService(db)
            # 1. Scan and Parse the new directory
            from infrastructure.parser_bridge import FileScanner
            files = FileScanner.scan(directory)
            nodes, edges = analysis.parser.parse_files(files, root_path=directory)
            
            # 2. Build temporary graph
            from domain.models.graph_model import GraphModel
            graph = GraphModel()
            for n in nodes: graph.add_node(n)
            for e in edges: graph.add_edge(e)
            
            # 3. Check for Cycles (The ultimate safety check)
            import networkx as nx
            cycles = list(nx.simple_cycles(graph.graph))
            
            return {
                "status": "passed" if not cycles else "warning",
                "cycle_count": len(cycles),
                "file_count": len(files),
                "is_safe": len(cycles) == 0
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
