import logging
from application.services.publishing.models import CanonicalModel, Finding

logger = logging.getLogger(__name__)

class QualityGate:
    """Pass 4: Quality Review. Ensures documents are trustworthy and codebase-specific."""
    
    GENERIC_FILLER_PHRASES = [
        "opportunities for improvement",
        "areas of high complexity",
        "refactoring may help",
        "needs modernization"
    ]

    def validate(self, model: CanonicalModel) -> bool:
        """Validates the entire model before generation."""
        is_valid = True
        
        if not model.findings:
            logger.warning("Quality Gate Failed: Model has zero findings.")
            is_valid = False
            
        for finding in model.findings:
            if not self._validate_finding(finding):
                is_valid = False
                
        return is_valid

    def _validate_finding(self, finding: Finding) -> bool:
        # 1. Evidence Check
        if not finding.evidence or len(finding.evidence) == 0:
            logger.warning(f"Quality Gate Failed: Finding {finding.id} lacks evidence.")
            return False
            
        # 2. Specificity Check
        obs_lower = finding.observation.lower()
        for filler in self.GENERIC_FILLER_PHRASES:
            if filler in obs_lower:
                logger.warning(f"Quality Gate Failed: Finding {finding.id} uses generic filler: '{filler}'")
                return False
                
        return True
