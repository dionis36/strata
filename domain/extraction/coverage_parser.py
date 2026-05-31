import os
import xml.etree.ElementTree as ET
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class CoverageParser:
    """Parses Clover/PHPUnit coverage XML reports to map classes to their coverage percentage."""

    @staticmethod
    def parse(project_path: str) -> Dict[str, float]:
        """
        Scans the project for coverage.xml or clover.xml and extracts coverage per class/file.
        Returns a dict of { "fqn_or_filename": float_coverage_percentage }
        """
        coverage_map = {}
        
        # Look for common coverage files
        potential_files = [
            os.path.join(project_path, "clover.xml"),
            os.path.join(project_path, "coverage.xml"),
            os.path.join(project_path, "build", "logs", "clover.xml")
        ]
        
        target_file = None
        for pf in potential_files:
            if os.path.exists(pf):
                target_file = pf
                break
                
        if not target_file:
            logger.info("No test coverage XML found in project.")
            return coverage_map
            
        try:
            tree = ET.parse(target_file)
            root = tree.getroot()
            
            # Parse Clover XML format
            for class_node in root.findall(".//class"):
                name = class_node.get("name")
                # In Clover, a class node contains metrics
                metrics = class_node.find("metrics")
                if metrics is not None and name:
                    statements = float(metrics.get("statements", 0))
                    covered_statements = float(metrics.get("coveredstatements", 0))
                    
                    if statements > 0:
                        coverage = covered_statements / statements
                        coverage_map[name.lower()] = coverage
            
            # Fallback to file-level coverage if classes aren't explicitly mapped
            for file_node in root.findall(".//file"):
                path = file_node.get("name")
                metrics = file_node.find("metrics")
                if metrics is not None and path:
                    statements = float(metrics.get("statements", 0))
                    covered_statements = float(metrics.get("coveredstatements", 0))
                    if statements > 0:
                        coverage = covered_statements / statements
                        # Standardize path
                        coverage_map[os.path.basename(path).lower()] = coverage
                        
        except Exception as e:
            logger.error(f"Error parsing coverage file {target_file}: {e}")
            
        return coverage_map
