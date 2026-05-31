from sqlalchemy.orm import Session
from application.services.publishing.evidence_builder import EvidenceBuilder
from application.services.publishing.quality_gate import QualityGate
from application.services.publishing.document_generator import DocumentGenerator

class PublishingPipeline:
    """Orchestrates the artifact generation process."""
    
    def __init__(self, db: Session):
        self.db = db
        self.builder = EvidenceBuilder(db)
        self.gate = QualityGate()
        self.generator = DocumentGenerator()

    def publish_executive_report(self, run_id: int) -> str:
        # Pass 1 & 2: Build Evidence
        model = self.builder.build(run_id)
        
        # Pass 4: Quality Gate
        if not self.gate.validate(model):
            return "# Error: Quality Gate Failed\n\nThe underlying analysis lacks sufficient evidence or specificity to generate a reliable executive report."
            
        # Pass 5: Render
        return self.generator.generate_executive_report(model)
        
    def publish_technical_report(self, run_id: int) -> str:
        model = self.builder.build(run_id)
        if not self.gate.validate(model):
            return "# Error: Quality Gate Failed"
        return self.generator.generate_technical_report(model)
