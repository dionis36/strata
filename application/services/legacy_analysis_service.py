"""
Phase 2 & 3: Legacy Analysis Service
Orchestrates specialized legacy metrics extraction (Eras, Modernization Scores).
"""

import logging
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import LegacyRepository, AnalysisRunRepository
from domain.decision.era_classifier import EraClassifier
from domain.scoring.modernization_model import ModernizationModel
from domain.decision.framework_fingerprinter import FrameworkFingerprinter
from domain.decision.tech_stack_profiler import TechStackProfiler

logger = logging.getLogger(__name__)

class LegacyAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LegacyRepository(db)

    def analyze_legacy_environment(self, run_id: int, nodes: list, edges: list) -> dict:
        """
        Extracts high-level legacy environment insights from a completed run.
        """
        from infrastructure.persistence.models import AnalysisRun, Project
        
        # 1. Fetch root_path for dependency intelligence (composer.json parsing)
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        project = self.db.query(Project).filter(Project.id == run.project_id).first() if run else None
        root_path = project.root_path if project else None
        
        # 2. Aggregate signals for Era/Score calculation
        stats = self._aggregate_signals(nodes, edges)
        
        # 3. Framework Fingerprinting (Requirement 9) - Now parses composer.json
        framework = FrameworkFingerprinter.detect(nodes, edges, root_path)
        
        # 3. Deep Technical Profiling (Requirement 10-13)
        tech_profile = TechStackProfiler.profile(nodes, edges)
        
        # 4. Classify Era (Requirement 1)
        php_era = EraClassifier.classify(nodes, edges, stats)
        
        # 5. Calculate Modernization Scores (Requirement 8)
        scores = ModernizationModel.calculate(stats)
        
        # 6. Hosting Risk Level (Requirement 15)
        hosting_risk = "low"
        if stats.get("hosting_sink_count", 0) > 5 or stats.get("has_htaccess"):
            hosting_risk = "high"
        elif stats.get("hosting_sink_count", 0) > 0:
            hosting_risk = "medium"

        # 7. Persistence
        metrics = {
            "php_era": php_era,
            "detected_framework": framework,
            "hosting_risk_level": hosting_risk,
            **tech_profile,
            **scores
        }
        
        self.repo.save_legacy_metrics(run_id, metrics)
        logger.info(f"Legacy metrics saved for run {run_id}: Era={php_era}, Framework={framework}, DB={tech_profile['db_layer']}")
        
        return metrics

    def _aggregate_signals(self, nodes: list, edges: list) -> dict:
        """Helper to boil down graph nodes/edges into signal inputs."""
        class_nodes = [n for n in nodes if n.get('node_type') == 'class' or n.get('node_type') == 'NodeType.CLASS']
        
        total_classes = len(class_nodes)
        namespaced_classes = sum(1 for n in class_nodes if n.get('namespace'))
        
        # Check for legacy DB sinks and Dangerous patterns from metadata
        legacy_db_ratio = 0.0
        danger_count = 0
        hosting_sink_count = 0
        
        # Recursive helper to find all values of a specific key
        def find_keys(obj, key):
            if isinstance(obj, dict):
                if key in obj:
                    yield obj[key]
                for k, v in obj.items():
                    yield from find_keys(v, key)
            elif isinstance(obj, list):
                for item in obj:
                    yield from find_keys(item, key)

        for n in nodes:
            meta = n.get('metadata', {})
            
            for t in find_keys(meta, 'type'):
                if t == 'MYSQL_LEGACY':
                    legacy_db_ratio = 1.0
                elif t == 'DB' and legacy_db_ratio == 0.0:
                    legacy_db_ratio = 0.5
                elif t == 'DANGER':
                    danger_count += 1
                elif t == 'HOSTING':
                    hosting_sink_count += 1
                    
            for se_list in find_keys(meta, 'side_effects'):
                if isinstance(se_list, list):
                    for st in se_list:
                        if st == 'DB' and legacy_db_ratio == 0.0:
                            legacy_db_ratio = 0.5
                        elif st == 'DANGER':
                            danger_count += 1
                        elif st == 'HOSTING':
                            hosting_sink_count += 1
        
        file_types = {"file", "entry_point", "bootstrap", "controller", "view", "config", "job", "model"}
        
        # Helper to check if a node type represents a file
        def is_file_node(n):
            nt = n.get('node_type') or n.get('type') or ''
            if not isinstance(nt, str):
                nt = getattr(nt, 'value', str(nt))
            nt = nt.replace("NodeType.", "").lower()
            return nt in file_types

        # Check for composer/htaccess
        has_htaccess = any(n.get('name') == '.htaccess' for n in nodes if is_file_node(n))
        has_composer = any(n.get('name') == 'composer.json' for n in nodes if is_file_node(n) or (n.get('name') or '').lower() == 'composer.json')
        
        # PHP files only for structural calculations
        php_files = [n for n in nodes if is_file_node(n) and n.get('name', '').lower().endswith(('.php', '.phtml', '.inc'))]
        total_php_files = len(php_files)
        
        # Procedural ratio based on AST metadata within files
        procedural_files = 0
        for n in php_files:
            meta = n.get('metadata', {})
            has_oop = (
                meta.get('classes') or 
                meta.get('interfaces') or 
                meta.get('traits')
            )
            if not has_oop:
                procedural_files += 1
                
        procedural_ratio = procedural_files / total_php_files if total_php_files > 0 else 0.0

        # Heuristic for has_tests: Check if any PHP file contains "test" or "phpunit" in name or path
        has_tests = any(
            'test' in n.get('name', '').lower() or 
            (n.get('file_path') and 'test' in n.get('file_path', '').lower()) or
            'phpunit' in n.get('name', '').lower()
            for n in nodes if is_file_node(n)
        )

        return {
            "namespace_ratio": namespaced_classes / total_classes if total_classes > 0 else 0.0,
            "legacy_db_ratio": legacy_db_ratio,
            "uses_mysql_legacy": legacy_db_ratio > 0.5,
            "procedural_ratio": procedural_ratio,
            "security_risk_count": danger_count,
            "hosting_sink_count": hosting_sink_count,
            "has_htaccess": has_htaccess,
            "coupling_density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0,
            "has_composer": has_composer,
            "has_tests": has_tests
        }
