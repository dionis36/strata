"""
Phase 4: Table Extractor
Extracts normalized table names from SQL queries and ORM calls.
"""
import re
from typing import Optional, List

class TableExtractor:
    @staticmethod
    def normalize_table_name(table_name: str) -> str:
        """Removes noise (backticks, quotes) and lowercases the table name."""
        clean = table_name.replace('`', '').replace('"', '').replace("'", "").strip()
        return clean.lower()

    @staticmethod
    def extract_from_sql(query: str) -> Optional[str]:
        """Extracts the primary table name from a write SQL query."""
        # Matches: INSERT INTO table, UPDATE table, DELETE FROM table
        pattern = r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+([a-zA-Z0-9_`\'\"]+)"
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return TableExtractor.normalize_table_name(match.group(1))
        return None

    @staticmethod
    def extract_from_orm(line: str) -> Optional[str]:
        """Attempts to infer table context from generic ORM calls (best effort heuristic)."""
        # Finds: $this->db->update('table_name', data) or Model::create(data)
        # Note: True ORM table mapping requires deep static analysis. 
        # For Phase 4, we use simple localized regex heuristics.
        table_param_match = re.search(r'->(?:update|insert|delete)\(\s*[\'"]([a-zA-Z0-9_]+)[\'"]', line, re.IGNORECASE)
        if table_param_match:
            return TableExtractor.normalize_table_name(table_param_match.group(1))
        return None

    @staticmethod
    def extract_all(queries: List[str], orm_lines: List[str]) -> List[str]:
        """Aggregates all distinct table names touched by these operations."""
        tables = set()
        for q in queries:
            tbl = TableExtractor.extract_from_sql(q)
            if tbl:
                tables.add(tbl)
        
        for line in orm_lines:
            tbl = TableExtractor.extract_from_orm(line)
            if tbl:
                tables.add(tbl)
                
        return sorted(list(tables))
