# Strata vs PhpMetrics: Critical Evaluation & Comparison Strategy

## 1. Evaluation of Current Validation Results (OWASPWebGoatPHP)

Based on the recent run (`run_comparison.py` against Strata Run 3 and PhpMetrics baseline 1), we observed several critical divergences. Rather than simply indicating that Strata is "wrong," these divergences highlight fundamental differences in architectural philosophy, alongside a few actual ingestion bugs that need fixing.

### A. The "Total Methods = 0" Aggregation Bug
*   **Observation:** Strata reports `0` Total Methods, while PhpMetrics reports `4818`.
*   **Critical Evaluation:** This is an aggregation bug in Strata's Application Layer (`analysis_service.py`). Even though the PHP AST parser correctly identifies methods and calculates their complexity, the Python service is failing to properly aggregate them from the JSON `metadata` payload of `CLASS` nodes. This severely skews downstream averages and must be fixed.

### B. Logical Lines of Code (LLOC) & Class Sizing
*   **Observation:** Strata counts ~119k LLOC vs PhpMetrics ~93k. Strata also identifies 847 classes vs PhpMetrics' 754.
*   **Critical Evaluation:** Strata is parsing *more* of the codebase. PhpMetrics often ignores test directories, vendor files, or specific legacy structures by default. Strata's `token_get_all` approach is strictly counting all executable tokens. **Strata is arguably more accurate here** for a complete modernization audit, as legacy debt often hides in un-autoloaded or procedural scripts that PhpMetrics skips.

### C. The 40 "Missing" Classes
*   **Observation:** PhpMetrics found 40 classes (e.g., `Autoload`, `ErrorHandler`) that Strata completely missed.
*   **Critical Evaluation:** These are likely files containing highly irregular legacy syntax (e.g., mixed HTML/PHP, missing `<?php` tags, or nested closures) that caused the `php-parser` in Strata to silently fail or skip the file during ingestion. We need to improve Strata's error logging during AST parsing to capture these dropped files.

### D. Cyclomatic Complexity (CC) Averages
*   **Observation:** Strata Avg CC is `6.94`, PhpMetrics is `13.01`.
*   **Critical Evaluation:** PhpMetrics calculates the average by summing the WMC (Weighted Method Complexity) of all classes and dividing by the number of classes. Strata is currently aggregating complexity at the *file* level and averaging across all files (including simple config files and views). This dilutes Strata's average. 

### E. LCOM (Cohesion) and Coupling (Ca/Ce)
*   **Observation:** Massive divergence in LCOM (565 classes) and Coupling (530 classes).
*   **Critical Evaluation:** **Strata is correct in its context.** PhpMetrics uses static imports (`use` statements) to calculate Afferent/Efferent coupling. In legacy PHP (pre-namespaces), `use` statements don't exist. Strata calculates *Runtime Blast Radius* by tracing actual method calls, instantiations, and SQL injections, providing a much more accurate picture of runtime coupling. Similarly, Strata uses the strict Henderson-Sellers LCOM formula (yielding 0.0 - 1.0+), while PhpMetrics likely uses LCOM4 (measuring disconnected graph components).

---

## 2. Proposed Changes to `run_comparison.py`

To make the comparison script a valuable strategic tool rather than just a naive diff tool, we need to completely overhaul its logic. It should not penalize Strata for being different; it should highlight *why* Strata's metrics are superior for legacy modernization, while strictly enforcing parity on objective counts.

### Proposed Script Logic Upgrades:

#### 1. Shift from "Fail/Pass" to "Divergence Context"
Instead of marking a 20% delta in LCOM as a `[FAIL]`, the script should recognize semantic differences.
*   *Current Output:* `❌ [FAIL] Avg Cyclomatic Complexity ... Δ=46.7%`
*   *Proposed Output:* `ℹ️ [ARCH] CC Divergence: Strata averages by File (6.94), PhpMetrics by Class (13.01).`

#### 2. Strict Parity on Objective Metrics Only
The script should only trigger a `[FAIL]` on strictly objective, mathematically absolute metrics:
*   Total Classes (If Strata misses classes PhpMetrics found, it's a parsing failure).
*   Total Methods (Strata's `0` count is an objective failure).

#### 3. Deep-Dive on Missing Entities
The script should isolate the exact file paths of the 40 classes Strata missed, rather than just their names. 
*   *Proposed Logic:* Cross-reference PhpMetrics' class list with Strata's scanned files to output: `Class 'ErrorHandler' missing in Strata. File path: /core/ErrorHandler.php. Recommendation: Check for parsing errors in this file.`

#### 4. Semantic Rename in Output
The script should stop comparing Strata's "Out-Degree" to PhpMetrics' "Efferent Coupling" as if they are the same metric.
*   *Proposed Logic:* `[SUPERIORITY] Runtime Blast Radius vs Efferent Coupling: Strata detected 15 dynamic instantiations that PhpMetrics missed due to lack of static imports.`

#### 5. Halstead & PageRank Baseline
Since PhpMetrics tracks Halstead metrics, the script should explicitly validate Strata's new Phase 3 Halstead calculations against PhpMetrics to ensure mathematical parity in bug prediction scoring.
