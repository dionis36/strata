"""
Phase 4: Write Analyzer
Orchestrator that combines Tokenizer, SQL/ORM Detectors, and Table Extractor
to yield a mapping of targeted tables per file/class.
"""
from typing import List, Dict

from domain.behavior.tokenizer import CodeSanitizer
from domain.behavior.sql_detector import SqlDetector
from domain.behavior.orm_detector import OrmDetector
from domain.behavior.table_extractor import TableExtractor

class WriteAnalyzer:
    @staticmethod
    def analyze_file(file_content: str) -> Dict[str, List[str]]:
        """Analyzes full PHP file content and extracts database write behavior.
        
        Returns:
            Dict containing:
                - 'tables': List of unique table names modified.
                - 'sql_writes': List of detected raw SQL operations.
                - 'orm_writes': List of detected ORM operations.
        """
        # 1. Sanitize code (strip comments, protect literals)
        sanitized = CodeSanitizer.sanitize(file_content)
        
        # 2. Detect operations
        sql_queries = SqlDetector.detect_write_queries(sanitized['literals'])
        orm_lines = OrmDetector.detect_orm_writes(sanitized['clean_code'])
        
        # 3. Extract impacted tables
        tables = TableExtractor.extract_all(sql_queries, orm_lines)
        
        return {
            "tables": tables,
            "sql_writes": sql_queries,
            "orm_writes": orm_lines,
            "total_writes": len(sql_queries) + len(orm_lines)
        }
