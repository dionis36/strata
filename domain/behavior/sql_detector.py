"""
Phase 4: Raw SQL Detector
Scans protected string literals for raw SQL write operations (INSERT, UPDATE, DELETE).
"""
import re
from typing import List

WRITE_KEYWORDS = ["INSERT INTO", "UPDATE", "DELETE FROM", "REPLACE INTO", "CALL ", "EXEC "]

class SqlDetector:
    @staticmethod
    def detect_write_queries(literals: List[str]) -> List[str]:
        """Scans extracted string literals for write SQL patterns and stored procedures."""
        queries = []
        for literal in literals:
            upper_literal = literal.upper()
            # Fast keyword check
            if any(keyword in upper_literal for keyword in WRITE_KEYWORDS):
                # Ensure it loosely looks like a query
                # e.g., looks for "UPDATE <table> SET" or "INSERT INTO <table>" or "CALL <proc>"
                if re.search(r'\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO|CALL|EXEC)\b\s+\w+', literal, re.IGNORECASE):
                    queries.append(literal.strip())
        return queries
