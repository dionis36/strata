
# Immediate Execution Plan: Phase 1 — AST Parser Bridge

This document details the immediate technical actions to initialize the **High-Fidelity AST Extraction** phase.

## Step 1: Environment & Infrastructure (Infrastructure Layer)
**Goal**: Enable PHP 8.2 execution within the Strata container.

1. **Update `Dockerfile`**:
    - Add `php-cli`, `php-xml`, `php-mbstring`, and `unzip` to the `apt-get install` list.
    - Copy Composer from the official image: `COPY --from=composer:latest /usr/bin/composer /usr/bin/composer`.
2. **Initialize PHP Workspace**:
    - Create directory: `infrastructure/php/`.
    - Initialize Composer: `composer init --no-interaction --name="strata/parser-bridge"`.
    - Install Parser: `composer require nikic/php-parser:^5.0`.

## Step 2: The PHP Sidecar (`infrastructure/php/parser.php`)
**Goal**: Create a high-performance metadata extractor.

1. **JSON Protocol**:
    - Implement a `while(fgets(STDIN))` loop to listen for file paths.
    - Output `{"status": "success", "data": {...}}` for every parsed file.
2. **Visitor Implementation**:
    - Use `PhpParser\NodeTraverser` and a custom `NodeVisitor`.
    - Extract:
        - `Stmt\Class_`: Name, Extends, Implements.
        - `Stmt\Trait_`: Name.
        - `Stmt\Interface_`: Name.
        - `Expr\New_`: Class instantiation.
        - `Expr\StaticCall` & `Expr\MethodCall`: Method calls.
3. **Safety**:
    - Catch `PhpParser\Error` to handle syntax issues gracefully.

## Step 3: The Python Bridge Refactor (`infrastructure/parser_bridge.py`)
**Goal**: Seamlessly swap regex for AST.

1. **Process Management**:
    - Use `subprocess.Popen` with `bufsize=1` (line buffered).
    - Implement a `_send_command(path)` and `_read_response()` pattern.
2. **Model Mapping**:
    - Convert PHP's JSON output into `domain.models.node.Node` and `domain.models.edge.Edge` objects.
    - Ensure all `Node.id` fields use the new FQN-based hashing strategy.

## Step 4: Validation Fixtures (`tests/fixtures/`)
**Goal**: Verify accuracy against known ground truth.

1. **`kitchen_sink.php`**: A file containing every complex PHP feature we need to support.
2. **`test_ast_accuracy.py`**: A new test file that compares `ParserBridge` output against a manually verified JSON snapshot.

---

**Next Action**: Update the `Dockerfile` to include PHP and Composer.
