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
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def _invoke_with_retry(self, generate_func, max_retries=3, base_delay=30):
        """Executes a Gemini API call with exponential backoff for 429 and 503 errors."""
        import time
        for attempt in range(max_retries):
            try:
                return generate_func()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "503" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "UNAVAILABLE" in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Gemini API rate limit or overload hit (Attempt {attempt+1}/{max_retries}). Sleeping for {delay} seconds before retrying...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Gemini API failed after {max_retries} attempts: {e}")
                        raise
                else:
                    raise

    def synthesize_batch_findings(self, risk_data: List[Dict[str, Any]]) -> List[GeminiFindingResponse]:
        """Calls Gemini to write a bespoke finding narrative for a batch of high-risk components."""
        
        if not self.client:
            raise ValueError("No GEMINI_API_KEY found. AI Synthesis unavailable.")
            
        # We cap the batch to 5 items to keep the LLM context focused and fast.
        batch = risk_data[:5]
        
        playbook_rules = ""
        playbook_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../domain/explanation/playbook.json"))
        if os.path.exists(playbook_path):
            try:
                with open(playbook_path, "r", encoding="utf-8") as f:
                    playbook_data = json.load(f)
                    playbook_rules = json.dumps(playbook_data, indent=2)
            except Exception as e:
                logger.warning(f"Failed to load playbook.json: {e}")

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
        - `test_coverage`: Float representing unit test coverage (0.0 to 1.0).
        
        CRITICAL PLAYBOOK RULES (MUST FOLLOW):
        Match the structural anti-patterns found in `dependency_edges` or `domain_archetype` to the rules in this playbook. 
        If a rule matches, you MUST prioritize its strict recommendation in the `recommended_action` field.
        {playbook_rules}
        
        If a class is flagged as a GOD_CLASS, explicitly advise breaking it down based on its disjointed LCOM properties. 
        If it's a UTILITY that had its risk slashed, explain why it is structurally safe despite high fan-in.
        CRITICAL TEST RULE: If `test_coverage` is missing or below 0.20, the FIRST recommended action MUST be "Write Characterization Tests before attempting extraction". Refactoring legacy code without tests is extremely dangerous.
        Cite exact structural anti-patterns and use the `ast_metadata` to point to specific dependencies or line numbers.
        
        CRITICAL: Generate a valid `Mermaid.js` syntax string for the `mermaid_diagram` field. This diagram should be a `graph TD` that visually plots the component, its tightest dependencies, and a proposed architectural extraction boundary to fix the bottleneck. Do not wrap the string in markdown backticks, just the raw mermaid code.
        """
        
        try:
            def _call_api():
                return self.client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "findings": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "component_name": {"type": "STRING"},
                                            "category": {
                                                "type": "STRING",
                                                "enum": ["Architecture", "Security", "Complexity", "Coupling", "Legacy"]
                                            },
                                            "observation": {"type": "STRING"},
                                            "impact": {"type": "STRING"},
                                            "reasoning": {"type": "STRING"},
                                            "recommended_action": {"type": "STRING"},
                                            "priority": {
                                                "type": "STRING",
                                                "enum": ["Critical", "High", "Medium", "Low"]
                                            },
                                            "confidence": {
                                                "type": "STRING",
                                                "enum": ["Confirmed", "Probable", "Insufficient Evidence"]
                                            },
                                            "mermaid_diagram": {"type": "STRING"}
                                        },
                                        "required": ["component_name", "category", "observation", "impact", "reasoning", "recommended_action", "priority", "confidence", "mermaid_diagram"]
                                    }
                                }
                            },
                            "required": ["findings"]
                        },
                    ),
                )
            response = self._invoke_with_retry(_call_api)
            data = json.loads(response.text)
            return [GeminiFindingResponse(**f) for f in data.get("findings", [])]
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            raise

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

    def synthesize_executive_summary(self, system_context: Any, legacy_posture: Any) -> Dict[str, str]:
        """Calls Gemini to write a high-level strategic executive summary."""
        if not self.client:
            raise ValueError("No GEMINI_API_KEY found. AI Synthesis unavailable.")
            
        prompt = f"""
        You are a Principal PHP Modernization Architect consulting for a C-level executive.
        
        Analyze the overall health and structure of this legacy system:
        System Context:
        - Project: {system_context.project_name}
        - Total Files: {system_context.total_files}
        - Lines of Code: {system_context.lines_of_code}
        - Framework: {system_context.framework} ({system_context.php_era})
        - Overall Readiness: {system_context.overall_readiness}%
        - Architectural Footprint: {system_context.architectural_footprint}
        
        Legacy Posture Scores (0.0 to 10.0 scale, where 10 is modern):
        - Version Score: {legacy_posture.version_score if legacy_posture else 'N/A'}
        - Namespace Score: {legacy_posture.namespace_score if legacy_posture else 'N/A'}
        - Database Layer Score: {legacy_posture.db_layer_score if legacy_posture else 'N/A'}
        - Security Score: {legacy_posture.security_score if legacy_posture else 'N/A'}
        - Testability Score: {legacy_posture.testability_score if legacy_posture else 'N/A'}
        - Coupling Score: {legacy_posture.coupling_score if legacy_posture else 'N/A'}
        
        Provide a strategic evaluation in three exact parts:
        1. current_state: A blunt, 2-sentence assessment of the system's current architectural health. You MUST explicitly list the structural components of the application (e.g. X Models, Y Controllers, Z Schemas) based on the Architectural Footprint provided above to prove deep comprehension.
        2. critical_risks: The biggest systemic danger based on the lowest dimension scores.
        3. strategic_roadmap: A definitive 3-step action plan to modernize the system without halting feature development.
        """
        
        try:
            def _call_api():
                return self.client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "current_state": {"type": "STRING"},
                                "critical_risks": {"type": "STRING"},
                                "strategic_roadmap": {"type": "STRING"}
                            },
                            "required": ["current_state", "critical_risks", "strategic_roadmap"]
                        },
                    ),
                )
            response = self._invoke_with_retry(_call_api)
            data = json.loads(response.text)
            return data
        except Exception as e:
            logger.error(f"Gemini API Error (Summary): {e}")
            raise

    def _generate_summary_fallback(self, system_context: Any) -> Dict[str, str]:
        return {
            "current_state": f"The {system_context.framework} system contains significant technical debt.",
            "critical_risks": "High architectural coupling and low test coverage make modifications dangerous.",
            "strategic_roadmap": "1. Introduce static analysis. 2. Add characterization tests. 3. Incrementally decouple the database layer."
        }

    def synthesize_rector_config(self, system_framework: str, php_era: str, ast_metrics: str) -> RectorArtifact:
        """Calls Gemini to write a bespoke, actionable rector.php script."""
        if not self.client:
            raise ValueError("No GEMINI_API_KEY found. AI Synthesis unavailable.")
            
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
            def _call_api():
                return self.client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RectorArtifact,
                    ),
                )
            response = self._invoke_with_retry(_call_api)
            data = json.loads(response.text)
            return RectorArtifact(**data)
        except Exception as e:
            logger.error(f"Gemini API Error (Rector): {e}")
            raise
            
    def _generate_rector_fallback(self) -> RectorArtifact:
        fallback_code = "<?php\n\nuse Rector\\Config\\RectorConfig;\nuse Rector\\Set\\ValueObject\\LevelSetList;\n\nreturn static function (RectorConfig $rectorConfig): void {\n    $rectorConfig->sets([\n        LevelSetList::UP_TO_PHP_82\n    ]);\n};\n"
        return RectorArtifact(
            target_php_version="8.2",
            suggested_rules=["LevelSetList::UP_TO_PHP_82"],
            rector_php_code=fallback_code,
            explanation="Static fallback configuration due to missing API key."
        )
