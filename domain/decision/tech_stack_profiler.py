"""
Requirement 10, 11, 12, 13: Technical Stack Profiler
Analyzes deep technical patterns to create migration blueprints.
"""

from typing import List, Dict

class TechStackProfiler:
    @staticmethod
    def profile(nodes: List[Dict], edges: List[Dict]) -> dict:
        """
        Profiles the DB, Auth, Template, and Autoloading layers based on actual AST metadata.
        """
        db_layer = "Bespoke / Custom"
        auth_layer = "Bespoke / Custom"
        template_layer = "Bespoke / Custom"
        autoloading = "Bespoke / Custom"

        has_mysql_legacy = False
        has_db_sink = False
        has_auth_sink = False
        has_template_sink = False
        has_legacy_autoload = False
        has_composer = any(n.get('name') == 'composer.json' for n in nodes if n.get('node_type') == 'file')

        for n in nodes:
            meta = n.get('metadata', {})
            
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

            for req_type in find_keys(meta, 'type'):
                if req_type == "MYSQL_LEGACY":
                    has_mysql_legacy = True
                elif req_type == "LEGACY_AUTOLOAD":
                    has_legacy_autoload = True
                elif req_type == "INLINE_HTML":
                    has_template_sink = True
                    
                # Side effects often use the same 'type' key
                if req_type == "DB":
                    has_db_sink = True
                elif req_type in ["AUTH", "LEGACY_HASH"]:
                    has_auth_sink = True
                elif req_type == "TEMPLATE":
                    has_template_sink = True

            # Also check side_effects lists which are strings
            for se_list in find_keys(meta, 'side_effects'):
                if isinstance(se_list, list):
                    for st in se_list:
                        if st == "DB":
                            has_db_sink = True
                        elif st in ["AUTH", "LEGACY_HASH"]:
                            has_auth_sink = True
                        elif st == "TEMPLATE":
                            has_template_sink = True

        if has_mysql_legacy:
            db_layer = "mysql_* Family (Legacy)"
        elif has_db_sink:
            db_layer = "Raw SQL (PDO / mysqli)"
            
        if has_auth_sink:
            auth_layer = "Custom / Procedural Hooks"
            
        if has_template_sink:
            template_layer = "Inline HTML / include()"
            
        if has_legacy_autoload:
            autoloading = "__autoload() (Deprecated)"
        elif has_composer:
            autoloading = "Composer (PSR-4)"

        return {
            "db_layer": db_layer,
            "auth_layer": auth_layer,
            "template_layer": template_layer,
            "autoloading_strategy": autoloading
        }
