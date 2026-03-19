"""
Phase 4: Lightweight Behavioral Tokenizer
Strips PHP comments and extracts only protected string literals and un-commented structural code 
to prevent false-positive SQL findings in legacy PHP codebases.
"""
import re
from typing import List

class CodeSanitizer:
    @staticmethod
    def remove_comments(code: str) -> str:
        """Removes C-style (/*...*/) and line (// ...) comments cautiously."""
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove single-line comments (but not inside url protocols like http://)
        # We naively split by newline and remove anything after //, unless it's an edge case
        lines = []
        for line in code.splitlines():
            # Basic naive strip - sufficient for Phase 4 detection
            if '//' in line and not ('http://' in line or 'https://' in line):
                line = line.split('//')[0]
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def extract_string_literals(code: str) -> List[str]:
        """Extracts standard single and double-quoted strings where raw SQL lives."""
        # Basic extraction matching "..." or '...'
        # For Phase 4, this is a sufficient heuristic.
        double_quotes = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', code)
        single_quotes = re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", code)
        return double_quotes + single_quotes

    @staticmethod
    def sanitize(code: str) -> dict:
        """Returns a sanitized view of the codebase for analysis."""
        clean_code = CodeSanitizer.remove_comments(code)
        literals = CodeSanitizer.extract_string_literals(clean_code)
        return {
            "clean_code": clean_code,  # Useful for ORM chaining
            "literals": literals       # Useful for raw SQL inspection
        }
