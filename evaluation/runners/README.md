# Strata × PhpMetrics Validation Suite

This directory contains the automated evaluation runners used to benchmark the **Strata Modernization Intelligence Platform** against **PhpMetrics**, the industry-standard static analysis tool for PHP.

This suite is decoupled into a two-step process: **Generation** (creating the ground truth) and **Comparison** (validating Strata's output).

---

## 1. Prerequisites & Setup

Before running the evaluation suite, you must have Docker installed. The runner scripts utilize Docker to ensure a clean, isolated, and reproducible PhpMetrics environment across all operating systems (Linux, Windows, macOS).

Run the following command to pull the official PhpMetrics image:
```bash
docker pull phpmetrics/phpmetrics
```

---

## 2. The Workflow

The validation process is split into two independent steps to allow for highly collaborative testing. You only need to generate the baseline *once*, and you can then validate Strata against it *infinitely*.

### Step 1: Generate the PhpMetrics Baseline
Run this script to analyze a legacy project from the `/data` directory using PhpMetrics.

```bash
./evaluation/runners/generate_phpmetrics.py
```

**What happens:**
1. The script will list all available projects in the `/data` directory.
2. Select the project you want to baseline (e.g., `OWASPWebGoatPHP-master`).
3. The script automatically executes the Docker container, applying OS-specific volume mounts safely.
4. The output (a 2MB+ `report.json` and a visual HTML dashboard) is saved to the `/AUDIT/` directory at the root of the project. 

> **Note:** The `/AUDIT/` directory is intentionally ignored by `.gitignore`. This ensures our repository stays clean and is not bloated by massive, temporary JSON files.

### Step 2: Run the Strata Validation
Once the PhpMetrics baseline exists, run a standard Strata analysis on the same project using the UI or API. Take note of the **Run ID**.

Then, run the comparison script:

```bash
./evaluation/runners/run_comparison.py
```

**What happens:**
1. You select the PhpMetrics baseline from `/AUDIT/`.
2. You enter the **Strata Run ID**.
3. The script dynamically extracts the Strata intelligence directly from the SQLite `app.db`.
4. It performs a strict one-to-one class matching.
5. It outputs a detailed PASS/WARN/FAIL matrix, calculating the divergence on WMC, LCOM, and Coupling.

---

## 3. Understanding the Validation Output (Expected Shortcomings)

Strata is an architectural *modernization* tool, whereas PhpMetrics is an academic *code quality* tool. Because of this, you will see deliberate divergences in the validation output. 

When evaluating the output, keep the following in mind:

### ✅ Coupling (In/Out Degree vs Ca/Ce) -> STRATA IS HIGHER
PhpMetrics only counts formal static dependencies (e.g., `use` statements, `implements`, type-hints). 
Strata parses the AST for runtime behaviors: `new Object()`, `$obj->method()`, and constructor injections. **Strata's coupling metrics represent the true runtime blast radius**, making it mathematically much higher but significantly more accurate for legacy PHP monoliths.

### ⚠️ LCOM (Cohesion) -> DIFFERENT MATHEMATICAL SCALES
PhpMetrics uses an older, absolute-integer LCOM formula (outputs like `3.0`, `5.0`). 
Strata uses the **Henderson-Sellers LCOM4 formula**, which bounds the cohesion score strictly between `[0, 1]`. Strata's scale is superior for machine learning and risk scoring pipelines.

### ❌ WMC & LOC (Complexity) -> PHPMETRICS IS MORE ACCURATE
Strata approximates complexity by counting logical AST nodes (`If`, `For`, `While`) and calculates LOC by counting raw lines (`\n`). PhpMetrics strictly adheres to McCabe's Cyclomatic Complexity and Logical LOC (LLOC). If you see a major divergence here, trust the PhpMetrics number. (This is a known improvement target for Strata).

###  Unparsed Classes
If the report shows that Strata missed classes that PhpMetrics found, it is likely due to the legacy file containing PHP 5.x short-open-tags (`<?`) or raw syntax errors that caused Strata's `parser.php` sidecar to fail silently. 
