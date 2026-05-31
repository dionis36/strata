import os
import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiFindingResponse(BaseModel):
    component_name: str
    category: str
    observation: str
    impact: str
    reasoning: str
    recommended_action: str
    priority: str
    confidence: str

class GeminiFindingList(BaseModel):
    findings: list[GeminiFindingResponse]

class AIAdvisoryService:
    """Uses Gemini to synthesize intelligent impact and reasoning for evidence nodes."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client() if self.api_key else None

    def synthesize_batch_findings(self, risk_data: List[Dict[str, Any]]) -> List[GeminiFindingResponse]:
        """Calls Gemini to write a bespoke finding narrative for a batch of high-risk components."""
        
        if not self.client:
            logger.warning("No GEMINI_API_KEY found. Falling back to static strings.")
            return self._generate_batch_fallback(risk_data)
            
        # We cap the batch to 5 items to keep the LLM context focused and fast.
        batch = risk_data[:5]
        
        prompt = f"""
        You are a Principal PHP Architect analyzing a legacy codebase.
        
        Analyze these highest-risk components extracted from the AST:
        {json.dumps(batch, indent=2)}
        
        For each component, generate a highly specific, consultant-grade architectural assessment.
        Do NOT use generic filler like 'opportunities for improvement' or 'areas of high complexity'.
        Be extremely concrete about what the coupling and blast radius mean for a PHP application's maintainability.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiFindingList,
                ),
            )
            data = json.loads(response.text)
            return [GeminiFindingResponse(**f) for f in data.get("findings", [])]
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self._generate_batch_fallback(batch)

    def _generate_batch_fallback(self, risk_data: List[Dict[str, Any]]) -> List[GeminiFindingResponse]:
        results = []
        for r in risk_data:
            risk_score = r.get("risk_score", 0)
            blast_radius = r.get("blast_radius", 0)
            name = r.get("component_name", "Unknown")
            
            priority = "Critical" if risk_score > 0.8 else "High"
            reasoning = "High structural coupling pressure indicates this component is deeply entangled."
            action = "Isolate dependencies behind an interface. Write integration tests before refactoring."
            
            if blast_radius > 0.8:
                reasoning = "Extremely high blast radius. This component is a single point of failure."
                action = "Extract into a dedicated bounded context and decouple callers via events or strict APIs."
                
            results.append(GeminiFindingResponse(
                component_name=name,
                category="Architecture",
                observation=f"Component '{name}' identified as an architectural bottleneck.",
                impact="Modifications to this component carry a high blast radius, risking cascading failures.",
                reasoning=reasoning,
                recommended_action=action,
                priority=priority,
                confidence="Confirmed" if risk_score > 0.8 else "Probable"
            ))
        return results
