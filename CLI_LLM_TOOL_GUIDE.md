# Strata CLI: AI Executive Summary Override Tool

Because large language models (LLMs) are often rate-limited, overloaded, or non-deterministic (especially free-tier models), the Strata application occasionally fails to generate the **AI Executive Summary** during the automated analysis pipeline.

If a run fails at the intelligence phase, you can use the built-in CLI override tool to manually extract the database metrics, communicate with the LLM API, handle broken JSON, and forcibly inject the completed insights back into your SQLite database.

## 🚀 The Script Location
The tool is located at `tests/test_llm_prompt_for_run.py` and must be executed *inside* the API Docker container.

---

## 🛠️ Command Structure

The base command looks like this:
```bash
docker exec strata-api-1 python tests/test_llm_prompt_for_run.py [OPTIONS]
```

## 🏷️ Available Flags

### 1. `--run-id <ID>` (Required)
Specifies which Analysis Run you want to generate intelligence for.
*   **Example:** `--run-id 2`

### 2. `--print-prompt`
A dry-run tool. This will extract all data from your database (Architecture, Database Metrics, Global State, Boundary Couplings, etc.), assemble the massive prompt string exactly as it would be sent to the LLM, and print it to your terminal.
*   *It does NOT contact the API and costs zero tokens.*
*   **Example:** `docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id 2 --print-prompt`

### 3. `--invoke`
Actually sends the assembled payload to the active LLM defined in your `.env` file (`OPENROUTER_MODEL`). It features an automatic "Ping Test" before sending the heavy payload to verify that your API keys are valid and the model is not currently overloaded.
*   *It will print the raw JSON response to your terminal, but it will NOT save it to the database.*
*   **Example:** `docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id 2 --invoke`

### 4. `--save`
Pairs with `--invoke`. If the LLM successfully returns valid JSON (or if `json-repair` successfully fixes it), this flag will physically inject the JSON block into your `data/app.db` database under `ai_executive_summary_json`. It also flips the run status to `intelligence_ready`.
*   *Once this succeeds, refreshing your browser will instantly unlock the Master Report download buttons.*
*   **Example:** `docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id 2 --invoke --save`

### 5. `--force`
A safety bypass. By default, if the script sees that a Run ID already has the `intelligence_ready` status in the database, it will immediately abort to prevent you from accidentally burning API quota on a run that is already finished. If you *want* to overwrite the existing summary (e.g., you switched to a smarter model), append `--force`.
*   **Example:** `docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id 2 --invoke --save --force`

---

## 💡 Quick Start Workflows

**Scenario A: The UI says "AI Synthesis Failed" (Red Box)**
Just run this command. It will retry the LLM, fix any broken JSON, and save it.
```bash
docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id <YOUR_RUN_ID> --invoke --save
```

**Scenario B: You changed your OPENROUTER_MODEL in `.env` and want to test it.**
Don't forget to restart your Docker containers first so the container sees the new `.env` file!
```bash
docker compose up -d --build
docker exec strata-api-1 python tests/test_llm_prompt_for_run.py --run-id <YOUR_RUN_ID> --invoke --save --force
```

## 🛡️ Built-In Protections
- **Pre-flight Ping:** Sends a 1-token prompt ("Ping") to check for `429` (Rate Limits) or `503` (Overloaded) errors before wasting your bandwidth.
- **Auto-JSON Repair:** Free models frequently miss commas or use unescaped double quotes. The script passes the raw LLM output through `json-repair` to structurally fix the syntax before inserting it into the database.
- **Gemini Fallback:** If OpenRouter completely fails, it intelligently falls back to the native `GEMINI_API_KEY` (if provided) as a safety net.
