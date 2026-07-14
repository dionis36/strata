<?php

require __DIR__ . '/vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\PhpVersion;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitor\NameResolver;
use Strata\Parser\MetadataExtractor;

use PhpParser\ErrorHandler\Collecting;

// ── Parser Initialisation ────────────────────────────────────────────────────
// MULTI-PASS ARCHITECTURE: We instantiate two parsers. 
// 1. Modern (PHP 8.2): For strict validation of modern syntax.
// 2. Legacy (PHP 5.6): For fallback parsing of procedural PHP 4/5 files (e.g. 'var $x').
$modernParser = (new ParserFactory())->createForVersion(PhpVersion::fromString('8.2'));
$legacyParser = (new ParserFactory())->createForVersion(PhpVersion::fromString('5.6'));

while ($path = fgets(STDIN)) {
    $path = trim($path);
    if (empty($path)) continue;

    if (!file_exists($path)) {
        echo json_encode(['status' => 'error', 'path' => $path, 'message' => 'File not found']) . "\n";
        continue;
    }

    try {
        $code = file_get_contents($path);

        // ── Normalise PHP short-open-tags (<?) ─────────────────────────────────
        // PHP-Parser v5 does not support <? because PHP 7+ dropped short_open_tag.
        // Legacy PHP 5 codebases use it everywhere. Rewriting to <?php is safe.
        // Negative lookahead leaves <?php, <?=, and <?xml untouched.
        $code = preg_replace('/<\?(?!php\b|xml\b|=)/', '<?php', $code);

        // ── Normalise deprecated curly-brace string-index syntax ($s{n}) ───────
        // $str{0} was deprecated in PHP 7.4 and removed in PHP 8.0.
        // The Emulative lexer (PHP 7.4 target) still chokes on it inside the AST.
        // We rewrite to the equivalent bracket syntax before parsing.
        $code = preg_replace('/(\$[a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*)\{(\d+)\}/', '$1[$2]', $code);

        $loc = substr_count($code, "\n") + 1;
        
        // ── Calculate Logical Lines of Code (LLOC) ─────────────────────────────
        $lloc = 0;
        $tokens = token_get_all($code);
        $logicalLines = [];
        $currentLine = 1;
        foreach ($tokens as $token) {
            if (is_array($token)) {
                $id = $token[0];
                $text = $token[1];
                if ($id !== T_COMMENT && $id !== T_DOC_COMMENT && $id !== T_WHITESPACE) {
                    $logicalLines[$currentLine] = true;
                }
                $currentLine += substr_count($text, "\n");
            } else {
                $logicalLines[$currentLine] = true;
                $currentLine += substr_count($token, "\n");
            }
        }
        $lloc = count($logicalLines);
        // ── AST Extraction (Multi-Pass & Error Recovery) ──────────────────────
        $errorHandler = new Collecting();
        
        try {
            $stmts = $modernParser->parse($code, $errorHandler);
            if ($stmts === null) {
                throw new PhpParser\Error("Modern parser returned null");
            }
        } catch (PhpParser\Error $e) {
            // PASS 2: Legacy Fallback
            $errorHandler = new Collecting();
            try {
                $stmts = $legacyParser->parse($code, $errorHandler);
            } catch (PhpParser\Error $e2) {
                $stmts = null;
            }
        }

        if ($stmts === null) {
            echo json_encode([
                'status'  => 'error',
                'path'    => $path,
                'message' => 'Parser returned null after multi-pass fallback (unrecoverable error)',
            ]) . "\n";
            continue;
        }

        $extractor = new MetadataExtractor();
        $traverser = new NodeTraverser();
        // NameResolver with lenient mode: do not throw on forward-declared or
        // globally-scoped class names that are unresolvable (common in PHP 5 code).
        $traverser->addVisitor(new NameResolver(null, ['throwOnUnresolvableNames' => false]));
        $traverser->addVisitor($extractor);
        $traverser->traverse($stmts);

        $metadata = $extractor->metadata;
        $metadata['loc'] = $loc;
        $metadata['lloc'] = $lloc;

        echo json_encode([
            'status'   => 'success',
            'path'     => $path,
            'metadata' => $metadata,
        ]) . "\n";

    } catch (PhpParser\Error $error) {
        echo json_encode([
            'status'  => 'error',
            'path'    => $path,
            'message' => "Parse error: {$error->getMessage()}",
        ]) . "\n";
    }
}
