"""
Requirement 9: Framework Fingerprinting
Detects legacy framework signatures to inform modernization strategies.
"""

from typing import List, Dict

class FrameworkFingerprinter:
    @staticmethod
    def detect(nodes: List[Dict], edges: List[Dict]) -> str:
        """
        Heuristically identifies PHP frameworks based on file names and class patterns.
        """
        file_names = {n.get('name').lower() for n in nodes if n.get('node_type') == 'file'}
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
        if 'artisan' in file_names and 'app/providers' in str(file_names):
            return "Laravel (Modern MVC)"
            
        # Symfony
        if 'console' in file_names and 'appkernel.php' in file_names:
            return "Symfony (Early Modern)"
            
        return "Custom Legacy Monolith"
