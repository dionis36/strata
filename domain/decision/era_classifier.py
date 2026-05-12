"""
Requirement 1: Era Classification
Determines if a project is Era A (Procedural), B (Custom MVC), C (Namespaced), or D (Modern).
"""

from typing import List, Dict

class EraClassifier:
    @staticmethod
    def classify(nodes: List[Dict], edges: List[Dict], metadata_summary: Dict) -> str:
        """
        Heuristically determines the PHP Era based on structural signals.
        """
        # Signals
        has_namespaces = any(n.get('namespace') for n in nodes if n.get('node_type') == 'class')
        uses_mysql_legacy = metadata_summary.get('uses_mysql_legacy', False)
        high_procedural_ratio = metadata_summary.get('procedural_ratio', 0.0) > 0.5
        has_composer = metadata_summary.get('has_composer', False)

        if not has_namespaces and uses_mysql_legacy:
            return "Era A — PHP 3 / PHP 4 (Procedural/Legacy)"
        
        if not has_namespaces and not uses_mysql_legacy and high_procedural_ratio:
            return "Era B — Early PHP 5 (Procedural/Custom MVC)"
        
        if has_namespaces and not has_composer:
            return "Era C — PHP 5.3+ (Namespaced Legacy)"
        
        if has_namespaces and has_composer:
            return "Era D — Modern PHP (PSR-4/Composer)"
        
        return "Unknown Legacy Era"
