"""
Requirement 9: Framework Fingerprinting
Detects legacy framework signatures to inform modernization strategies.
"""

import os
import json
from typing import List, Dict

class FrameworkFingerprinter:
    @staticmethod
    def detect(nodes: List[Dict], edges: List[Dict], root_path: str = None) -> str:
        """
        Parses composer.json for explicit versions. Falls back to heuristics.
        """
        composer_data = {}
        if root_path:
            composer_path = os.path.join(root_path, "composer.json")
            if os.path.exists(composer_path):
                try:
                    with open(composer_path, 'r', encoding='utf-8') as f:
                        composer_data = json.load(f)
                except Exception:
                    pass

        if composer_data:
            require = composer_data.get("require", {})
            php_version = require.get("php", "Unknown")
            
            # Check for known frameworks in require
            framework_str = None
            if "laravel/framework" in require:
                framework_str = f"Laravel (Framework: {require['laravel/framework']}, PHP: {php_version})"
            elif "symfony/symfony" in require:
                framework_str = f"Symfony (Framework: {require['symfony/symfony']}, PHP: {php_version})"
            elif "codeigniter4/framework" in require:
                framework_str = f"CodeIgniter (Framework: {require['codeigniter4/framework']}, PHP: {php_version})"
            elif "yiisoft/yii2" in require:
                framework_str = f"Yii2 (Framework: {require['yiisoft/yii2']}, PHP: {php_version})"
            elif "cakephp/cakephp" in require:
                framework_str = f"CakePHP (Framework: {require['cakephp/cakephp']}, PHP: {php_version})"
            
            if framework_str:
                return framework_str

        # Fallback to heuristics
        file_names = {n.get('name', '').lower() for n in nodes if n.get('node_type') == 'file'}
        class_names = {n.get('fqn', '').lower() for n in nodes if n.get('node_type') == 'class'}
        
        # WordPress
        if 'wp-config.php' in file_names or 'wp-load.php' in file_names:
            return "WordPress (Legacy Monolith)"
            
        # Zend 1
        if any(c.startswith('zend_') for c in class_names):
            return "Zend Framework 1.x"
            
        # CodeIgniter 2/3
        if 'codeigniter.php' in file_names or any(c.startswith('ci_') for c in class_names):
            return "CodeIgniter (Legacy)"
            
        # Laravel (Modern)
        if 'artisan' in file_names and any('app/providers' in str(f) for f in file_names):
            return "Laravel (Modern MVC)"
            
        # Symfony
        if 'console' in file_names and 'appkernel.php' in file_names:
            return "Symfony (Early Modern)"
            
        if composer_data and "php" in composer_data.get("require", {}):
            return f"Custom App (PHP: {composer_data['require']['php']})"
            
        return "Bespoke / Custom App"
