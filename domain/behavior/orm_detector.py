"""
Phase 4: ORM Write Detector
Scans clean codebase (comments removed) for ORM-based database mutations.
"""
import re
from typing import List

class OrmDetector:
    # Common PHP ORM write patterns (Eloquent, CodeIgniter Active Record, Doctrine, PHP-ActiveRecord)
    ORM_PATTERNS = [
        r'->save\(\)',
        r'->save\(false\)',           # PHP-ActiveRecord: save without validation
        r'::create\(',
        r'->update\(',
        r'->delete\(',
        r'->insert\(',
        r'->insert_batch\(',
        r'->update_batch\(',
        r'->update_attributes\(',    # PHP-ActiveRecord: bulk attribute update
        r'->update_attribute\(',     # PHP-ActiveRecord: single attribute update
        r'->destroy\(',              # PHP-ActiveRecord: delete record
        r'::delete_all\(',           # PHP-ActiveRecord: bulk delete
        r'::update_all\(',           # PHP-ActiveRecord: bulk update
        r'::create_or_update\(',     # PHP-ActiveRecord: upsert
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
