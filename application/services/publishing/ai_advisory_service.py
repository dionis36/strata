import os
import json
import logging
import requests
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AIAdvisoryService:
    """Uses Gemini or OpenRouter to synthesize high-level strategic executive summaries."""
    
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
        self.client = genai.Client(api_key=self.gemini_key) if self.gemini_key else None

    def _invoke_with_retry(self, generate_func, max_retries=2, base_delay=5):
        """Executes an API call with exponential backoff for 429 and 503 errors."""
        import time
        for attempt in range(max_retries):
            try:
                return generate_func()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "503" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "UNAVAILABLE" in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"API rate limit or overload hit (Attempt {attempt+1}/{max_retries}). Sleeping for {delay} seconds before retrying...")
                        time.sleep(delay)
                    else:
                        logger.error(f"API failed after {max_retries} attempts: {e}")
                        raise
                else:
                    raise

    def synthesize_executive_summary(self, system_context: Any, legacy_posture: Any) -> Dict[str, str]:
        """Calls an LLM to write a high-level strategic executive summary."""
        if not self.openrouter_key and not self.client:
            raise ValueError("No API keys found. AI Synthesis unavailable.")
            
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
        
        Provide a strategic evaluation in three exact parts.
        You must return a raw JSON object with EXACTLY these three string keys.
        
        CRITICAL FORMATTING RULES:
        1. Do NOT use double quotes (") anywhere inside the text values of current_state, critical_risks, or strategic_roadmap. If you need to quote anything, use single quotes (') or backticks (`) instead.
        2. All double quotes (") must strictly be used ONLY for JSON keys and JSON value boundaries.
        3. Do not include markdown backticks around the JSON.
        
        {{
            "current_state": "A comprehensive, multi-paragraph deep-dive assessment of the system's current architectural health. You MUST explicitly list the structural components of the application (e.g. X Models, Y Controllers, Z Schemas) based on the Architectural Footprint provided above to prove deep comprehension. Use professional, advisory tone and expand on the implications of the current footprint.",
            "critical_risks": "A detailed explanation of the biggest systemic dangers based on the lowest dimension scores. Provide multiple paragraphs if necessary.",
            "strategic_roadmap": "A definitive, highly-detailed 3-step action plan to modernize the system without halting feature development. Explain the 'why' behind each step."
        }}
        """
        
        try:
            if self.openrouter_key:
                def _call_openrouter():
                    headers = {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": self.openrouter_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                    response.raise_for_status()
                    result_json = response.json()
                    content = result_json["choices"][0]["message"]["content"]
                    
                    # Extract clean JSON block if there is preamble/postamble
                    content_str = content.strip()
                    start_idx = content_str.find('{')
                    end_idx = content_str.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        content_str = content_str[start_idx:end_idx+1]
                        
                    try:
                        return json.loads(content_str, strict=False)
                    except Exception as parse_e:
                        logger.warning(f"Initial JSON parse failed: {parse_e}. Trying to repair and parse using AST...")
                        try:
                            import ast
                            py_str = content_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
                            return ast.literal_eval(py_str)
                        except Exception as ast_e:
                            logger.error(f"AST parse also failed: {ast_e}")
                            raise parse_e
                            
                return self._invoke_with_retry(_call_openrouter)
            else:
                def _call_gemini():
                    res = self.client.models.generate_content(
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
                    return json.loads(res.text, strict=False)
                return self._invoke_with_retry(_call_gemini)
        except Exception as e:
            logger.error(f"API Error (Summary): {e}")
            raise

    def _generate_summary_fallback(self, system_context: Any) -> Dict[str, str]:
        return {
            "current_state": f"The {system_context.framework} system contains significant technical debt.",
            "critical_risks": "High architectural coupling and low test coverage make modifications dangerous.",
            "strategic_roadmap": "1. Introduce static analysis.\n2. Add characterization tests.\n3. Incrementally decouple the database layer."
        }
