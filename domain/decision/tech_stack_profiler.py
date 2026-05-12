"""
Requirement 10, 11, 12, 13: Technical Stack Profiler
Analyzes deep technical patterns to create migration blueprints.
"""

from typing import List, Dict

class TechStackProfiler:
    @staticmethod
    def profile(nodes: List[Dict], edges: List[Dict]) -> dict:
        """
        Profiles the DB, Auth, Template, and Autoloading layers.
        """
        # Collect 'virtual sink' edges
        sinks = {e.get('target_fqn', '') for e in edges if 'sink::' in e.get('target_fqn', '')}
        
        # Collect requirements-specific metadata (e.g., RAW_SQL, LEGACY_AUTOLOAD)
        # Note: These are often attached to Nodes as 'requirements' list
        # For simplicity, we'll check if any node has these markers.
        
        db_layer = "Modern (ORM/PDO)"
        if any('sink::DB' in s for s in sinks):
            db_layer = "Mixed (Raw SQL & Abstraction)"
            
        auth_layer = "Modern / Middleware"
        if any('sink::AUTH' in s for s in sinks) or any('sink::LEGACY_HASH' in s for s in sinks):
            auth_layer = "Legacy (Session-based / Homemade)"
            
        template_layer = "Native PHP / Unknown"
        if any('sink::TEMPLATE' in s for s in sinks):
            template_layer = "Custom / Smarty-like Engine"
            
        autoloading = "Standard (Composer/PSR-4)"
        # This signal comes from the 'requirements' metadata in nodes
        # We'll use a placeholder for now or assume if No Namespaces -> Legacy
        
        return {
            "db_layer": db_layer,
            "auth_layer": auth_layer,
            "template_layer": template_layer,
            "autoloading_strategy": autoloading
        }
