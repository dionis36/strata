import os
import json
import logging
import requests
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import json_repair

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

    def synthesize_executive_summary(self, system_context: Any, legacy_posture: Any, recs: List[Dict[str, Any]] = None, hotspots: List[Dict[str, Any]] = None, boundary_data: Any = None, database_data: Any = None, architecture_data: Any = None, global_state_data: Any = None, roadmap_data: Any = None) -> Dict[str, Any]:
        """Calls an LLM to write a high-level strategic executive summary."""
        if not self.openrouter_key and not self.client:
            raise ValueError("No API keys found. AI Synthesis unavailable.")
            
        recs_str = ""
        if recs:
            recs_str = "\n".join([
                f"- Module '{r.get('Context')}': Recommend {r.get('Recommended Strategy')} (ROI: {r.get('Modernization ROI')}%, Effort: {r.get('Migration Effort')}). Rationale: {r.get('Rationale')}. Primary Blocker: {r.get('Primary Blocker')}."
                for r in recs
            ])
        else:
            recs_str = "No specific module-level recommendations calculated."

        hotspots_str = ""
        if hotspots:
            hotspots_str = "\n".join([
                f"- File '{h.get('file_path', h.get('component_name', 'Unknown'))}': Risk Score: {h.get('risk_score', 0):.1f}/100, WMC (Complexity): {h.get('wmc', 0)}, LCOM (Lack of Cohesion): {h.get('lcom', 0):.2f}, Instability: {h.get('instability', 0):.2f}, Halstead Effort: {h.get('halstead_effort', 0):.1f}, PageRank: {h.get('pagerank', 0):.4f}, DB Write Intensity: {h.get('write_intensity', 0):.2f}."
                for hr, h in zip(range(len(hotspots)), hotspots)
            ])
        else:
            hotspots_str = "No specific code hotspots or risk items isolated."
            
        boundary_str = str(boundary_data) if boundary_data else "None"
        database_str = str(database_data) if database_data else "None"
        architecture_str = str(architecture_data) if architecture_data else "None"
        global_state_str = str(global_state_data) if global_state_data else "None"
        roadmap_str = json.dumps(roadmap_data.get('phases', []), indent=2) if roadmap_data else "None"

        prompt = f"""
        You are a Principal PHP Modernization Architect consulting for a C-level executive.
        
        Analyze the overall health and structure of this legacy system:
        System Context:
        - Project: {system_context.project_name}
        - Project Description / Documentation (README Excerpt): {getattr(system_context, 'project_description', 'No description available.')}
        - Total Files: {system_context.total_files}
        - Lines of Code: {system_context.lines_of_code}
        - Framework: {system_context.framework} ({system_context.php_era})
        - Overall Readiness: {system_context.overall_readiness}%
        - Architectural Footprint: {system_context.architectural_footprint}
        
        Legacy Posture Scores (0.0 to 10.0 scale, where 10 is modern):
        - Version Score: {legacy_posture.version_score if legacy_posture else 'N/A'}
        - Namespace Score: {legacy_posture.namespace_score if legacy_posture else 'N/A'} (Note: A score of 0.0 means the project's own source code does not use PSR-4 namespaces, even if vendor/dependency frameworks in the graph do).
        - Database Layer Score: {legacy_posture.db_layer_score if legacy_posture else 'N/A'}
        - Security Score: {legacy_posture.security_score if legacy_posture else 'N/A'}
        - Testability Score: {legacy_posture.testability_score if legacy_posture else 'N/A'}
        - Coupling Score: {legacy_posture.coupling_score if legacy_posture else 'N/A'}
        
        Detailed Backend Recommendations calculated per cluster:
        {recs_str}
        
        Identified Hotspots & Code-Level Risks:
        {hotspots_str}
        
        Boundary Intelligence:
        {boundary_str}
        
        Database Intelligence:
        {database_str}
        
        Architecture Data:
        {architecture_str}
        
        Global State Data:
        {global_state_str}
        
        Strategic Roadmap Sequence (Deterministic):
        {roadmap_str}
        
        Provide a strategic evaluation in exact JSON format.
        You must return a raw JSON object with EXACTLY these keys.
        
        CRITICAL FORMATTING RULES:
        1. Do NOT use double quotes (") anywhere inside the text values. If you need to quote anything, use single quotes (') or backticks (`) instead.
        2. All double quotes (") must strictly be used ONLY for JSON keys and JSON value boundaries.
        3. Do not include markdown backticks around the JSON.
        
        {{
            "current_state": "A comprehensive, multi-paragraph (3 to 4 paragraphs) deep-dive assessment of the system's current architectural health. Paragraph 1: Introduce the system using its real project name and explicitly explain the system's overall purpose, domain, or use cases (based on the Project Description/documentation context). Connect this purpose to the physical codebase footprint (total files, lines of code, and specific layers) to paint the bigger picture. Paragraph 2: Analyze the structural topology and metrics. Detail the footprint numbers (Models, Controllers, Views, CLI Scripts, Schemas, Libraries) and explain the namespace adoption score (why it is 0.0, why classes live in the global scope, and the implications for modern autoloading). Paragraph 3: Detail the coupling, complexity, and hotspot findings. Explicitly reference the top class hotspots from the provided hotspot list, specifying their WMC (complexity), LCOM (lack of cohesion), instability, and lack of test coverage. Explain the implications of these hotspots on architectural risk. Paragraph 4: Synthesize the bigger picture and modernization impedance. Explain how these factors combine to create high regression risks and why refactoring or upgrading is critical to secure and professionalize the application. Ensure paragraphs are separated by a double newline (\\n\\n) so they render correctly in the HTML view.",
            "critical_risks": "A detailed explanation of the biggest systemic dangers based on the lowest dimension scores and code-level hotspots. Explicitly reference the risks of SQL injection (Score 0.0), testability gaps (Score 0.0), and architectural coupling of identified hotspots.",
            "boundary_layer_insights": "Insight into the boundary layer coupling, API endpoints, and vendor footprint based on the provided Boundary Intelligence data.",
            "architecture_insights": "Insights into the layered architecture and bounded contexts.",
            "database_coupling_insights": "Insight into database ownership and CRUD access patterns.",
            "global_state_insights": "Insight into the usage of superglobals and side-effects.",
            "quick_wins": [
                {{ "title": "Title of quick win", "impact": "High/Medium/Low impact description" }}
            ],
            "security_posture": "Narrative evaluating the overall security risks (e.g. SQL injection, unprotected endpoints).",
            "testing_strategy": "A recommendation for writing the first tests for the system.",
            "strategic_roadmap_prose": [
                {{
                    "phase_id": 0,
                    "executive_summary": "Provide a 2-3 sentence executive rationale for Phase 0 based strictly on the provided roadmap data."
                }},
                {{
                    "phase_id": 1,
                    "executive_summary": "Provide a 2-3 sentence executive rationale for Phase 1 based strictly on the provided roadmap data."
                }},
                {{
                    "phase_id": 2,
                    "executive_summary": "Provide a 2-3 sentence executive rationale for Phase 2 based strictly on the provided roadmap data."
                }},
                {{
                    "phase_id": 3,
                    "executive_summary": "Provide a 2-3 sentence executive rationale for Phase 3 based strictly on the provided roadmap data."
                }},
                {{
                    "phase_id": 4,
                    "executive_summary": "Provide a 2-3 sentence executive rationale for Phase 4 based strictly on the provided roadmap data."
                }}
            ]
        }}
        """
        
        try:
            if self.openrouter_key:
                try:
                    def _call_openrouter():
                        headers = {
                            "Authorization": f"Bearer {self.openrouter_key}",
                            "Content-Type": "application/json"
                        }
                        data = {
                            "model": self.openrouter_model,
                            "messages": [{"role": "user", "content": prompt}]
                        }
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                        response.raise_for_status()
                        result_json = response.json()
                        content = result_json.get("choices", [{}])[0].get("message", {}).get("content")
                        if not content:
                            raise ValueError(f"Model {self.openrouter_model} returned empty or null content. Response: {result_json}")
                            
                        # Extract clean JSON block if there is preamble/postamble
                        content_str = content.strip()
                        start_idx = content_str.find('{')
                        end_idx = content_str.rfind('}')
                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            content_str = content_str[start_idx:end_idx+1]
                            
                        try:
                            return json_repair.loads(content_str)
                        except Exception as parse_e:
                            logger.error(f"json_repair parse failed: {parse_e}")
                            raise parse_e
                                
                    return self._invoke_with_retry(_call_openrouter)
                except Exception as or_err:
                    if self.client:
                        logger.warning(f"OpenRouter synthesis failed ({or_err}). Falling back to native Gemini...")
                    else:
                        raise or_err

            if self.client:
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
                                    "boundary_layer_insights": {"type": "STRING"},
                                    "architecture_insights": {"type": "STRING"},
                                    "database_coupling_insights": {"type": "STRING"},
                                    "global_state_insights": {"type": "STRING"},
                                    "security_posture": {"type": "STRING"},
                                    "testing_strategy": {"type": "STRING"},
                                    "quick_wins": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "title": {"type": "STRING"},
                                                "impact": {"type": "STRING"}
                                            },
                                            "required": ["title", "impact"]
                                        }
                                    },
                                    "strategic_roadmap": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "step_number": {"type": "INTEGER"},
                                                "title": {"type": "STRING"},
                                                "description": {"type": "STRING"},
                                                "rationale": {"type": "STRING"}
                                            },
                                            "required": ["step_number", "title", "description", "rationale"]
                                        }
                                    }
                                },
                                "required": ["current_state", "critical_risks", "boundary_layer_insights", "architecture_insights", "database_coupling_insights", "global_state_insights", "security_posture", "testing_strategy", "quick_wins", "strategic_roadmap"]
                            },
                        ),
                    )
                    return json_repair.loads(res.text)
                return self._invoke_with_retry(_call_gemini)
        except Exception as e:
            logger.error(f"API Error (Summary): {e}")
            raise
 
    def _generate_summary_fallback(self, system_context: Any) -> Dict[str, Any]:
        return {
            "current_state": (
                f"The {system_context.project_name} codebase is an enterprise-scale PHP system designed to execute mission-critical domain logic. The codebase spans {system_context.total_files} files and approximately {system_context.lines_of_code} lines of code, serving as a key backbone for business workflows.\n\n"
                "From a structural standpoint, the architecture shows significant legacy characteristics. The namespace adoption score of 0.0 reflects a total absence of PSR-4 namespace mapping in source files, forcing classes to reside in the global scope and rely on dynamic require/include loops for autoloading. This severely limits static analysis and modifiability.\n\n"
                "Dependency metrics reveal high coupling and low cohesion across key transactional hotspots. God classes with high complexity (WMC) and low cohesion (LCOM) form tightly bound clusters, amplifying regression risk and blast radius for even minor code modifications.\n\n"
                "Given the zero-test-coverage footprint (0.0%), manual quality assurance is the only safeguard, acting as a modernization blocker. Decoupling the codebase, introducing autoloading mappings, and writing automated characterization tests are necessary prerequisites to ensure secure and sustainable evolutionary progress."
            ),
            "critical_risks": "High architectural coupling and low test coverage make modifications dangerous.",
            "boundary_layer_insights": "Fallback boundary insights not available.",
            "architecture_insights": "Fallback architecture insights not available.",
            "database_coupling_insights": "Fallback database insights not available.",
            "global_state_insights": "Fallback global state insights not available.",
            "security_posture": "Fallback security posture not available.",
            "testing_strategy": "Fallback testing strategy not available.",
            "quick_wins": [
                {"title": "Automate Code Linting", "impact": "Low effort, high readability improvement."}
            ],
            "strategic_roadmap": [
                {"step_number": 1, "title": "Introduce Static Analysis", "description": "Set up phpstan or psalm to baseline the project.", "rationale": "Ensures no new legacy syntax errors or deprecations are introduced."},
                {"step_number": 2, "title": "Add Characterization Tests", "description": "Create integration testing suites around critical endpoints.", "rationale": "Guarantees logic preservation during active refactoring."},
                {"step_number": 3, "title": "Database Decoupling", "description": "Isolate DB transactions behind modern service interfaces.", "rationale": "Enables migration to new database platforms without breaking core controllers."}
            ]
        }
