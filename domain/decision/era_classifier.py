"""
Requirement 1: Era Classification
Determines if a project is Era A (Procedural), B (Custom MVC), C (Namespaced), or D (Modern).
"""

from typing import List, Dict

class EraClassifier:
    @staticmethod
    def classify(nodes: List[Dict], edges: List[Dict], metadata_summary: Dict) -> str:
        """
        Heuristically determines the PHP Era using a weighted probability matrix.
        """
        score = 0
        
        # Signals
        has_namespaces = any(n.get('namespace') for n in nodes if n.get('node_type') == 'class')
        namespace_ratio = metadata_summary.get('namespace_ratio', 0.0)
        procedural_ratio = metadata_summary.get('procedural_ratio', 0.0)
        uses_mysql_legacy = metadata_summary.get('uses_mysql_legacy', False)
        has_composer = metadata_summary.get('has_composer', False)
        entry_point_count = metadata_summary.get('entry_point_count', 0)
        
        # 1. Negative Weights (Legacy Anchors)
        if uses_mysql_legacy:
            score -= 50
        if procedural_ratio > 0.6:
            score -= 30
        if entry_point_count > 5:
            score -= 20
            
        # 2. Positive Weights (Modern Anchors)
        if has_composer:
            score += 40
        if namespace_ratio > 0.5:
            score += 40
        elif namespace_ratio > 0.2:
            score += 20
            
        if entry_point_count == 1:
            score += 20
            
        # 3. Era Resolution based on Final Score
        if score < 0:
            return "Era A — PHP 3 / PHP 4 (Procedural/Legacy)"
        elif 0 <= score <= 30:
            return "Era B — Early PHP 5 (Procedural/Custom MVC)"
        elif 31 <= score <= 70:
            return "Era C — PHP 5.3+ (Namespaced Legacy)"
        else:
            return "Era D — Modern PHP (PSR-4/Composer)"
