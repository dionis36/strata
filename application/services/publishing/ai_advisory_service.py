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
    mermaid_diagram: str

class GeminiFindingList(BaseModel):
    findings: list[GeminiFindingResponse]

class RectorArtifact(BaseModel):
    target_php_version: str
    suggested_rules: list[str]
    rector_php_code: str
    explanation: str

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
        
        Analyze these highest-risk components extracted directly from the Abstract Syntax Tree (AST):
        {json.dumps(batch, indent=2)}
        
        For each component, generate a highly specific, consultant-grade architectural assessment.
        Do NOT use generic filler. Base your analysis on the provided semantic metrics:
        - `domain_archetype`: The system-assigned role of the class (e.g., ENTITY, UTILITY, CONTROLLER, GOD_CLASS).
        - `lcom`: Lack of Cohesion of Methods. A score > 0.8 means the class is severely disjointed.
        - `wmc`: Weighted Method Count (Cyclomatic Complexity). > 50 indicates massive logic bloat.
        - `semantic_multiplier`: How the system adjusted the raw graph risk based on semantic rules.
        
        If a class is flagged as a GOD_CLASS, explicitly advise breaking it down based on its disjointed LCOM properties. 
        If it's a UTILITY that had its risk slashed, explain why it is structurally safe despite high fan-in.
        Cite exact structural anti-patterns and use the `ast_metadata` to point to specific dependencies or line numbers.
        
        CRITICAL: Generate a valid `Mermaid.js` syntax string for the `mermaid_diagram` field. This diagram should be a `graph TD` that visually plots the component, its tightest dependencies, and a proposed architectural extraction boundary to fix the bottleneck. Do not wrap the string in markdown backticks, just the raw mermaid code.
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
                confidence="Confirmed" if risk_score > 0.8 else "Probable",
                mermaid_diagram=f"graph TD\n  {name} --> LegacyDependencies\n  style {name} fill:#f9f,stroke:#333,stroke-width:4px"
            ))
        return results

    def synthesize_rector_config(self, system_framework: str, php_era: str, ast_metrics: str) -> RectorArtifact:
        """Calls Gemini to write a bespoke, actionable rector.php script."""
        if not self.client:
            logger.warning("No GEMINI_API_KEY found. Falling back to static rector config.")
            return self._generate_rector_fallback()
            
        prompt = f"""
        You are an expert PHP modernization tool. 
        Analyze this extracted legacy codebase data:
        - Framework: {system_framework}
        - Era: {php_era}
        - AST Metadata & Issues: {ast_metrics}
        
        Generate a complete, ready-to-run `rector.php` configuration file to upgrade this exact codebase.
        Include specific Rector Sets and Rules that perfectly map to the framework and issues described.
        Ensure the output strictly adheres to the JSON schema.
        DO NOT include markdown backticks around the `rector_php_code` string itself.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RectorArtifact,
                ),
            )
            data = json.loads(response.text)
            return RectorArtifact(**data)
        except Exception as e:
            logger.error(f"Gemini API Error (Rector): {e}")
            return self._generate_rector_fallback()
            
    def _generate_rector_fallback(self) -> RectorArtifact:
        fallback_code = "<?php\n\nuse Rector\\Config\\RectorConfig;\nuse Rector\\Set\\ValueObject\\LevelSetList;\n\nreturn static function (RectorConfig $rectorConfig): void {\n    $rectorConfig->sets([\n        LevelSetList::UP_TO_PHP_82\n    ]);\n};\n"
        return RectorArtifact(
            target_php_version="8.2",
            suggested_rules=["LevelSetList::UP_TO_PHP_82"],
            rector_php_code=fallback_code,
            explanation="Static fallback configuration due to missing API key."
        )
