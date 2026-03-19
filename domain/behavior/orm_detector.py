"""
Phase 4: ORM Write Detector
Scans clean codebase (comments removed) for ORM-based database mutations.
"""
import re
from typing import List

class OrmDetector:
    # Common PHP ORM write patterns (Eloquent, CodeIgniter Active Record, Doctrine)
    ORM_PATTERNS = [
        r'->save\(\)',
        r'::create\(',
        r'->update\(',
        r'->delete\(',
        r'->insert\(',
        r'->insert_batch\(',
        r'->update_batch\('
    ]

    @staticmethod
    def detect_orm_writes(clean_code: str) -> List[str]:
        """Finds lines containing ORM write operations."""
        writes = []
        for line in clean_code.splitlines():
            line = line.strip()
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in OrmDetector.ORM_PATTERNS):
                writes.append(line)
        return writes
